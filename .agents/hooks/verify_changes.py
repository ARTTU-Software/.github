"""Independent working-tree policy check, usable from hooks and required CI."""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from policy import BINARY_SUFFIXES, PolicyError, SOURCE_SUFFIXES, protected, validate_change


def git(root, *args, check=True, input=None):
    return subprocess.run(['git', '-C', str(root), *args], capture_output=True,
                          check=check, timeout=30, input=input)


def changed_plans(root, base='HEAD'):
    if base == 'EMPTY':
        base = git(root, 'hash-object', '-t', 'tree', '--stdin', input=b'').stdout.decode().strip()
    else:
        git(root, 'rev-parse', '--verify', f'{base}^{{commit}}')
    names = git(root, 'diff', '--name-only', '--no-renames', '-z', base, '--').stdout
    names += git(root, 'ls-files', '--others', '--exclude-standard', '-z').stdout
    plans = []
    for raw in sorted(set(names.split(b'\0')) - {b''}):
        relative = raw.decode('utf-8')
        path = root / relative
        if path.suffix.lower() in BINARY_SUFFIXES and path.exists():
            raise PolicyError(f'Compiled artifact is not ignored: {relative}.')
        if path.suffix.lower() not in SOURCE_SUFFIXES and not protected(path):
            continue
        if path.is_symlink():
            raise PolicyError(f'Source symlink needs manual review: {relative}.')
        previous = git(root, 'show', f'{base}:{relative}', check=False)
        before = previous.stdout.decode('utf-8-sig').replace('\r\n', '\n') if previous.returncode == 0 else ''
        after = path.read_text(encoding='utf-8-sig') if path.exists() else None
        plans.append((path, before, after))
    return plans


def verify_policy(root, base='HEAD', allow_protected=()):
    plans = changed_plans(root, base)
    for path, before, after in plans:
        validate_change(path, before, after, allow_protected=allow_protected)
    return plans


def tree_identity(root):
    digest, seen = hashlib.sha256(), set()

    def include_repository(repository):
        repository = repository.resolve()
        if repository in seen:
            return
        seen.add(repository)
        digest.update(str(repository).encode() + b'\0')
        digest.update(git(repository, 'rev-parse', 'HEAD').stdout)
        names = git(repository, 'ls-files', '--cached', '--others', '--exclude-standard', '-z').stdout
        for raw in sorted(set(names.split(b'\0')) - {b''}):
            relative = Path(raw.decode('utf-8'))
            if relative.parts[:2] == ('.agents', 'state') or '__pycache__' in relative.parts:
                continue
            path = repository / relative
            digest.update(raw + b'\0')
            if path.is_symlink():
                raise PolicyError('Verification cache cannot fingerprint source/dependency symlinks; verify manually.')
            if path.is_dir() and (path / '.git').exists():
                include_repository(path)  # Include committed and dirty submodule inputs.
            elif path.is_file():
                content = hashlib.sha256()
                with path.open('rb') as source:
                    for chunk in iter(lambda: source.read(65536), b''):
                        content.update(chunk)
                digest.update(content.digest())
            else:
                digest.update(b'<absent-or-uninitialized>')

    include_repository(root)
    for name, value in sorted(os.environ.items()):
        if name in {'PATH', 'CC', 'CXX', 'CFLAGS', 'CPPFLAGS', 'LDFLAGS', 'GEM_HOME', 'GEM_PATH'} or name.startswith(('CEEDLING_', 'BUNDLE_')):
            digest.update(name.encode() + b'\0' + value.encode() + b'\0')
    return digest.hexdigest()


def verify_tests(root):
    state = root / '.agents/state/verification.json'
    identity = tree_identity(root)
    if state.is_file():
        try:
            if json.loads(state.read_text()) == {'identity': identity, 'command': 'ceedling test:all'}:
                return 'Ceedling result reused for the unchanged source/configuration tree.'
        except (ValueError, OSError):
            pass
    if not (root / 'project.yml').is_file():
        raise PolicyError('C changed but project.yml is absent; configure required verification for this repository.')
    if (root / 'Gemfile').is_file() and shutil.which('bundle'):
        command = ['bundle', 'exec', 'ceedling', 'test:all']
    else:
        executable = shutil.which('ceedling')
        if not executable:
            raise PolicyError('Ceedling is unavailable; install the repository test dependencies.')
        command = [executable, 'test:all']
    state.parent.mkdir(parents=True, exist_ok=True)
    log = state.parent / 'ceedling.log'
    lock = state.parent / 'verification.lock'
    try:
        descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as error:
        raise PolicyError('Verification already running (or stale verification.lock); inspect it before retrying.') from error
    os.close(descriptor)
    try:
        with log.open('w', encoding='utf-8') as stream:
            result = subprocess.run(command, cwd=root, stdout=stream, stderr=subprocess.STDOUT,
                                    timeout=240, shell=sys.platform == 'win32')
        if result.returncode:
            raise PolicyError('Ceedling failed; inspect .agents/state/ceedling.log with a bounded read.')
        if tree_identity(root) != identity:
            raise PolicyError('Source changed during verification; rerun tests.')
        temporary = state.with_suffix('.tmp')
        temporary.write_text(json.dumps({'identity': identity, 'command': 'ceedling test:all'}))
        temporary.replace(state)
    finally:
        lock.unlink()
    return 'Ceedling test:all passed.'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, default=Path.cwd())
    parser.add_argument('--base', default='HEAD')
    parser.add_argument('--tests', action='store_true')
    parser.add_argument('--allow-protected', action='append', default=[], help='Exact path approved by the reviewer; CI should not set this automatically.')
    args = parser.parse_args()
    root = args.root.resolve()
    try:
        approved = {str((root / name).resolve()) for name in args.allow_protected}
        plans = verify_policy(root, args.base, approved)
        if args.tests and plans:
            print(verify_tests(root))
        print(f'Policy checked {len(plans)} changed source/system files against {args.base}.')
    except Exception as error:
        print(f'ARTTU: {error}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
