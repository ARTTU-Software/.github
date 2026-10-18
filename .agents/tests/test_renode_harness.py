"""Exercise repository-local Renode execution without an emulator in contract CI."""
import contextlib
import importlib.util
import io
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from helpers import ROOT
SOURCE = ROOT / 'test/renode'
DEPENDENCIES = all(importlib.util.find_spec(name) for name in ('robot', 'yaml'))


@unittest.skipUnless(DEPENDENCIES, 'Renode contracts require the harness Python packages')
class RenodeHarnessTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='renode starter with spaces ')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.fixture = self.root / 'test/renode'
        shutil.copytree(SOURCE, self.fixture, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        spec = importlib.util.spec_from_file_location('renode_adapter', self.fixture / 'harness/run_tests.py')
        self.adapter = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.adapter)

    def test_repository_harness_discovers_and_selects_smoke_without_renode(self):
        normalized, paths = self.adapter.load_manifest(self.fixture / 'harness/tests.yaml')
        self.assertEqual(normalized, [str(paths[0])])
        self.assertEqual(self.adapter.selected_cases(paths, [], []), ['case:monitor-help'])
        self.assertEqual(self.adapter.selected_cases(paths, ['smoke'], []), ['case:monitor-help'])
        for includes, excludes in [(['firmware'], []), ([], ['infrastructure'])]:
            with self.assertRaisesRegex(ValueError, 'No test cases'):
                self.adapter.selected_cases(paths, includes, excludes)

    def test_serial_groups_keep_absolute_paths_including_spaces(self):
        path = self.fixture / 'harness/tests.yaml'
        path.write_text('- resource_group:\n    - suites/monitor.robot\n')
        normalized, paths = self.adapter.load_manifest(path)
        self.assertEqual(normalized, [{'resource_group': [str(paths[0])]}])
        self.assertTrue(paths[0].is_absolute())
        for text in ['[]', '- missing.robot', '- suites/monitor.robot\n- suites/monitor.robot',
                     '- empty: []', '- 123']:
            path.write_text(text)
            with self.assertRaises(ValueError):
                self.adapter.load_manifest(path)

    def make_result(self, body):
        import robot
        suite = self.root / 'outcome.robot'
        suite.write_text('*** Test Cases ***\n' + body)
        output = self.root / 'results'
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            robot.run(str(suite), outputdir=str(output), output='robot_output.xml', log='NONE', report='NONE')
        return output

    def test_real_robot_failure_is_retained_and_next_case_runs(self):
        output = self.make_result('Fails\n    [Tags]    case:first\n    Fail    deliberate failure\n'
                                  'Next\n    [Tags]    case:next\n    No Operation\n')
        with contextlib.redirect_stdout(io.StringIO()):
            result = self.adapter.validate_result(output, ['case:first', 'case:next'])
        self.assertEqual((result['failed'], result['passed'], result['skipped']), (1, 1, 0))
        self.assertNotIn('infrastructure_error', result)
        self.assertTrue((output / 'xunit.xml').is_file())

    def test_result_count_and_listener_errors_are_not_success(self):
        import xml.etree.ElementTree as ET
        output = self.make_result('Passes\n    [Tags]    case:actual\n    No Operation\n')
        with contextlib.redirect_stdout(io.StringIO()):
            result = self.adapter.validate_result(output, ['case:missing'])
        self.assertIn('infrastructure_error', result)
        path = output / 'robot_output.xml'
        tree = ET.parse(path)
        message = ET.SubElement(tree.getroot().find('errors'), 'msg', level='ERROR')
        message.text = 'synthetic listener failure'
        tree.write(path, encoding='utf-8')
        with contextlib.redirect_stdout(io.StringIO()):
            result = self.adapter.validate_result(output, ['case:actual'])
        self.assertIn('synthetic listener failure', result['infrastructure_error'])
        self.assertIn('infrastructure_error', self.adapter.validate_result(self.root, ['case:actual']))

    def test_skipped_result_is_visible(self):
        output = self.make_result('Skipped\n    [Tags]    case:skip\n    Skip    missing hardware\n')
        with contextlib.redirect_stdout(io.StringIO()):
            result = self.adapter.validate_result(output, ['case:skip'])
        self.assertEqual(result['skipped'], 1)

    def test_malformed_reports_and_manifest_fail_cleanly(self):
        (self.root / 'robot_output.xml').write_text('<robot>truncated')
        self.assertIn('infrastructure_error', self.adapter.validate_result(self.root, ['case:any']))
        manifest = self.fixture / 'harness/tests.yaml'
        manifest.write_text('- [broken')
        with self.assertRaisesRegex(ValueError, 'Invalid test manifest'):
            self.adapter.load_manifest(manifest)

    def test_duplicate_case_identity_is_rejected(self):
        suite = self.fixture / 'duplicate.robot'
        suite.write_text('*** Test Cases ***\nA\n    [Tags]    case:duplicate\n    No Operation\n'
                         'B\n    [Tags]    case:duplicate\n    No Operation\n')
        with self.assertRaisesRegex(ValueError, 'unique case:'):
            self.adapter.selected_cases([suite], [], [])

    def test_cli_rejects_empty_selection_and_stale_output_without_starting_renode(self):
        command = [sys.executable, str(self.fixture / 'harness/run_tests.py')]
        result = subprocess.run(command + ['--list'], cwd=self.root, capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('case:monitor-help', result.stdout)
        result = subprocess.run(command + ['--include', 'absent'], cwd=self.root,
                                capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 2)
        self.assertIn('No test cases', result.stderr)
        installation = self.root / 'fake install'
        installation.mkdir()
        executable = installation / 'renode'
        executable.touch()
        (installation / 'tests').mkdir()
        (installation / 'tests/run_tests.py').touch()
        output = self.root / 'stale'
        output.mkdir()
        (output / 'old-result').touch()
        result = subprocess.run(command + ['--renode', str(executable), '--results-dir', str(output)],
                                cwd=self.root, capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 2)
        self.assertIn('fresh results', result.stderr)

    def test_local_board_manifest_takes_precedence_over_infrastructure_fallback(self):
        suite = self.fixture / 'board.robot'
        suite.write_text('*** Test Cases ***\nBoard Case\n    [Tags]    case:board\n    No Operation\n')
        (self.fixture / 'tests.yaml').write_text('- board.robot\n')
        result = subprocess.run([sys.executable, str(self.fixture / 'harness/run_tests.py'), '--list'],
                                cwd=self.root, capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('case:board', result.stdout)
        self.assertNotIn('case:monitor-help', result.stdout)

    def test_exported_stm32_layout_runs_without_source_repository(self):
        from sync_plan import export_payload, load_plan
        _, targets, mappings = load_plan(ROOT)
        self.assertIn('ARTTU-Software/STM32-Template@main', targets)
        destination = self.root / 'standalone STM32 repository'
        export_payload(ROOT, destination, mappings)
        command = [sys.executable, str(destination / 'test/renode/harness/run_tests.py'), '--list']
        result = subprocess.run(command, cwd=destination, capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('case:monitor-help', result.stdout)
