"""Normalize vendor envelopes and emit only their documented decision shapes."""
import json
import os
import sys
from pathlib import Path
from policy import PolicyError, READ_WHOLE_LIMIT, READ_WINDOW_LIMIT
from edit_plan import resolve_path


def normalize(payload, vendor='auto'):
    if not isinstance(payload, dict):
        raise PolicyError('Hook input must be an object.')
    if vendor == 'auto':
        vendor = 'antigravity' if 'toolCall' in payload else ('cursor' if 'cursor_version' in payload else 'cli')
    if vendor == 'antigravity':
        call = payload.get('toolCall', {})
        name, args = call.get('name', ''), call.get('args', {})
    else:
        name = payload.get('tool_name', payload.get('name', payload.get('tool', '')))
        args = payload.get('tool_input', payload.get('tool_args', payload.get('arguments', {})))
        event = payload.get('hook_event_name')
        if event in {'beforeReadFile', 'beforeTabFileRead'}:
            name, args = 'Read', payload
        elif event == 'beforeShellExecution':
            name, args = 'Shell', payload
    if not isinstance(name, str) or not isinstance(args, dict):
        raise PolicyError('Invalid tool name or arguments.')
    roots = payload.get('workspacePaths', payload.get('workspace_roots', []))
    root = (payload.get('cwd') or os.environ.get('CLAUDE_PROJECT_DIR')
            or os.environ.get('CURSOR_PROJECT_DIR') or (roots[0] if roots else os.getcwd()))
    return vendor, name, args, Path(root).resolve()


def emit(vendor, allowed, reason='', *, stop=False):
    if stop:
        if vendor == 'antigravity':
            out = {'decision': 'allow' if allowed else 'continue', 'reason': reason}
        elif vendor == 'cursor':
            out = {} if allowed else {'followup_message': reason}
        else:
            out = {} if allowed else {'decision': 'block', 'reason': reason}
    elif vendor == 'antigravity':
        out = {'decision': 'allow' if allowed else 'deny'}
        if not allowed:
            out['reason'] = reason
    elif vendor == 'cursor':
        out = {'permission': 'allow' if allowed else 'deny'}
        if not allowed:
            out.update(user_message=reason, agent_message=reason)
    elif allowed:
        out = {}
    else:
        out = {'hookSpecificOutput': {'hookEventName': 'PreToolUse',
               'permissionDecision': 'deny', 'permissionDecisionReason': reason}}
    sys.stdout.write(json.dumps(out) + '\n')
    # Exit 2 also blocks CLI clients if JSON parsing is unavailable.
    if not allowed and vendor not in {'antigravity', 'cursor'} and not stop:
        sys.stderr.write(reason + '\n')
        return 2
    return 0


def check_read(args, root):
    raw = next((args[key] for key in ('file_path', 'AbsolutePath', 'path') if key in args), None)
    path = resolve_path(raw, root)
    start = args.get('StartLine', args.get('start_line'))
    end = args.get('EndLine', args.get('end_line'))
    span = None
    window = args.get('view_range', args.get('range'))
    if window is not None:
        if not isinstance(window, list) or len(window) != 2:
            raise PolicyError('Invalid read range.')
        start, end = window
    if 'offset' in args or 'limit' in args:
        offset, limit = args.get('offset', 0), args.get('limit')
        if type(offset) is not int or offset < 0 or type(limit) is not int or limit <= 0:
            raise PolicyError('Read offset/limit must be nonnegative/positive integers.')
        span = limit
    elif start is not None or end is not None:
        if type(start) is not int or type(end) is not int or not 1 <= start <= end:
            raise PolicyError('Read needs an ordered, positive line range.')
        span = end - start + 1
    if span is not None and span <= READ_WINDOW_LIMIT:
        return
    if not path.is_file():
        return  # Let the native tool report an absent file.
    with path.open(encoding='utf-8-sig', errors='replace') as source:
        for index, _ in enumerate(source, 1):
            if index > READ_WHOLE_LIMIT:
                raise PolicyError(f'{path.name}: use a graph snippet or a <=100-line window.')
