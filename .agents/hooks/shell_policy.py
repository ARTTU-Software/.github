"""Catch common shell bypasses; independent diff validation remains mandatory."""
import re
import shlex
from hook_io import check_read
from policy import PolicyError

MUTATOR = re.compile(r'(^|[;|&\n]\s*|\b(?:sudo|command)\s+)(?:\s*)(?:set-content|add-content|out-file|tee|remove-item|move-item|copy-item|rm|mv|cp)\b', re.I)
INLINE = re.compile(r'\b(?:python\d*|py|node|ruby|perl|bash|sh|cmd|powershell|pwsh)(?:\.exe)?\s+(?:[^;\n]*?\s)?-(?:c|e|command|encodedcommand|enc)\b|\b(?:invoke-expression|iex)\b|<<', re.I)


def check_shell(args, root):
    command = args.get('command', args.get('cmd', args.get('CommandLine')))
    if not isinstance(command, str) or not command.strip():
        raise PolicyError('Missing shell command.')
    if (MUTATOR.search(command) or INLINE.search(command)
            or re.search(r'\bsed\b[^\n]*\s-i\b|\bgit\s+(?:restore|reset|checkout)\b', command, re.I)
            or re.search(r'>\s*["\']?[^\s|;&]+\.(?:c|h|cpp|hpp|ld|s)\b', command, re.I)):
        raise PolicyError('Use a checked edit/apply_patch tool for file mutations; avoid opaque inline shell code.')
    # Fast path for ordinary build, tests, Git queries, and graph tooling.
    if not re.match(r'^\s*(?:cat|tac|type|Get-Content|gc)\b', command, re.I):
        return
    bounded = re.search(r'(?:\bhead\s+(?:-n\s+|-)(\d+)|(?<!\w)-(?:TotalCount|Head|First)\s+(\d+))', command, re.I)
    if bounded and 0 < int(next(value for value in bounded.groups() if value)) <= 100:
        return
    tokens = shlex.split(command, posix=False)
    candidates = [token.strip('"\'') for token in tokens[1:]
                  if not token.startswith('-') and token not in {'|', ';'}]
    if not candidates or any('*' in value or '?' in value for value in candidates):
        raise PolicyError('Use the bounded read helper or graph snippets.')
    for value in candidates:
        path = root / value
        if path.is_file():
            check_read({'file_path': str(path)}, root)
