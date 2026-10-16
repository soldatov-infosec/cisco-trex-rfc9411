# Repository tooling tests

Run `python3 -m unittest discover -s tests -v` from this repository.
These tests exercise dry-run, application, idempotence rejection, modified input,
new-file collisions, symlink parents and patch checksum tampering.

For the real series, run `python3 tools/test_application.py --base /path/to/clean/trex`.
This uses temporary trees to compare helper/patch and Git application against
all result hashes. It leaves the supplied clean base unchanged.

Engine tests live in patch 0007 and install into TRex's `tests/tls` and simulator
sources. See [testing](../docs/testing.md) for those commands and prerequisites.

## Ready-to-load profiles

With a patched source tree and TRex-compatible Python 3.10/3.11:

```sh
TREX_ROOT=/path/to/patched/trex python3 -m unittest discover -s tests -p test_profiles.py -v
```

This loads all 33 workload entry points through the real ASTF loader, checks
TLS policy/ALPN, HTTP request counts, CC delays, exact body length and rejected
unsupported tunables. Without `TREX_ROOT`, these tests are explicitly skipped.
The placeholder certificate files are only for serialization; no cryptography
is tested by this unit suite. Run the profiles against the engine separately.

For an end-to-end smoke run after building `bp-sim-64-debug` with TLS:

```sh
python3 tools/test_profile_smoke.py --trex /path/to/patched/trex --output /tmp/profile-smoke
```

It executes 55 cases (both TLS versions plus cleartext H2), checks successful
response/handshake counts and published connection-latency fields, and saves text logs. CC uses
three requests with 10 ms holds to keep this a functional smoke test. It does not
measure capacity or the long-duration CC population. Certificates and PCAPs are
temporary and are deleted at completion; OpenSSL CLI is required for lab fixtures.


Add `--named-groups` to repeat the smoke suite with a named template group; this
regresses the simulator's client-statistics allocation. HTTP/2 CLI simulation
also loads, clears and reloads the profile, exercising non-mutating command reads.
Each standalone file is tested after copying it away from the profile directory.

Add `--cc-defaults` to use ten exchanges and 30-second holds (300 seconds
of virtual hold time per CC flow). This still tests one connection per scenario,
not the large population needed for a physical-NIC CC benchmark.
