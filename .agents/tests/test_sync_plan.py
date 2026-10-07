"""Exercise the actual central sync mappings, not a manually assembled harness."""
import subprocess
import sys
import unittest
from helpers import Fixture, ROOT
from doctor import validate_configs
from sync_plan import export_payload, load_plan


@unittest.skipUnless((ROOT / '.github/sync.yml').is_file(), 'Central distribution configuration only')
class SyncPlanTests(Fixture):
    def test_exported_runtime_works_without_central_harness_assets(self):
        _, targets, mappings = load_plan(ROOT)
        self.assertIn('ARTTU-Software/BMS-Master@dev', targets)
        export_payload(ROOT, self.root, mappings)
        validate_configs(self.root)
        for path in ['.github/sync.yml', '.agents/tests', '.agents/harness-manifest.json',
                     'docs/agent-harness.md', '.github/workflows/agent-harness-check.yml',
                     '.agents/hooks/benchmark_context.py', '.agents/hooks/sync_plan.py']:
            self.assertFalse((self.root / path).exists(), path)
        result = subprocess.run(
            [sys.executable, '.agents/hooks/doctor.py'],
            cwd=self.root, capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        references = list((ROOT / '.agents/skills').glob('*/references/**/*'))
        self.assertTrue(any(path.is_file() for path in references))
        for path in references:
            if path.is_file():
                self.assertEqual(path.read_bytes(), (self.root / path.relative_to(ROOT)).read_bytes())
        result = subprocess.run([sys.executable, '.agents/hooks/doctor.py', '--self-test'],
                                cwd=self.root, capture_output=True, text=True, timeout=10)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('central-only', result.stderr)

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

    def test_workflow_uses_plan_and_scoped_runtime_permissions(self):
        text = (ROOT / '.github/workflows/sync-agent-rules.yml').read_text()
        for declaration in ['needs: plan', 'fromJSON(needs.plan.outputs.matrix)',
                            'repositories: ${{ matrix.repository }}',
                            'permission-contents: write', 'permission-pull-requests: write']:
            self.assertIn(declaration, text)
        self.assertNotIn('permission-workflows:', text)

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
