"""Run the shared workflow's collector against temporary Ceedling report layouts."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from helpers import ROOT


@unittest.skipUnless(importlib.util.find_spec('yaml'), 'Workflow contracts require PyYAML')
class CeedlingReportingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import yaml
        cls.workflow = yaml.load((ROOT / '.github/workflows/ceedling-test.yml').read_text(encoding='utf-8'),
                                 Loader=yaml.BaseLoader)
        cls.steps = {step['name']: step for step in cls.workflow['jobs']['build']['steps']}
        run = cls.steps['Collect Ceedling Reports']['run']
        cls.collector = run.split("python3 - <<'PY'\n", 1)[1].rsplit('\nPY', 1)[0]

    def collect(self, roots=('build',), *, coverage=True, junit=True, text=True, other_mode=False):
        with tempfile.TemporaryDirectory(prefix='ceedling reports ') as directory:
            workspace = Path(directory)
            runner_temp = workspace / 'runner-temp'
            runner_temp.mkdir()
            mode = 'gcov' if coverage else 'test'
            for root in roots:
                reports = workspace / root / 'artifacts' / mode
                reports.mkdir(parents=True)
                if junit:
                    (reports / 'junit_tests_report.xml').write_text(
                        '<testsuite tests="1"><testcase name="passes"/></testsuite>', encoding='utf-8')
                if coverage and text:
                    (reports / 'gcovr').mkdir()
                    (reports / 'gcovr/coverage.txt').write_text('TOTAL 10 8 80%\n', encoding='utf-8')
                if other_mode:
                    stale = workspace / root / 'artifacts' / ('test' if coverage else 'gcov')
                    stale.mkdir()
                    (stale / 'junit_tests_report.xml').write_text('<testsuite tests="99"/>', encoding='utf-8')
            output = workspace / 'outputs'
            summary = workspace / 'summary'
            env = dict(os.environ, COVERAGE_ENABLED=str(coverage).lower(), RUNNER_TEMP=str(runner_temp),
                       GITHUB_OUTPUT=str(output), GITHUB_STEP_SUMMARY=str(summary))
            run = subprocess.run([sys.executable, '-c', self.collector], cwd=workspace,
                                 env=env, capture_output=True, text=True, encoding='utf-8', timeout=15)
            # Parse the actual Actions output protocol, including multiline values.
            values = {}
            lines = iter(output.read_text(encoding='utf-8').splitlines())
            for line in lines:
                if '<<' in line:
                    name, delimiter = line.split('<<', 1)
                    parts = []
                    for part in lines:
                        if part == delimiter:
                            break
                        parts.append(part)
                    values[name] = '\n'.join(parts)
                else:
                    name, value = line.split('=', 1)
                    values[name] = value
            content = Path(values['coverage_file']).read_text(encoding='utf-8') if 'coverage_file' in values else ''
            return run, values, content, summary.read_text(encoding='utf-8') if summary.exists() else ''

    def test_default_nested_and_custom_build_roots(self):
        for root in ['build', 'build/host', 'custom output/native']:
            with self.subTest(root=root):
                run, outputs, coverage, summary = self.collect(roots=(root,))
                self.assertEqual(run.returncode, 0, run.stderr)
                self.assertEqual(outputs['junit_files'], f'{root}/artifacts/gcov/junit_tests_report.xml')
                self.assertEqual(outputs['artifact_paths'], f'{root}/artifacts/gcov')
                self.assertIn('TOTAL 10 8 80%', coverage)
                self.assertIn(coverage, summary)

    def test_coverage_disabled_publishes_only_test_reports(self):
        run, outputs, coverage, summary = self.collect(coverage=False, other_mode=True)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(outputs['junit_files'], 'build/artifacts/test/junit_tests_report.xml')
        self.assertNotIn('coverage_file', outputs)
        self.assertEqual(coverage + summary, '')

    def test_gcov_run_does_not_publish_test_mode_reports(self):
        run, outputs, _, _ = self.collect(other_mode=True)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(outputs['junit_files'], 'build/artifacts/gcov/junit_tests_report.xml')

    def test_missing_junit_fails_even_with_other_mode_report(self):
        run, outputs, coverage, _ = self.collect(junit=False, other_mode=True)
        self.assertNotEqual(run.returncode, 0)
        self.assertIn('::error::Missing Ceedling JUnit', run.stdout)
        self.assertEqual(outputs['junit_files'], '')
        self.assertIn('TOTAL', coverage)

    def test_missing_coverage_fails_but_preserves_junit_for_publication(self):
        run, outputs, _, _ = self.collect(text=False)
        self.assertNotEqual(run.returncode, 0)
        self.assertIn('::error::Missing Ceedling coverage summary', run.stdout)
        self.assertTrue(outputs['junit_files'])
        self.assertNotIn('coverage_file', outputs)

    def test_no_artifacts_fails_with_diagnostics(self):
        run, outputs, _, _ = self.collect(roots=())
        self.assertNotEqual(run.returncode, 0)
        self.assertEqual(run.stdout.count('::error::Missing Ceedling'), 2)
        self.assertEqual(outputs['artifact_paths'], '')

    def test_multiple_projects_keep_all_reports(self):
        run, outputs, coverage, _ = self.collect(roots=('one/build', 'two/build/host'))
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(len(outputs['junit_files'].splitlines()), 2)
        self.assertEqual(len(outputs['artifact_paths'].splitlines()), 2)
        for root in ['one/build', 'two/build/host']:
            self.assertIn(f'{root}/artifacts/gcov/gcovr/coverage.txt', coverage)

    def test_consumers_use_collected_paths_and_reject_empty_results(self):
        publisher = self.steps['Publish Unit Test Results']
        self.assertEqual(publisher['with']['files'], '${{ steps.reports.outputs.junit_files }}')
        for option in ['action_fail', 'action_fail_on_inconclusive']:
            self.assertEqual(publisher['with'][option], 'true')
        self.assertIn('always()', publisher['if'])
        upload = self.steps['Upload Ceedling Reports']
        self.assertEqual(upload['with']['path'], '${{ steps.reports.outputs.artifact_paths }}')
        self.assertIn('always()', upload['if'])
        comment = self.steps['Comment Coverage on PR']
        self.assertEqual(comment['env']['COVERAGE_FILE'], '${{ steps.reports.outputs.coverage_file }}')
        self.assertIn('process.env.COVERAGE_FILE', comment['with']['script'])
        self.assertNotIn('build/artifacts', comment['with']['script'])

    @unittest.skipUnless(shutil.which('node'), 'Comment execution requires Node')
    def test_coverage_comment_creates_then_updates_with_actual_summary(self):
        script = self.steps['Comment Coverage on PR']['with']['script']
        bridge = r'''
        const fs = require('fs');
        const input = JSON.parse(fs.readFileSync(0, 'utf8'));
        const writes = [];
        const github = {rest: {issues: {
          listComments: async () => ({data: input.comments}),
          createComment: async value => writes.push({kind: 'create', ...value}),
          updateComment: async value => writes.push({kind: 'update', ...value})
        }}};
        const context = {repo: {owner: 'team', repo: 'firmware'}, issue: {number: 9}};
        const AsyncFunction = Object.getPrototypeOf(async function(){}).constructor;
        new AsyncFunction('github', 'context', 'require', input.script)(github, context, require)
          .then(() => process.stdout.write(JSON.stringify(writes)))
          .catch(error => {console.error(error); process.exitCode = 1;});
        '''
        with tempfile.TemporaryDirectory(prefix='coverage comment ') as directory:
            report = Path(directory) / 'summary.md'
            content = '### build/host/artifacts/gcov/gcovr/coverage.txt\n\n```text\nTOTAL 80%\n```'
            report.write_text(content, encoding='utf-8', newline='\n')
            for comments, expected in [([], 'create'),
                                       ([{'id': 7, 'body': '### 📊 Code Coverage Summary\nold'}], 'update')]:
                run = subprocess.run([shutil.which('node'), '-e', bridge],
                                     input=json.dumps({'script': script, 'comments': comments}),
                                     env=dict(os.environ, COVERAGE_FILE=str(report)),
                                     capture_output=True, text=True, encoding='utf-8', timeout=10)
                self.assertEqual(run.returncode, 0, run.stderr)
                writes = json.loads(run.stdout)
                self.assertEqual(len(writes), 1)
                self.assertEqual(writes[0]['kind'], expected)
                self.assertEqual(writes[0]['body'], f'### 📊 Code Coverage Summary\n\n{content}')
                if expected == 'update':
                    self.assertEqual(writes[0]['comment_id'], 7)
