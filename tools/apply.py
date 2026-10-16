#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Apply to clean TRex v3.06 without Git; validate before and after mutation."""
import argparse
from pathlib import Path
import subprocess
import sys
from series import REPO, load, verify_tree

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('trex', type=Path, help='Clean TRex v3.06 source directory')
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--check', action='store_true', help='Validate and dry-run only')
    mode.add_argument('--verify', action='store_true', help='Verify the patched result only')
    args = parser.parse_args()
    data = load(); root = args.trex.resolve()
    if not (root / 'VERSION').is_file() or (root / 'VERSION').read_text().strip() != 'v3.06':
        raise ValueError('Expected TRex VERSION v3.06')
    verify_tree(root, data, 'result' if args.verify else 'base')
    if args.verify:
        print('PASS: all patched file hashes match the release manifest'); return
    # Each file belongs to one patch: independent dry-runs cover the entire series.
    for dry in (True, False):
        for entry in data['patches']:
            cmd = ['patch', '--batch', '--forward', '--fuzz=0', '-p1']
            if dry: cmd.append('--dry-run')
            with (REPO / 'patches' / entry['path']).open('rb') as stream:
                subprocess.run(cmd, cwd=root, stdin=stream, check=True)
        if dry and args.check:
            print('PASS: base hashes and all dry-runs; no files changed'); return
    verify_tree(root, data, 'result')
    print('PASS: applied and verified. Build TRex using docs/getting-started.md.')

if __name__ == '__main__':
    try: main()
    except (ValueError, OSError, subprocess.CalledProcessError) as exc:
        print(str(exc), file=sys.stderr)
        print('Stopped. Do not retry on a partially modified tree; use a clean copy.', file=sys.stderr)
        sys.exit(1)
