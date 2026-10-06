#!/usr/bin/env python3
"""Cheap preflight gate; successful calls add no explanatory context."""
import argparse
import json
import sys
from pathlib import Path
from edit_plan import file_edit
from hook_io import check_read, emit, normalize
from patch_plan import patch_edits
from policy import PolicyError, validate_change
from shell_policy import check_shell


def check_tool(name, args, root, approved=()):
    lower = name.lower()
    if lower in {'write_stdin', 'functions.write_stdin'}:
        return
    if lower in {'apply_patch', 'functions.apply_patch'} or lower.endswith('__apply_patch'):
        plans = patch_edits(args, root)
    elif lower in {'bash', 'shell', 'run_command', 'exec_command', 'functions.exec_command'}:
        check_shell(args, root)
        return
    elif lower.endswith(('__read_section', '.read_section')) or lower == 'read_section':
        return
    elif any(token in lower for token in ('write', 'edit', 'replace', 'delete_file')) or lower == 'delete':
        plans = file_edit(name, args, root)
    elif any(token in lower for token in ('read', 'view')):
        if any(key in args for key in ('file_path', 'AbsolutePath', 'path')):
            check_read(args, root)
        return
    else:
        return
    for path, before, after, whole in plans:
        validate_change(path, before, after, whole_write=whole, allow_protected=approved)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--vendor', choices=['auto', 'antigravity', 'claude', 'codex', 'cursor'], default='auto')
    parser.add_argument('--allow-protected', action='append', default=[], help='Exact absolute path explicitly approved in a reviewed hook definition.')
    options = parser.parse_args()
    vendor = options.vendor if options.vendor != 'auto' else 'cli'
    try:
        raw = sys.stdin.read(2 * 1024 * 1024 + 1)
        if len(raw) > 2 * 1024 * 1024:
            raise PolicyError('Hook payload exceeds 2 MiB; split the operation.')
        payload = json.loads(raw)
        vendor, name, args, root = normalize(payload, options.vendor)
        if not name:
            raise PolicyError('Missing tool name.')
        if any(not Path(path).is_absolute() for path in options.allow_protected):
            raise PolicyError('Protected-file hook exceptions need exact absolute paths.')
        approved = {str(Path(path).resolve()) for path in options.allow_protected}
        check_tool(name, args, root, approved)
    except Exception as error:
        return emit(vendor, False, f'ARTTU: {error}')
    return emit(vendor, True)


if __name__ == '__main__':
    sys.exit(main())
