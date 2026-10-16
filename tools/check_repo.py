#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Check patch inventory, local Markdown links and accidental secret artifacts."""
import re
from pathlib import Path
from series import REPO, load

def main():
    data = load()
    failures = []
    for path in REPO.rglob('*'):
        if '.git' in path.parts or '__pycache__' in path.parts: continue
        if not path.is_file(): continue
        if path.suffix in ('.key', '.pem', '.p12', '.pfx', '.pcap', '.pcapng') or path.name.startswith('.env'):
            failures.append('Unexpected sensitive/binary artifact: ' + str(path.relative_to(REPO)))
        if path.suffix != '.md': continue
        # Skip fenced code and remote links; validate real local Markdown targets.
        text = re.sub(r'```.*?```', '', path.read_text(), flags=re.S)
        for link in re.findall(r'\[[^\]]*\]\(([^)]+)\)', text):
            link = link.split('#', 1)[0]
            if not link or re.match(r'[a-z]+:', link): continue
            target = (path.parent / link).resolve()
            if REPO not in target.parents and target != REPO:
                failures.append('Link escapes repository: ' + link)
            elif not target.exists(): failures.append(str(path.relative_to(REPO)) + ': broken link ' + link)
    if failures: raise SystemExit('\n'.join(failures))
    print('PASS: {} patches, {} unique source paths, local links and artifact scan'.format(
        len(data['patches']), len(data['files'])))

if __name__ == '__main__': main()
