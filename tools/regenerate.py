#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Regenerate existing manifest paths from a clean base and a development tree."""
import argparse
import difflib
import json
from pathlib import Path
from series import REPO, digest, load, verify_tree, relative

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--base', type=Path, required=True)
    p.add_argument('--modified', type=Path, required=True)
    p.add_argument('--add', action='append', default=[], metavar='PATCH:PATH',
                   help='Explicitly assign a new text path to an existing patch')
    a = p.parse_args()
    a.base = a.base.resolve(); a.modified = a.modified.resolve()
    data = load(); verify_tree(a.base, data, 'base')
    for assignment in a.add:
        patch, name = assignment.split(':', 1)
        relative(name)
        if any(c.isspace() for c in name): raise ValueError('Whitespace in path')
        if patch not in [e['path'] for e in data['patches']]: raise ValueError('Unknown patch')
        if name in [e['path'] for e in data['files']]: raise ValueError('Path already assigned')
        original = a.base / name
        if any(p.is_symlink() for p in [original, *original.parents]):
            raise ValueError('Symlink base path')
        data['files'].append({'path': name, 'patch': patch,
            'base_sha256': digest(original.read_bytes()) if original.exists() else None,
            'result_sha256': None, 'origin': 'maintainer-addition'})
    # Build every output in memory before writing; never sweep a working directory.
    outputs = {}
    for patch in data['patches']:
        text = ''
        for entry in [e for e in data['files'] if e['patch'] == patch['path']]:
            f = entry['path']; original = a.base / f; modified = a.modified / f
            before = original.read_bytes() if original.exists() else None
            if any(p.is_symlink() for p in [modified, *modified.parents]):
                raise ValueError('Symlink result: ' + f)
            after = modified.read_bytes()
            if before == after: raise ValueError('Unchanged manifest path: ' + f)
            entry['result_sha256'] = digest(after)
            text += 'diff --git a/' + f + ' b/' + f + '\n'
            if before is None: text += 'new file mode 100644\n'
            diff = difflib.unified_diff((before or b'').decode().splitlines(True), after.decode().splitlines(True),
                    fromfile='a/' + f if before is not None else '/dev/null', tofile='b/' + f)
            for line in diff:
                text += line if line.endswith('\n') else line + '\n\\ No newline at end of file\n'
        outputs[patch['path']] = text
        patch['sha256'] = digest(text.encode())
    for name, text in outputs.items(): (REPO / 'patches' / name).write_text(text)
    (REPO / 'patches/manifest.json').write_text(json.dumps(data, indent=2) + '\n')
    print('Regenerated series. Run tools/check_repo.py and test both application methods.')

if __name__ == '__main__': main()
