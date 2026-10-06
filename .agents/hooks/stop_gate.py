"""One checkpoint per source tree, with bounded repair continuations."""
import argparse
import hashlib
import json
import sys
from pathlib import Path
from hook_io import emit, normalize
from verify_changes import git, tree_identity, verify_policy, verify_tests


def failure_file(root, payload):
    session = payload.get('conversationId', payload.get('session_id', payload.get('conversation_id', 'local')))
    return root / '.agents/state' / ('stop-' + hashlib.sha256(str(session).encode()).hexdigest()[:24] + '.json')


def repeated_failure(root, payload, reason):
    target = failure_file(root, payload)
    fingerprint = hashlib.sha256((tree_identity(root) + reason).encode()).hexdigest()
    repeated = False
    if target.exists():
        repeated = target.read_text(encoding='utf-8') == fingerprint
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix('.tmp')
    temporary.write_text(fingerprint, encoding='utf-8')
    temporary.replace(target)
    return repeated


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--vendor', choices=['antigravity', 'claude', 'codex', 'cursor'], required=True)
    parser.add_argument('--allow-protected', action='append', default=[])
    options = parser.parse_args()
    try:
        payload = json.load(sys.stdin)
        _, _, _, cwd = normalize(payload, options.vendor)
        root = Path(git(cwd, 'rev-parse', '--show-toplevel').stdout.decode().strip())
        if any(not Path(path).is_absolute() for path in options.allow_protected):
            raise ValueError('Protected-file hook exceptions need exact absolute paths.')
        approved = {str(Path(path).resolve()) for path in options.allow_protected}
        plans = verify_policy(root, allow_protected=approved)
        if plans:
            verify_tests(root)
        failure_file(root, payload).unlink(missing_ok=True)
    except Exception as error:
        reason = f'ARTTU verification: {error}. Fix this or report verification as blocked.'
        repeated = (payload.get('stop_hook_active') or payload.get('loop_count', 0) >= 1) if isinstance(locals().get('payload'), dict) else False
        if 'root' in locals() and isinstance(payload, dict):
            try:
                repeated = repeated_failure(root, payload, reason) or repeated
            except Exception:
                pass  # The first failure reason remains available to the client.
        if repeated:
            # Do not spend an unbounded number of model turns on the same gate.
            out = {} if options.vendor == 'cursor' else {'systemMessage': reason}
            if options.vendor == 'antigravity':
                out = {'decision': 'allow', 'reason': reason}
            print(json.dumps(out))
            print(reason, file=sys.stderr)
            return 0
        return emit(options.vendor, False, reason, stop=True)
    return emit(options.vendor, True, stop=True)


if __name__ == '__main__':
    sys.exit(main())
