"""Validate local setup without installing packages or assuming hooks are trusted."""
import argparse
import json
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

CONFIGS = {'antigravity': '.agents/hooks.json', 'codex': '.codex/hooks.json',
           'claude': '.claude/settings.json', 'cursor': '.cursor/hooks.json'}
HOOK_SCRIPTS = ('pre_tool_enforcer.py', 'stop_gate.py')


def validate_configs(root):
    for vendor, relative in CONFIGS.items():
        data = json.loads((root / relative).read_text(encoding='utf-8-sig'))
        events = data['arttu-guardrails'] if vendor == 'antigravity' else data['hooks']
        if vendor == 'cursor':
            if data.get('version') != 1 or not {'preToolUse', 'stop'} <= events.keys():
                raise ValueError('Invalid Cursor event names or schema version.')
            handlers = events['preToolUse'] + events['stop']
            if not all(item.get('failClosed') for item in events['preToolUse']):
                raise ValueError('Cursor preflight must fail closed.')
        else:
            groups = events['PreToolUse'] + (events['Stop'] if vendor != 'antigravity' else [])
            if not all(isinstance(group.get('hooks'), list) and group['hooks'] for group in groups):
                raise ValueError(f'{vendor}: missing nested hook handlers.')
            handlers = [handler for group in groups for handler in group['hooks']]
            if vendor == 'antigravity':
                handlers += events['Stop']
        for handler in handlers:
            if (not isinstance(handler.get('command'), str)
                    or f'--vendor {vendor}' not in handler['command']
                    or not 0 < handler.get('timeout', 0) <= 300):
                raise ValueError(f'{vendor}: invalid command, adapter, or timeout.')
            if vendor == 'antigravity' and handler['command'].partition(' --allow-protected ')[0] not in {
                    f'python hooks/{script} --vendor antigravity' for script in HOOK_SCRIPTS}:
                raise ValueError('Antigravity requires a standalone script relative to .agents; no inline Python.')
        if not all(any(script in handler['command'] for handler in handlers) for script in HOOK_SCRIPTS):
            raise ValueError(f'{vendor}: missing preflight or checkpoint script.')
    for script in HOOK_SCRIPTS:
        if not (root / '.agents/hooks' / script).is_file():
            raise ValueError(f'Missing script: {script}.')
    cursor = json.loads((root / '.cursor/mcp.json').read_text())['mcpServers']
    claude = json.loads((root / '.mcp.json').read_text())['mcpServers']
    codex = tomllib.loads((root / '.codex/config.toml').read_text())['mcp_servers']
    if cursor != claude or cursor != codex:
        raise ValueError('MCP definitions differ between clients.')
    if any('@' not in entry['args'][-1] for entry in cursor.values()):
        raise ValueError('MCP packages must use reviewed, explicit versions.')
    from mcp_launcher import PACKAGES
    if {entry['args'][-1] for entry in cursor.values()} != PACKAGES:
        raise ValueError('MCP config versions differ from the launcher allowlist.')
    manifest = json.loads((root / '.agents/harness-manifest.json').read_text())
    if manifest.get('version') != 1:
        raise ValueError('Unsupported harness manifest version.')
    required = manifest['files']
    sync_path = root / '.github/sync.yml'
    mappings = None
    if sync_path.is_file():
        from sync_plan import load_plan
        _, _, pairs = load_plan(root)
        mappings = dict(pairs)
    for path in required:
        if not (root / path).exists():
            raise ValueError(f'Missing distributed harness component: {path}.')
        if mappings is not None and mappings.get(path) != path:
            raise ValueError(f'Sync omits or relocates {path}.')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    root = args.root.resolve()
    try:
        validate_configs(root)
        print('PASS: native hook shapes, adapter selection, scripts, pinned MCP definitions, sync completeness.')
        for executable in ['git', 'python', 'npx', 'codex', 'claude', 'cursor', 'ceedling']:
            print(f'{executable}: {"on PATH" if shutil.which(executable) else "not on PATH"}')
        print('Hook activation/trust and live MCP connectivity: not inferred; check the client hook/MCP UI.')
        print('Antigravity MCP: import the pinned .mcp.json server entries in its MCP settings.')
        if args.self_test:
            return subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', str(root / '.agents/tests'), '-q'], cwd=root).returncode
    except Exception as error:
        print(f'FAIL: {error}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
