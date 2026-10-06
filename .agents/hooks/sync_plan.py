"""Validate the central single-group sync schema and exercise its actual payload.

This deliberately supports only the plain paths and terminal repos block used by
sync.yml. Reject new YAML constructs until their distribution semantics are tested.
"""
import argparse
import json
import re
import shutil
import tempfile
from pathlib import Path, PurePosixPath


def safe_path(value):
    path = PurePosixPath(value)
    if path.is_absolute() or '..' in path.parts or not re.fullmatch(r'[\w./-]+', value):
        raise ValueError(f'Unsafe sync path: {value}')
    return value


def load_plan(root):
    text = (root / '.github/sync.yml').read_text(encoding='utf-8-sig')
    header, separator, block = text.partition('    repos: |\n')
    if not separator:
        raise ValueError('Expected one terminal repos block.')
    targets = []
    for line in block.splitlines():
        if not re.fullmatch(r'      [\w.-]+/[\w.-]+@[\w./-]+', line):
            raise ValueError(f'Invalid sync target: {line!r}')
        targets.append(line.strip())
    if not targets or len(set(targets)) != len(targets):
        raise ValueError('Sync targets must be nonempty and unique.')
    mappings = re.findall(r'^      - source: (\S+)\n        dest: (\S+)\n', header, re.M)
    remainder = re.sub(r'^      - source: \S+\n        dest: \S+\n', '', header, flags=re.M)
    if remainder != 'group:\n  - files:\n' or not mappings:
        raise ValueError('Unsupported sync schema; expected one group with source/dest pairs.')
    for source, dest in mappings:
        safe_path(source)
        safe_path(dest)
        if not (root / source).exists():
            raise ValueError(f'Missing sync source: {source}')
        if source.endswith('/') != dest.endswith('/'):
            raise ValueError('Directory mappings must preserve trailing slashes.')
    return header, targets, mappings


def export_payload(root, destination, mappings):
    """Copy mapped source files, excluding ignored runtime state from directories."""
    seen = set()
    for source, dest in mappings:
        origin = root / source
        files = sorted(origin.rglob('*')) if origin.is_dir() else [origin]
        for path in files:
            if '__pycache__' in path.parts or path.suffix == '.pyc':
                continue
            if path.is_symlink():
                raise ValueError(f'Sync source must not be a symlink: {path}')
            if not path.is_file():
                continue
            target = destination / dest
            if origin.is_dir():
                target /= path.relative_to(origin)
            if target in seen:
                raise ValueError(f'Overlapping sync destination: {target}')
            seen.add(target)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, target)
    return len(seen)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['matrix', 'render', 'check'])
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument('--target')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    header, targets, mappings = load_plan(args.root)
    if args.command == 'matrix':
        print(json.dumps({'include': [{'target': target, 'repository': target.split('/')[1].split('@')[0]}
                                      for target in targets]}, separators=(',', ':')))
    elif args.command == 'render':
        if args.target not in targets or args.output is None:
            parser.error('render requires a configured --target and --output')
        args.output.write_text(header + '    repos: |\n      ' + args.target + '\n', encoding='utf-8')
    else:
        from doctor import validate_configs
        with tempfile.TemporaryDirectory() as directory:
            count = export_payload(args.root, Path(directory), mappings)
            validate_configs(Path(directory))
        print(f'PASS: {len(targets)} targets; {count} payload files; downstream configuration valid.')


if __name__ == '__main__':
    main()
