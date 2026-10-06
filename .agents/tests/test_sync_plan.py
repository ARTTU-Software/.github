"""Exercise the actual central sync mappings, not a manually assembled harness."""
import os
import subprocess
import sys
import unittest
from helpers import Fixture, ROOT
from doctor import validate_configs
from sync_plan import export_payload, load_plan


@unittest.skipUnless((ROOT / '.github/sync.yml').is_file(), 'Central distribution configuration only')
class SyncPlanTests(Fixture):
    def test_exported_bundle_runs_its_own_regression_suite(self):
        _, targets, mappings = load_plan(ROOT)
        self.assertIn('ARTTU-Software/BMS-Master@dev', targets)
        export_payload(ROOT, self.root, mappings)
        validate_configs(self.root)
        self.assertFalse((self.root / '.github/sync.yml').exists())
        result = subprocess.run(
            [sys.executable, '-m', 'unittest', 'discover', '-s', '.agents/tests', '-q'],
            cwd=self.root, capture_output=True, text=True, timeout=120,
            env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_matrix_and_render_use_configured_targets(self):
        import json
        script = ROOT / '.agents/hooks/sync_plan.py'
        result = subprocess.run([sys.executable, str(script), 'matrix'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        entries = json.loads(result.stdout)['include']
        header, targets, _ = load_plan(ROOT)
        self.assertEqual([entry['target'] for entry in entries], targets)
        for entry in entries:
            output = self.root / '.github/sync.yml'
            output.parent.mkdir(parents=True, exist_ok=True)
            result = subprocess.run([sys.executable, str(script), 'render', '--target', entry['target'],
                                     '--output', str(output)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(output.read_text(), header + '    repos: |\n      ' + entry['target'] + '\n')

    def test_workflow_uses_plan_and_scoped_workflow_permission(self):
        text = (ROOT / '.github/workflows/sync-agent-rules.yml').read_text()
        for declaration in ['needs: plan', 'fromJSON(needs.plan.outputs.matrix)',
                            'repositories: ${{ matrix.repository }}', 'permission-workflows: write',
                            'permission-contents: write', 'permission-pull-requests: write']:
            self.assertIn(declaration, text)

    def test_invalid_targets_and_destination_omissions_fail(self):
        path = self.root / '.github/sync.yml'
        path.parent.mkdir(parents=True, exist_ok=True)
        original = (ROOT / '.github/sync.yml').read_text()
        for suffix in ['      ARTTU-Software/BMS-Master@dev\n', '      bad target\n']:
            path.write_text(original + suffix)
            with self.assertRaises(ValueError):
                load_plan(self.root)
        _, _, mappings = load_plan(ROOT)
        mappings = [(source, 'wrong.json' if source == '.codex/hooks.json' else dest)
                    for source, dest in mappings]
        export_payload(ROOT, self.root, mappings)
        with self.assertRaises((ValueError, FileNotFoundError)):
            validate_configs(self.root)
