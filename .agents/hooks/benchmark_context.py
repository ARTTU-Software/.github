"""Measure instruction payload size; does not estimate paid/model tokens."""
import argparse
import subprocess
from pathlib import Path

ENTRYPOINTS = ['AGENTS.md', '.agents/skills/arttu-code-discovery/SKILL.md',
              '.agents/skills/arttu-cstyle/SKILL.md', '.agents/skills/arttu-docs-assistant/SKILL.md']


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument('--base', default='HEAD')
    args = parser.parse_args()
    old_total, new_total = 0, 0
    for relative in ENTRYPOINTS:
        previous = subprocess.run(['git', '-C', str(args.root), 'show', f'{args.base}:{relative}'],
                                  check=True, capture_output=True, timeout=10).stdout
        current = (args.root / relative).read_bytes()
        old_total += len(previous)
        new_total += len(current)
        print(f'{relative}: {len(previous)} -> {len(current)} bytes')
    reduction = 100 * (1 - new_total / old_total) if old_total else 0
    print(f'Combined entry points: {old_total} -> {new_total} bytes ({reduction:.1f}% smaller).')
    print('References load on demand. Actual token use/correctness requires a repeated task benchmark in each real client.')


if __name__ == '__main__':
    main()
