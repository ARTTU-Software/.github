"""Small evidence cards, invalidated by Git identity, source hashes and graph generation."""
import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

MAX_BYTES = 8192
FIELDS = {'scope', 'facts', 'relationships', 'unknowns', 'checks', 'coverage'}


def head(root):
    result = subprocess.run(['git', '-C', str(root), 'rev-parse', 'HEAD'],
                            check=True, capture_output=True, text=True, timeout=10)
    return result.stdout.strip()


def source_hashes(root, files):
    root = root.resolve()
    hashes = {}
    for name in files:
        path = (root / name).resolve()
        relative = path.relative_to(root).as_posix()
        hashes[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
    return hashes


def save(root, name, body, files, generation=None):
    if not re.fullmatch(r'[a-z0-9][a-z0-9_-]{0,63}', name):
        raise ValueError('Use a short lowercase evidence-card name.')
    if not isinstance(body, dict) or set(body) - FIELDS or not body.get('scope'):
        raise ValueError('Card needs scope; permitted fields: facts, relationships, unknowns, checks, coverage.')
    if not files:
        raise ValueError('Evidence cards must name their source files.')
    encoded = json.dumps(body, ensure_ascii=False)
    if len(encoded.encode('utf-8')) > MAX_BYTES:
        raise ValueError('Evidence card exceeds 8 KiB; keep only task-relevant facts.')
    card = {'version': 1, 'head': head(root), 'files': source_hashes(root, files),
            'generation': generation, 'evidence': body}
    directory = root / '.agents/state/context'
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / f'{name}.json'
    temporary = target.with_suffix('.tmp')
    temporary.write_text(json.dumps(card, ensure_ascii=False), encoding='utf-8')
    temporary.replace(target)


def load(root, name, generation=None):
    if not re.fullmatch(r'[a-z0-9][a-z0-9_-]{0,63}', name):
        raise ValueError('Invalid evidence-card name.')
    target = root / '.agents/state/context' / f'{name}.json'
    if not target.is_file():
        return None, 'miss'
    card = json.loads(target.read_text(encoding='utf-8'))
    if card.get('version') != 1 or card.get('head') != head(root):
        return None, 'stale Git identity'
    if card.get('generation') and card['generation'] != generation:
        return None, 'stale or unspecified graph generation'
    try:
        if source_hashes(root, card['files']) != card['files']:
            return None, 'stale source'
    except (OSError, ValueError):
        return None, 'missing or relocated source'
    body = card['evidence']
    if len(json.dumps(body).encode()) > MAX_BYTES:
        raise ValueError('Oversized evidence card.')
    return body, 'hit'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['save', 'show'])
    parser.add_argument('name')
    parser.add_argument('--root', type=Path, default=Path.cwd())
    parser.add_argument('--generation')
    parser.add_argument('--files', nargs='+', default=[])
    args = parser.parse_args()
    try:
        root = args.root.resolve()
        if args.action == 'save':
            save(root, args.name, json.load(sys.stdin), args.files, args.generation)
            print('Evidence card saved; reuse only within its recorded scope.')
        else:
            body, status = load(root, args.name, args.generation)
            print(json.dumps({'status': status, 'evidence': body}, ensure_ascii=False))
    except Exception as error:
        print(f'Context cache: {error}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
