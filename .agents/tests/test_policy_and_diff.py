import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from helpers import Fixture, SOURCE
from policy import PolicyError, generated, generated_signature, protected, validate_change
from pre_tool_enforcer import check_tool
from verify_changes import tree_identity, verify_policy, verify_tests


class PolicyTests(Fixture):
    def test_generated_text_and_marker_identity(self):
        validate_change(self.main, SOURCE, SOURCE.replace('user_call();','safe();'))
        for after in [SOURCE.replace('int generated = 0;', 'int generated = 1;'),
                      SOURCE.replace('END 0','END 9'), SOURCE.replace('BEGIN 0','BEGIN 9')]:
            with self.subTest(after=after):
                with self.assertRaises(PolicyError):
                    validate_change(self.main, SOURCE, after)

    def test_malformed_markers_fail_closed(self):
        for value in ['/* USER CODE BEGIN 0 */\n', '/* USER CODE END 0 */\n',
                      '/* USER CODE BEGIN 0 */\n/* USER CODE BEGIN 1 */\n']:
            with self.subTest(value=value):
                with self.assertRaises(PolicyError):
                    generated_signature(value)

    def test_non_c_examples_are_not_generated_code(self):
        self.assertFalse(generated(self.root / 'guide.md', SOURCE))
        self.assertFalse(generated(self.root / 'script.py', SOURCE))

    def test_handwritten_core_source_without_markers_is_editable(self):
        path = self.root/'Core/Src/helper.c'
        self.assertFalse(generated(path, 'void helper(void) {}'))
        validate_change(path, 'void helper(void) {}', 'void helper(void) { return; }')

    def test_compiled_artifact_write_is_rejected(self):
        with self.assertRaises(PolicyError):
            validate_change(self.root/'firmware.elf', '', 'not a source file')

    def test_protected_paths_are_case_insensitive(self):
        for name in ['BOARD.LD', 'Core/Startup/STARTUP_stm32.S', 'Drivers/CMSIS/core_cm4.h',
                     'Drivers/STM32G4xx_HAL_Driver/Src/stm32g4xx_hal.c']:
            with self.subTest(name=name):
                self.assertTrue(protected(self.root / name))

    def test_exact_reviewed_system_override(self):
        path = self.root / 'board.ld'
        with self.assertRaises(PolicyError):
            validate_change(path, 'old', 'new')
        validate_change(path, 'old', 'new', allow_protected={str(path.resolve())})
        with self.assertRaises(PolicyError):
            validate_change(self.root / 'other.ld', 'old', 'new', allow_protected={str(path.resolve())})

    def test_native_override_comes_from_definition_not_tool_payload(self):
        path = self.root/'board.ld'
        path.write_text('MEMORY {}')
        args = {'file_path':str(path),'old_string':'MEMORY {}','new_string':'MEMORY { FLASH: ORIGIN=0 }',
                'allow_protected':[str(path)]}
        with self.assertRaises(PolicyError):
            check_tool('Edit',args,self.root)
        check_tool('Edit',args,self.root,{str(path.resolve())})


class GitDiffTests(Fixture):
    def setUp(self):
        super().setUp()
        self.init_git()

    def test_independent_gate_catches_script_mutation(self):
        self.main.write_text(SOURCE.replace('int generated = 0;', 'int generated = 1;'))
        with self.assertRaises(PolicyError):
            verify_policy(self.root)

    def test_staged_safe_edit_is_accepted(self):
        self.main.write_text(SOURCE.replace('user_call();', 'safe();'))
        self.run_git('add', 'Core/Src/main.c')
        self.assertEqual(len(verify_policy(self.root)), 1)

    def test_untracked_source_is_checked(self):
        path = self.app.parent / 'new.c'
        path.write_text('void *p = malloc(8);\n')
        with self.assertRaises(PolicyError):
                verify_policy(self.root)

    def test_unignored_build_artifact_is_rejected(self):
        (self.root/'firmware.elf').write_bytes(b'\x7fELF\xff')
        with self.assertRaises(PolicyError):
            verify_policy(self.root)

    def test_newline_conversion_does_not_corrupt_comparison(self):
        self.main.write_bytes(SOURCE.replace('\n','\r\n').encode())
        self.run_git('add', 'Core/Src/main.c')
        self.run_git('commit', '-qm', 'CRLF baseline')
        self.main.write_bytes(SOURCE.replace('user_call();','safe();').replace('\n','\r\n').encode())
        self.assertEqual(len(verify_policy(self.root)), 1)

    def test_deleting_generated_file_is_rejected(self):
        self.main.unlink()
        with self.assertRaises(PolicyError):
            verify_policy(self.root)

    def test_ci_base_catches_committed_changes(self):
        base = self.run_git('rev-parse','HEAD').stdout.decode().strip()
        self.main.write_text(SOURCE.replace('int generated = 0;', 'int generated = 1;'))
        self.run_git('add','Core/Src/main.c')
        self.run_git('commit','-qm','Unsafe committed fixture')
        with self.assertRaises(PolicyError):
            verify_policy(self.root, base)


class VerificationCacheTests(Fixture):
    def test_non_c_fixtures_invalidate_but_runtime_state_does_not(self):
        self.init_git()
        before = tree_identity(self.root)
        (self.root/'fixture.json').write_text('{"input": 1}')
        after = tree_identity(self.root)
        self.assertNotEqual(before, after)
        state = self.root/'.agents/state'
        state.mkdir(parents=True)
        (state/'context.json').write_text('local notes')
        self.assertEqual(after, tree_identity(self.root))

    def test_nested_git_dependency_changes_invalidate(self):
        self.init_git()
        nested = self.root/'common'
        nested.mkdir()
        (nested/'helper.c').write_text('void helper(void) {}')
        for args in [('init','-q'),('config','user.email','fixture@example.invalid'),
                     ('config','user.name','Fixture'),('add','.'),('commit','-qm','Dependency baseline')]:
            self.run_git('-C',str(nested),*args)
        before = tree_identity(self.root)
        (nested/'helper.c').write_text('void helper(void) { return; }')
        self.assertNotEqual(before, tree_identity(self.root))

    def test_missing_project_is_not_a_pass(self):
        with patch('verify_changes.tree_identity', return_value='tree'):
            with self.assertRaises(PolicyError):
                verify_tests(self.root)

    def test_pass_reused_only_for_identical_tree(self):
        (self.root/'project.yml').write_text('fixture: true')
        with patch('verify_changes.tree_identity', return_value='tree-1'), patch('verify_changes.shutil.which', return_value='ceedling'), patch('verify_changes.subprocess.run', return_value=SimpleNamespace(returncode=0)) as runner:
            self.assertIn('passed', verify_tests(self.root))
            self.assertIn('reused', verify_tests(self.root))
            self.assertEqual(runner.call_count, 1)
        with patch('verify_changes.tree_identity', return_value='tree-2'), patch('verify_changes.shutil.which', return_value='ceedling'), patch('verify_changes.subprocess.run', return_value=SimpleNamespace(returncode=0)) as runner:
            self.assertIn('passed', verify_tests(self.root))
            self.assertEqual(runner.call_count, 1)

    def test_failed_result_is_never_cached(self):
        (self.root/'project.yml').write_text('fixture: true')
        with patch('verify_changes.tree_identity', return_value='tree'), patch('verify_changes.shutil.which', return_value='ceedling'), patch('verify_changes.subprocess.run', return_value=SimpleNamespace(returncode=1)):
            with self.assertRaises(PolicyError):
                verify_tests(self.root)
        self.assertFalse((self.root/'.agents/state/verification.json').exists())
        self.assertFalse((self.root/'.agents/state/verification.lock').exists())

    def test_concurrent_verification_does_not_run_a_second_build(self):
        (self.root/'project.yml').write_text('fixture: true')
        state = self.root/'.agents/state'
        state.mkdir(parents=True)
        (state/'verification.lock').write_text('another verifier')
        with patch('verify_changes.tree_identity', return_value='tree'), patch('verify_changes.shutil.which', return_value='ceedling'), patch('verify_changes.subprocess.run') as runner:
            with self.assertRaises(PolicyError):
                verify_tests(self.root)
            runner.assert_not_called()


if __name__ == '__main__':
    unittest.main()
