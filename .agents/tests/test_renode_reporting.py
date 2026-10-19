"""Exercise workflow reporting with mock GitHub APIs; never publish live comments."""
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from helpers import ROOT

HAS_YAML = importlib.util.find_spec('yaml') is not None
NODE = shutil.which('node')
BRIDGE = r'''
const fs = require('fs');
const input = JSON.parse(fs.readFileSync(0, 'utf8'));
const actions = {checks: [], created: [], updated: [], summaries: []};
const summary = {addHeading() {return this;}, addRaw(text) {actions.summaries.push(text); return this;}, async write() {}};
const github = {rest: {
  checks: {create: async value => actions.checks.push(value)},
  issues: {listComments: () => {}, createComment: async value => actions.created.push(value),
           updateComment: async value => actions.updated.push(value)}
}, paginate: async () => input.comments || []};
process.env.RENODE_JOB_RESULT = input.result;
process.env.RENODE_ARTIFACT = 'renode-results';
const AsyncFunction = Object.getPrototypeOf(async function(){}).constructor;
new AsyncFunction('github', 'context', 'core', 'require', input.script)(github, input.context, {summary}, require)
  .then(() => process.stdout.write(JSON.stringify(actions)))
  .catch(error => {process.stderr.write(error.stack); process.exitCode = 1;});
'''


@unittest.skipUnless(HAS_YAML and NODE, 'Workflow reporting contracts require PyYAML and Node')
class RenodeReportingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import yaml
        cls.workflow = yaml.load((ROOT / '.github/workflows/renode-test.yml').read_text(), Loader=yaml.BaseLoader)
        steps = cls.workflow['jobs']['publish']['steps']
        cls.script = next(step['with']['script'] for step in steps if step.get('uses', '').startswith('actions/github-script@'))

    def report(self, *, exists=True, result='success', event='pull_request', fork=False, comments=None):
        with tempfile.TemporaryDirectory(prefix='renode report ') as directory:
            if exists:
                path = Path(directory) / 'renode-results/xunit.xml'
                path.parent.mkdir()
                path.write_text('<testsuite tests="1"/>')
            context = {'serverUrl': 'https://github.com', 'repo': {'owner': 'team', 'repo': 'firmware'},
                       'runId': 42, 'sha': 'a' * 40, 'eventName': event, 'issue': {'number': 7},
                       'payload': {'pull_request': {'head': {'repo': {'full_name': 'fork/firmware' if fork else 'team/firmware'}}}}}
            data = {'script': self.script, 'context': context, 'result': result, 'comments': comments or []}
            run = subprocess.run([NODE, '-e', BRIDGE], input=json.dumps(data), text=True,
                                 capture_output=True, cwd=directory, timeout=10)
            self.assertEqual(run.returncode, 0, run.stderr)
            return json.loads(run.stdout)

    def test_success_publishes_execution_check_and_artifact_link(self):
        result = self.report()
        self.assertEqual(result['checks'][0]['conclusion'], 'success')
        self.assertIn('actions/runs/42', result['created'][0]['body'])
        self.assertIn('renode-results', result['summaries'][0])

    def test_missing_report_is_failure_not_empty_success(self):
        result = self.report(exists=False, result='failure')
        self.assertEqual(result['checks'][0]['conclusion'], 'failure')
        self.assertIn('No xUnit report', result['created'][0]['body'])

    def test_valid_xml_does_not_hide_execution_failure(self):
        result = self.report(exists=True, result='failure')
        self.assertEqual(result['checks'][0]['conclusion'], 'failure')
        self.assertIn('**failure**', result['created'][0]['body'])

    def test_repeated_pr_run_updates_existing_bot_comment(self):
        comments = [{'id': 12, 'user': {'type': 'Bot'}, 'body': '<!-- renode-execution:renode-results -->'}]
        result = self.report(comments=comments)
        self.assertFalse(result['created'])
        self.assertEqual(result['updated'][0]['comment_id'], 12)

    def test_fork_pr_keeps_summary_without_writes(self):
        result = self.report(fork=True)
        self.assertTrue(result['summaries'])
        for field in ['checks', 'created', 'updated']:
            self.assertFalse(result[field])

    def test_manual_run_publishes_check_without_pr_comment(self):
        result = self.report(event='workflow_dispatch')
        self.assertEqual(result['checks'][0]['conclusion'], 'success')
        self.assertFalse(result['created'])

    def test_publisher_is_separate_and_has_required_permissions(self):
        publisher = self.workflow['jobs']['publish']
        self.assertEqual(publisher['needs'], 'renode')
        self.assertIn('always()', publisher['if'])
        self.assertEqual(self.workflow['jobs']['renode']['permissions'], {'contents': 'read'})
        self.assertEqual(publisher['runs-on'], 'ubuntu-24.04')
        for permission in ['checks', 'pull-requests']:
            self.assertEqual(publisher['permissions'][permission], 'write')
        self.assertEqual(publisher['permissions']['actions'], 'read')

    def test_draft_pr_skips_execution_and_publication(self):
        script = '''
const data = JSON.parse(require('fs').readFileSync(0, 'utf8'));
const condition = new Function('inputs', 'github', 'always', 'cancelled',
                              'return (' + data.condition + ');');
process.stdout.write(JSON.stringify(condition(data.inputs, data.github,
                                              () => true, () => false)));
'''
        for job in ['renode', 'publish']:
            for event, draft, enabled, expected in [
                    ('pull_request', True, True, False),
                    ('pull_request', False, True, True),
                    ('workflow_dispatch', None, True, True),
                    ('workflow_dispatch', None, False, False)]:
                with self.subTest(job=job, event=event, draft=draft, enabled=enabled):
                    github = {'event_name': event, 'event': {}}
                    if draft is not None:
                        github['event']['pull_request'] = {'draft': draft}
                    data = {'condition': self.workflow['jobs'][job]['if'],
                            'inputs': {'enabled': enabled}, 'github': github}
                    run = subprocess.run([NODE, '-e', script], input=json.dumps(data),
                                         text=True, capture_output=True, timeout=10)
                    self.assertEqual(run.returncode, 0, run.stderr)
                    self.assertEqual(json.loads(run.stdout), expected)
