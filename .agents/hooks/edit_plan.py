"""Reconstruct complete tool edits without modifying the working tree."""
from pathlib import Path
from policy import PolicyError


def resolve_path(raw, root):
    if not isinstance(raw, str) or not raw:
        raise PolicyError('Missing file path.')
    path = Path(raw)
    return (path if path.is_absolute() else root / path).resolve()


def read_source(path):
    if path.exists():
        return path.read_text(encoding='utf-8-sig')
    return ''


def replacements(before, args):
    chunks = args.get('ReplacementChunks', args.get('edits', [args]))
    if not isinstance(chunks, list) or not chunks:
        raise PolicyError('Missing edit chunks.')
    spans = []
    lines = before.splitlines(keepends=True)
    for chunk in chunks:
        if not isinstance(chunk, dict):
            raise PolicyError('Invalid edit chunk.')
        old = chunk.get('old_string', chunk.get('TargetContent'))
        new = chunk.get('new_string', chunk.get('ReplacementContent'))
        if not isinstance(old, str) or not old or not isinstance(new, str):
            raise PolicyError('Each edit needs nonempty old text and replacement text.')
        start, end = chunk.get('StartLine'), chunk.get('EndLine')
        offset, window = 0, before
        if start is not None or end is not None:
            if (type(start) is not int or type(end) is not int
                    or not 1 <= start <= end <= len(lines)):
                raise PolicyError('Invalid edit line range.')
            offset = sum(map(len, lines[:start - 1]))
            window = ''.join(lines[start - 1:end])
        positions, cursor = [], 0
        while True:
            found = window.find(old, cursor)
            if found < 0:
                break
            positions.append(offset + found)
            cursor = found + len(old)
        multiple = chunk.get('replace_all', args.get('replace_all', args.get('AllowMultiple', False)))
        if type(multiple) is not bool or not positions or (len(positions) > 1 and not multiple):
            raise PolicyError('Edit text is missing or ambiguous; provide exact context.')
        spans.extend((pos, pos + len(old), new) for pos in positions)
    spans.sort()
    if any(right[0] < left[1] for left, right in zip(spans, spans[1:])):
        raise PolicyError('Overlapping edit chunks.')
    after = before
    for start, end, new in reversed(spans):
        after = after[:start] + new + after[end:]
    return after


def file_edit(name, args, root):
    raw = next((args[key] for key in ('file_path', 'AbsolutePath', 'TargetFile', 'path')
                if key in args), None)
    path = resolve_path(raw, root)
    before = read_source(path)
    whole = name.lower() in {'write', 'write_to_file', 'filewrite'}
    if whole:
        after = args.get('content', args.get('CodeContent', args.get('contents')))
        if not isinstance(after, str):
            raise PolicyError('Missing full file content.')
    elif name.lower() in {'delete', 'delete_file'}:
        after = None
    else:
        if not path.is_file():
            raise PolicyError('Edit target does not exist.')
        after = replacements(before, args)
    return [(path, before, after, whole)]
