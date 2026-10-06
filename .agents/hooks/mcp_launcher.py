"""Portable stdio launch of reviewed npm MCP packages, including Windows .cmd."""
import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

PACKAGES = {'codebase-memory-mcp@0.11.0', 'markdown-docs-mcp@0.1.5'}


def launch_command(package, platform=sys.platform):
    if package not in PACKAGES:
        raise ValueError('MCP package/version is not in the reviewed allowlist.')
    executable = shutil.which('npx.cmd' if platform == 'win32' else 'npx')
    if not executable:
        raise FileNotFoundError('Install Node.js/npm; npx is not on PATH.')
    return [executable, '-y', package], platform == 'win32'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('package', choices=sorted(PACKAGES))
    args = parser.parse_args()
    try:
        command, shell = launch_command(args.package)
        # stdout/stdin belong exclusively to the MCP wire protocol.
        options = {'creationflags': subprocess.CREATE_NO_WINDOW} if sys.platform == 'win32' else {}
        result = subprocess.run(command, shell=shell, cwd=Path(__file__).resolve().parents[2],
                                env=os.environ.copy(), **options)
        return result.returncode
    except Exception as error:
        print(f'MCP launcher: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
