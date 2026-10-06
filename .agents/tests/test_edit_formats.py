import unittest
from helpers import Fixture


class MultiEdits(Fixture):
    def chunks(self, chunks):
        return {'TargetFile':str(self.main), 'ReplacementChunks':chunks}

    def test_safe_and_unsafe_antigravity_chunks(self):
        inside = {'StartLine':3,'EndLine':3,'TargetContent':'user_call();','ReplacementContent':'safe();'}
        outside = {'StartLine':1,'EndLine':1,'TargetContent':'int generated = 0;','ReplacementContent':'int generated = 1;'}
        self.assert_gate('multi_replace_file_content', self.chunks([inside]), False, 'antigravity')
        self.assert_gate('multi_replace_file_content', self.chunks([inside, outside]), True, 'antigravity')

    def test_overlapping_chunks_and_wrong_ranges(self):
        chunk = {'StartLine':3,'EndLine':3,'TargetContent':'user_call();','ReplacementContent':'safe();'}
        self.assert_gate('multi_replace_file_content', self.chunks([chunk, chunk]), True, 'antigravity')
        chunk['StartLine'], chunk['EndLine'] = 1, 1
        self.assert_gate('multi_replace_file_content', self.chunks([chunk]), True, 'antigravity')


class PatchEdits(Fixture):
    def patch(self, path, body):
        return {'command':f'*** Begin Patch\n*** Update File: {path}\n{body}\n*** End Patch'}

    def test_safe_and_unsafe_canonical_codex_patch(self):
        self.assert_gate('apply_patch', self.patch('Core/Src/main.c','@@\n-user_call();\n+safe();'), False, 'codex')
        self.assert_gate('apply_patch', self.patch('Core/Src/main.c','@@\n-int generated = 0;\n+int generated = 1;'), True, 'codex')

    def test_multi_file_patch_checks_all_files(self):
        patch = ('*** Begin Patch\n*** Update File: Core/Src/App/logic.c\n@@\n'
                 '-void application(void) {}\n+void application(void) { return; }\n'
                 '*** Update File: Core/Src/main.c\n@@\n-int generated = 0;\n+int generated = 1;\n*** End Patch')
        self.assert_gate('apply_patch', {'command':patch}, True, 'codex')
        self.assertIn('void application(void) {}', self.app.read_text())

    def test_ambiguous_and_unsupported_patches_fail_closed(self):
        self.assert_gate('apply_patch', self.patch('Core/Src/main.c','@@\n-shared();\n+safe();'), True, 'codex')
        self.assert_gate('apply_patch', {'command':'garbage'}, True, 'codex')
        move = '*** Begin Patch\n*** Update File: Core/Src/main.c\n*** Move to: renamed.c\n@@\n-user_call();\n+safe();\n*** End Patch'
        self.assert_gate('apply_patch', {'command':move}, True, 'codex')

    def test_anchor_and_context_disambiguate(self):
        body = '@@\n /* USER CODE BEGIN 1 */\n-shared();\n+safe();\n /* USER CODE END 1 */'
        self.assert_gate('apply_patch', self.patch('Core/Src/main.c',body), False, 'codex')

    def test_add_delete_and_allocations(self):
        add = '*** Begin Patch\n*** Add File: Core/Src/App/new.c\n+void task(void) {}\n*** End Patch'
        self.assert_gate('apply_patch', {'command':add}, False, 'codex')
        self.assert_gate('apply_patch', {'command':add.replace('void task(void) {}','void *p = malloc(8);')}, True, 'codex')
        delete = '*** Begin Patch\n*** Delete File: Core/Src/main.c\n*** End Patch'
        self.assert_gate('apply_patch', {'command':delete}, True, 'codex')


class ShellHooks(Fixture):
    def test_common_mutators_are_denied(self):
        commands = ["printf 'unsafe' > Core/Src/main.c", 'Set-Content Core/Src/main.c unsafe',
                    'sed -i s/a/b/ Core/Src/main.c', 'tee Core/Src/main.c',
                    'python -c "open(\'Core/Src/main.c\',\'w\').write(\'unsafe\')"',
                    'pwsh -EncodedCommand abc', 'git restore Core/Src/main.c']
        for command in commands:
            with self.subTest(command=command):
                self.assert_gate('Bash', {'command':command}, True)
                self.assert_gate('run_command', {'CommandLine':command}, True, 'antigravity')

    def test_build_tests_and_git_queries_remain_allowed(self):
        for command in ['ceedling test:all', 'bundle exec ceedling test:all', 'cmake --build build',
                        'git status -s', 'git diff --stat', 'rg --files Core/Src',
                        'python .agents/hooks/doctor.py --self-test']:
            with self.subTest(command=command):
                self.assert_gate('Bash', {'command':command}, False)

    def test_bulk_shell_reads_need_bounded_output(self):
        self.assert_gate('Bash', {'command':'cat large.c'}, True)
        self.assert_gate('Bash', {'command':'Get-Content -Raw large.c'}, True)
        self.assert_gate('Bash', {'command':'cat large.c | head -n 100'}, False)
        self.assert_gate('Bash', {'command':'Get-Content large.c -TotalCount 100'}, False)
        self.assert_gate('Bash', {'command':'cat small.c'}, False)

    def test_terminal_transport_is_not_a_file_write(self):
        self.assert_gate('write_stdin', {'session_id':1, 'chars':''}, False, 'codex')


if __name__ == '__main__':
    unittest.main()
