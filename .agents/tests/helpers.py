"""Small isolated fixtures; no probe performs its proposed firmware operation."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HOOKS = ROOT / '.agents/hooks'
sys.path.insert(0, str(HOOKS))
SOURCE = ('int generated = 0;\n/* USER CODE BEGIN 0 */\nuser_call();\n'
          '/* USER CODE END 0 */\nint duplicate = 0;\n'
          '/* USER CODE BEGIN 1 */\nshared();\n/* USER CODE END 1 */\nshared();\n')


class Fixture(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='arttu harness ')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.main = self.root / 'Core/Src/main.c'
        self.main.parent.mkdir(parents=True)
        self.main.write_text(SOURCE, newline='\n')
        self.app = self.root / 'Core/Src/App/logic.c'
        self.app.parent.mkdir()
        self.app.write_text('void application(void) {}\n')
        self.large = self.root / 'large.c'
        self.large.write_text('int item;\n' * 201)
        self.small = self.root / 'small.c'
        self.small.write_text('int item;\n' * 200)

    def run_git(self, *args):
        return subprocess.run(['git', '-C', str(self.root), *args], check=True,
                              capture_output=True, timeout=15)

    def init_git(self):
        self.run_git('init', '-q')
        (self.root / '.gitattributes').write_text('* -text\n')
        self.run_git('config', 'user.email', 'fixture@example.invalid')
        self.run_git('config', 'user.name', 'Harness test fixture')
        self.run_git('config', 'core.autocrlf', 'false')
        self.run_git('add', '.')
        self.run_git('commit', '-qm', 'Fixture baseline')

    def invoke(self, name, args, vendor='claude', raw=None):
        if vendor == 'antigravity':
            payload = {'workspacePaths': [str(self.root)], 'toolCall': {'name': name, 'args': args}}
        else:
            payload = {'cwd': str(self.root), 'tool_name': name, 'tool_input': args}
        result = subprocess.run([sys.executable, str(HOOKS / 'pre_tool_enforcer.py'), '--vendor', vendor],
                                input=raw if raw is not None else json.dumps(payload),
                                text=True, capture_output=True, cwd=self.root, timeout=5)
        response = json.loads(result.stdout)
        denied = (result.returncode == 2 or response.get('decision') == 'deny'
                  or response.get('permission') == 'deny'
                  or response.get('hookSpecificOutput', {}).get('permissionDecision') == 'deny')
        return denied, result, response

    def assert_gate(self, name, args, denied, vendor='claude'):
        actual, result, response = self.invoke(name, args, vendor)
        self.assertEqual(actual, denied, (result.stderr, response))
        self.assertNotEqual(result.returncode, 1, result.stderr)
