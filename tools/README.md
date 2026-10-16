# Repository tools

All tools use Python 3's standard library. Applying also requires `patch`;
verification through Git is an independent alternative.

- `apply.py TREX --check`: check base hashes and dry-run every patch, without edits.
- `apply.py TREX`: preflight, apply, verify resulting hashes.
- `apply.py TREX --verify`: verify an already patched tree.
- `check_repo.py`: manifest/patch consistency and local documentation links.
- `regenerate.py --base CLEAN --modified DEV`: rebuild existing patch assignments
  from a development tree, preserving exact bytes and missing-final-newline markers.
  Use `--add PATCH:PATH` to explicitly include a new path.

The apply helper rejects symlinks in touched paths. It does not back up, delete,
reset, download, install dependencies, or launch traffic. Preflight failures leave
the tree untouched; an interruption during writes requires a fresh base.
Regeneration is a maintainer operation: review the diff and rerun application
checks before committing. Never point it at diagnostic captures or build outputs.

`test_profile_smoke.py --trex TREX --output NEW_DIR` runs the 33 workload
profiles through a built ASTF simulator (55 cases across TLS versions).
See [test prerequisites](../tests/README.md#ready-to-load-profiles).
