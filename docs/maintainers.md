# Maintainer workflow

This repository distributes an extension, not a TRex fork. The authoritative release
is the patch series plus its manifest. Keep source development in a separate TRex
checkout; never include generated binaries, certificates, keys or captures here.

## Reproduce a release

1. Obtain the exact upstream tag and archive digest from `patches/manifest.json`.
2. Keep one pristine copy and apply the series to a second copy using `tools/apply.py`.
3. Develop and test in that second tree. Keep each file assigned to one subsystem
   patch; do not accumulate fix-on-fix patches.
4. Run `python3 tools/regenerate.py --base CLEAN --modified DEV` for existing paths.
   For new paths, use `--add PATCH:PATH`, with a patch filename from `patches/series`.
5. Review the generated diff, update release notes and documentation, and run:

```sh
python3 tools/check_repo.py
python3 -m unittest discover -s tests -v
python3 tools/test_application.py --base CLEAN
```

Run the engine, simulator and physical-NIC checks appropriate to the change as
explained in [testing](testing.md). Record what was actually run and its limitations.
The manifest is an integrity and reproducibility record, not a digital signature.
Regeneration currently supports UTF-8 text additions and modifications; removals,
renames and binary files require an explicit tooling change and review.

## Publish to GitHub

Create an empty GitHub repository named `cisco-trex-rfc9411`. The prepared local
repository has no remote and does not publish anything automatically. Review the
license notices and all content before publishing. Configure your own Git author
identity, then run from this repository:

```sh
git add .
git commit -m "Publish consolidated TRex RFC 9411 extension"
git remote add origin git@github.com:YOUR_ACCOUNT/cisco-trex-rfc9411.git
git push -u origin main
```

Enable private vulnerability reporting before advertising it as available. Configure
branch protection and required CI checks after their first successful hosted run.
Add maintainer contacts and ownership rules when the maintainer team is known;
this repository deliberately does not invent an organization, email or affiliation.
Suggested topics: `trex`, `dpdk`, `tls`, `http2`, `network-testing`, `rfc9411`.

For releases, publish the source archive, checksum, upstream revision, dependency
versions and validation scope. Do not describe a tested load point as a maximum,
or successful engine tests as certification of a complete RFC 9411 experiment.
