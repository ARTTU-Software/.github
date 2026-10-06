"""Portable bounded source fallback when a graph/snippet server is unavailable."""
import argparse
import sys
from pathlib import Path
from hook_io import check_read
from policy import PolicyError, READ_WHOLE_LIMIT


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('path', type=Path)
    parser.add_argument('--start', type=int)
    parser.add_argument('--end', type=int)
    args = parser.parse_args()
    try:
        inputs = {'file_path': str(args.path.resolve())}
        if args.start is not None or args.end is not None:
            inputs.update(StartLine=args.start, EndLine=args.end)
        check_read(inputs, Path.cwd())
        start, end = args.start or 1, args.end or READ_WHOLE_LIMIT
        with args.path.open(encoding='utf-8-sig', errors='replace') as source:
            for line, text in enumerate(source, 1):
                if line > end:
                    break
                if line >= start:
                    sys.stdout.write(f'{line}: {text}')
    except (PolicyError, OSError) as error:
        print(error, file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
