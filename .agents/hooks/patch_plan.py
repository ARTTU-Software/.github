"""Validate the supported apply_patch format conservatively, before execution."""
from edit_plan import read_source, resolve_path
from policy import PolicyError


def apply_hunks(before, body):
    lines, cursor = before.splitlines(), 0
    index = 0
    while index < len(body):
        header = body[index]
        if not header.startswith('@@'):
            raise PolicyError('Patch hunk needs @@ context.')
        anchor = header[2:].strip()
        if anchor:
            positions = [i for i in range(cursor, len(lines)) if lines[i] == anchor]
            if len(positions) != 1:
                raise PolicyError('Patch anchor is missing or ambiguous.')
            cursor = positions[0] + 1
        index += 1
        old, new, eof = [], [], False
        while index < len(body) and not body[index].startswith('@@'):
            line = body[index]
            index += 1
            if line == '*** End of File':
                eof = True
                if index < len(body) and not body[index].startswith('@@'):
                    raise PolicyError('Unexpected content after EOF marker.')
                break
            if not line or line[0] not in ' +-':
                raise PolicyError('Unsupported patch line.')
            if line[0] in ' -':
                old.append(line[1:])
            if line[0] in ' +':
                new.append(line[1:])
        if not old:
            if lines:
                raise PolicyError('Insertion needs source context.')
            positions = [0]
        else:
            positions = [i for i in range(cursor, len(lines) - len(old) + 1)
                         if lines[i:i + len(old)] == old
                         and (not eof or i + len(old) == len(lines))]
        if len(positions) != 1:
            raise PolicyError('Patch text is missing or ambiguous; add context.')
        start = positions[0]
        lines[start:start + len(old)] = new
        cursor = start + len(new)
    ending = '\n' if before.endswith('\n') or not before else ''
    return '\n'.join(lines) + (ending if lines else '')


def patch_edits(args, root):
    patch = args.get('command', args.get('patch', args.get('input')))
    if not isinstance(patch, str):
        raise PolicyError('Missing patch text.')
    lines = patch.splitlines()
    if not lines or lines[0] != '*** Begin Patch' or lines[-1] != '*** End Patch':
        raise PolicyError('Unsupported patch envelope.')
    plans, seen, index = [], set(), 1
    while index < len(lines) - 1:
        header = lines[index]
        action = next((key for key in ('Add', 'Update', 'Delete')
                       if header.startswith(f'*** {key} File: ')), None)
        if action is None:
            raise PolicyError('Unsupported patch operation.')
        path = resolve_path(header.split(': ', 1)[1], root)
        if path in seen:
            raise PolicyError('Repeated patch file; combine its hunks.')
        seen.add(path)
        before, index = read_source(path), index + 1
        if action == 'Delete':
            if not path.is_file():
                raise PolicyError('Delete target does not exist.')
            plans.append((path, before, None, False))
            continue
        body = []
        while index < len(lines) - 1 and not lines[index].startswith(('*** Add File:', '*** Update File:', '*** Delete File:', '*** Move to:')):
            body.append(lines[index])
            index += 1
        if action == 'Add':
            if path.exists() or any(not line.startswith('+') for line in body):
                raise PolicyError('Invalid new patch file.')
            after = '\n'.join(line[1:] for line in body) + ('\n' if body else '')
        else:
            if not path.is_file() or not body:
                raise PolicyError('Invalid patch target or empty update.')
            after = apply_hunks(before, body)
        plans.append((path, before, after, False))
    if not plans:
        raise PolicyError('Empty patch.')
    return plans
