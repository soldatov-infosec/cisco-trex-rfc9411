#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Shared manifest validation; no third-party Python dependencies."""
import hashlib
import json
from pathlib import Path, PurePosixPath

REPO = Path(__file__).resolve().parents[1]

def digest(data):
    return hashlib.sha256(data).hexdigest()

def relative(value):
    p = PurePosixPath(value)
    if not value or p.is_absolute() or '..' in p.parts or '\\' in value or str(p) != value:
        raise ValueError('Unsafe manifest path: ' + value)
    return p

def load():
    data = json.loads((REPO / 'patches/manifest.json').read_text())
    if data['schema'] != 1:
        raise ValueError('Unsupported manifest schema')
    names = (REPO / 'patches/series').read_text().splitlines()
    if names != [p['path'] for p in data['patches']] or len(set(names)) != len(names):
        raise ValueError('series and manifest disagree')
    seen = set()
    for entry in data['files']:
        relative(entry['path'])
        if entry['path'] in seen or entry['patch'] not in names:
            raise ValueError('Duplicate path or unknown patch: ' + entry['path'])
        seen.add(entry['path'])
    for entry in data['patches']:
        relative(entry['path'])
        if '/' in entry['path']:
            raise ValueError('Patch must be in patches/')
        p = REPO / 'patches' / entry['path']
        if p.is_symlink() or digest(p.read_bytes()) != entry['sha256']:
            raise ValueError('Patch checksum mismatch: ' + str(p))
        actual = []
        for line in p.read_text().splitlines():
            if line.startswith('diff --git '):
                _, _, a, b = line.split()
                if a[2:] != b[2:] or not a.startswith('a/') or not b.startswith('b/'):
                    raise ValueError('Unsupported diff header')
                relative(a[2:]); actual.append(a[2:])
        expected = [e['path'] for e in data['files'] if e['patch'] == entry['path']]
        if actual != expected:
            raise ValueError('Patch paths differ from manifest: ' + str(p))
    return data

def verify_tree(root, data, state):
    root = root.resolve()
    errors = []
    for entry in data['files']:
        p = root / entry['path']
        # Do not follow pre-existing symlinks into unrelated directories.
        current = root
        for part in relative(entry['path']).parts:
            current = current / part
            if current.is_symlink():
                errors.append(entry['path'] + ': symlink in target path'); break
        else:
            expected = entry[state + '_sha256']
            if expected is None:
                if p.exists(): errors.append(entry['path'] + ': must not exist')
            elif not p.is_file() or digest(p.read_bytes()) != expected:
                errors.append(entry['path'] + ': unexpected content')
    if errors:
        raise ValueError('\n'.join(errors))
