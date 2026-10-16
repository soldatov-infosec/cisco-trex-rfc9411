#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Check both application methods and rejection behavior against a clean base."""
import argparse
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from series import REPO, load, verify_tree

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', type=Path, required=True)
    args = parser.parse_args(); data = load(); verify_tree(args.base, data, 'base')
    with tempfile.TemporaryDirectory(prefix='trex-apply-') as tmp:
        for mode in ('helper', 'git'):
            root = Path(tmp) / mode; root.mkdir()
            shutil.copyfile(args.base / 'VERSION', root / 'VERSION')
            for e in data['files']:
                if e['base_sha256']:
                    dest = root / e['path']; dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(args.base / e['path'], dest)
            marker = root / 'unrelated-user-file'; marker.write_text('keep me\n')
            if mode == 'helper':
                command = [sys.executable, str(REPO / 'tools/apply.py'), str(root)]
                subprocess.run(command + ['--check'], check=True, stdout=subprocess.DEVNULL)
                verify_tree(root, data, 'base')
                subprocess.run(command, check=True, stdout=subprocess.DEVNULL)
                repeat = subprocess.run(command, capture_output=True)
                assert repeat.returncode != 0, 'repeat application unexpectedly accepted'
            else:
                subprocess.run(['git', 'init', '-q', str(root)], check=True)
                patches = [str(REPO / 'patches' / p['path']) for p in data['patches']]
                subprocess.run(['git', '-C', str(root), 'apply', '--check'] + patches, check=True)
                subprocess.run(['git', '-C', str(root), 'apply'] + patches, check=True)
            verify_tree(root, data, 'result')
            assert marker.read_text() == 'keep me\n'
            print('PASS:', mode, 'all result hashes; unrelated file preserved')
            if mode == 'helper': print('PASS: dry-run leaves base intact; repeat rejected without edits')

if __name__ == '__main__': main()
