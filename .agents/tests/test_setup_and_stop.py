import json
import os
import re
import shutil
import subprocess
import sys
import unittest
from helpers import Fixture, HOOKS, ROOT, SOURCE
from doctor import CONFIGS, RUNTIME_FILES, validate_configs


class SetupTests(Fixture):
    def copy_harness(self):
        shutil.copytree(HOOKS, self.root/'.agents/hooks', ignore=shutil.ignore_patterns('__pycache__'))
        for name in list(CONFIGS.values()) + ['.cursor/mcp.json','.mcp.json','.codex/config.toml','.github/sync.yml']:
            if name == '.github/sync.yml' and not (ROOT/name).is_file():
                continue
            path = self.root/name
            path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT/name, path)
        for name in ['.agents/skills', '.agents/tests']:
            shutil.copytree(ROOT/name, self.root/name, ignore=shutil.ignore_patterns('__pycache__'))
        for name in ['AGENTS.md','CLAUDE.md','GEMINI.md','.agents/.gitignore',
                     '.agents/harness-manifest.json', '.github/workflows/agent-harness-check.yml']:
            (self.root/name).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT/name, self.root/name)

    def test_project_configuration_contract(self):
        validate_configs(ROOT)
        manifest = json.loads((ROOT/'.agents/harness-manifest.json').read_text())
        self.assertEqual(manifest['files'], RUNTIME_FILES)

    def test_downstream_setup_does_not_require_central_sync_config(self):
        self.copy_harness()
        (self.root/'.github/sync.yml').unlink(missing_ok=True)
        (self.root/'.agents/harness-manifest.json').unlink()
        shutil.rmtree(self.root/'.agents/tests')
        (self.root/'.github/workflows/agent-harness-check.yml').unlink()
        (self.root/'.agents/hooks/sync_plan.py').unlink()
        (self.root/'.agents/hooks/benchmark_context.py').unlink()
        validate_configs(self.root)

    def test_sync_omissions_and_wrong_event_names_fail_doctor(self):
        self.copy_harness()
        path = self.root/'.cursor/hooks.json'
        data = json.loads(path.read_text())
        data['hooks']['PreToolUse'] = data['hooks'].pop('preToolUse')
        path.write_text(json.dumps(data))
        with self.assertRaises(ValueError):
            validate_configs(self.root)
        shutil.copyfile(ROOT/'.cursor/hooks.json', path)
        sync = self.root/'.github/sync.yml'
        if not sync.is_file():
            return
        sync.write_text(sync.read_text().replace('source: .codex/hooks.json','source: omitted.json'))
        with self.assertRaises(ValueError):
            validate_configs(self.root)

    def test_configured_commands_work_in_documented_working_directories(self):
        self.copy_harness()
        nested = self.root/'nested directory'
        nested.mkdir()
        for vendor, relative in CONFIGS.items():
            with self.subTest(vendor=vendor):
                data = json.loads((self.root/relative).read_text())
                events = data['arttu-guardrails'] if vendor == 'antigravity' else data['hooks']
                group = events['preToolUse' if vendor == 'cursor' else 'PreToolUse'][0]
                command = group['command'] if vendor == 'cursor' else group['hooks'][0]['command']
                payload = {'cwd':str(self.root),'tool_name':'Read','tool_input':{'file_path':str(self.small)}}
                if vendor == 'antigravity':
                    payload = {'workspacePaths':[str(self.root)],'toolCall':{'name':'view_file','args':{'AbsolutePath':str(self.small)}}}
                if vendor == 'antigravity':
                    # Antigravity runs sh -c / cmd /c in hooks.json's directory.
                    cwd = self.root/'.agents'
                    shell = ([os.environ.get('COMSPEC', 'cmd.exe'), '/d', '/s', '/c', command]
                             if os.name == 'nt' else ['/bin/sh', '-c', command])
                else:
                    cwd = nested
                    shell = (['powershell.exe', '-NoProfile', '-NonInteractive', '-Command', command]
                             if os.name == 'nt' else ['/bin/sh', '-c', command])
                result = subprocess.run(shell,input=json.dumps(payload),text=True,capture_output=True,cwd=cwd,timeout=10)
                self.assertEqual(result.returncode,0,result.stderr)
                response = json.loads(result.stdout)
                self.assertNotIn('deny',response.values())

    def test_antigravity_native_shell_preserves_denials_and_stop(self):
        self.copy_harness()
        self.init_git()
        events = json.loads((self.root/'.agents/hooks.json').read_text())['arttu-guardrails']
        def launch(command, payload):
            shell = ([os.environ.get('COMSPEC', 'cmd.exe'), '/d', '/s', '/c', command]
                     if os.name == 'nt' else ['/bin/sh', '-c', command])
            result = subprocess.run(shell, input=json.dumps(payload), text=True, capture_output=True,
                                    cwd=self.root/'.agents', timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr)
            return json.loads(result.stdout)
        command = events['PreToolUse'][0]['hooks'][0]['command']
        payload = {'workspacePaths':[str(self.root)], 'toolCall':{'name':'view_file',
                   'args':{'AbsolutePath':str(self.large)}}}
        self.assertEqual(launch(command, payload)['decision'], 'deny')
        payload['toolCall']['args'].update(StartLine=1, EndLine=3)
        self.assertEqual(launch(command, payload)['decision'], 'allow')
        payload['toolCall'] = {'name':'write_to_file', 'args':{'TargetFile':str(self.app),
                              'CodeContent':'void *p = malloc(16);'}}
        self.assertEqual(launch(command, payload)['decision'], 'deny')
        self.assertEqual(launch(events['Stop'][0]['command'],
                         {'workspacePaths':[str(self.root)], 'conversationId':'test'})['decision'], 'allow')

    def test_doctor_rejects_antigravity_inline_python(self):
        self.copy_harness()
        path = self.root/'.agents/hooks.json'
        data = json.loads(path.read_text())
        data['arttu-guardrails']['PreToolUse'][0]['hooks'][0]['command'] = (
            'python -c "import sys" --vendor antigravity')
        path.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, 'standalone script'):
            validate_configs(self.root)

    def test_skill_entrypoints_and_local_references(self):
        entrypoints = ['AGENTS.md', '.agents/skills/arttu-code-discovery/SKILL.md',
                      '.agents/skills/arttu-cstyle/SKILL.md', '.agents/skills/arttu-docs-assistant/SKILL.md']
        for relative in entrypoints:
            with self.subTest(relative=relative):
                text = (ROOT/relative).read_text(encoding='utf-8-sig')
                self.assertTrue(text.strip())
                for link in re.findall(r'\]\((references/[^)]+)\)',text):
                    self.assertTrue((ROOT/relative).parent.joinpath(link).is_file(),link)

    def test_workflows_use_immutable_action_refs(self):
        paths = ((ROOT/'.github/workflows').glob('*.yml') if (ROOT/'.github/sync.yml').is_file()
                 else [ROOT/'.github/workflows/agent-harness-check.yml'])
        for path in paths:
            for ref in re.findall(r'uses:\s*([^\s#]+)',path.read_text()):
                self.assertRegex(ref,r'^[\w.-]+/[\w./-]+@[0-9a-f]{40}$',str(path))


class StopTests(Fixture):
    def setUp(self):
        super().setUp()
        self.init_git()

    def stop(self, vendor, active=False):
        payload = {'cwd':str(self.root),'session_id':'test','stop_hook_active':active}
        if vendor == 'antigravity':
            payload = {'workspacePaths':[str(self.root)],'conversationId':'test','executionNum':1}
        if vendor == 'cursor':
            payload['loop_count'] = int(active)
        result = subprocess.run([sys.executable,str(HOOKS/'stop_gate.py'),'--vendor',vendor],
                                input=json.dumps(payload),text=True,capture_output=True,cwd=self.root,timeout=10)
        self.assertEqual(result.returncode,0,result.stderr)
        return json.loads(result.stdout)

    def test_clean_tree_allows_stop(self):
        for vendor in ['claude','codex','cursor','antigravity']:
            with self.subTest(vendor=vendor):
                response = self.stop(vendor)
                self.assertNotEqual(response.get('decision'),'block')
                self.assertNotEqual(response.get('decision'),'continue')

    def test_failure_requests_one_repair_then_reports_limitation(self):
        self.main.write_text(SOURCE.replace('int generated = 0;','int generated = 1;'))
        first = self.stop('codex')
        self.assertEqual(first['decision'],'block')
        second = self.stop('codex',True)
        self.assertIn('systemMessage',second)

    def test_antigravity_continuation_is_bounded_without_active_flag(self):
        self.main.write_text(SOURCE.replace('int generated = 0;','int generated = 1;'))
        self.assertEqual(self.stop('antigravity')['decision'],'continue')
        self.assertEqual(self.stop('antigravity')['decision'],'allow')


if __name__ == '__main__':
    unittest.main()
