# Testing

## Repository checks

```sh
python3 tools/check_repo.py
python3 -m unittest discover -s tests -v
```

These tests cover patch integrity, documentation links and apply-tool behavior.
They are not TLS protocol or physical-NIC tests. CI also applies the real series
to the pinned upstream release via both `patch` and `git apply` and verifies hashes.

## Engine and protocol tests

From the patched TRex tree, with AWS-LC installed:

```sh
export CXXFLAGS=-I/opt/trex-aws-lc-5.11.0/include
export LDFLAGS='-L/opt/trex-aws-lc-5.11.0/lib -Wl,-rpath,/opt/trex-aws-lc-5.11.0/lib'
sh tests/tls/run_engine_test.sh
sh tests/tls/run_http2_engine_tests.sh
python3 tests/tls/build_prefix_test.py
```

Use lib64 instead of lib if that is the install location. HTTP/2 tests require
python3-h2 and nghttp2 development files. ASan/UBSan requires a compatible compiler
and runtime. Keep leak detection enabled where the host supports it; the local
emulation evidence had to disable it and is recorded as such.

Build a simulator without requiring a NIC:

```sh
cd linux
./b configure --rfc9411 --aws-lc-prefix=/opt/trex-aws-lc-5.11.0
./b build --targets=bp-sim-64-debug -j4
cd ../scripts
# Generate a fresh SAN=localhost lab certificate and set absolute paths.
export TREX_TLS_TEST_CERT=/path/cert.pem
export TREX_TLS_TEST_KEY=/path/key.pem
./bp-sim-64-debug --ut --gtest_filter='gt_tcp.*:gt_astf_inter.*:astf_scheduler.*'
TREX_RX_PHASE_ALL=1 ./bp-sim-64-debug --ut --gtest_filter='gt_tcp.*:gt_astf_inter.*:astf_scheduler.*'
cd ..
sh tests/tls/run_profiles.sh
```

The simulator must run from `scripts` to find reference pcaps. Tests include TCP
reordering/overlap, resource faults, retry invariants, worker/context lifetime,
TLS resumption, HTTP validation, timestamps and bounded error drain.

Installed `doc/astf-tls-validation.md` documents record-fuzzer fixtures, supported
benchmarks and tooling limits. The smoke seeds do not substitute for a long
coverage-guided campaign or instrumentation inside AWS-LC itself.

## Physical NIC validation

Use the [getting-started suite](getting-started.md#4-smoke-test-then-load). Record
hardware, affinity, NUMA, NIC firmware/driver, negotiated TLS policy, actual flow
rate, payload/transaction count and any security inspection policy. Compare
identical profiles and sampling settings; include failures and completion tail.

Preserve natural completion. Do not hide overload by killing the run at the
requested duration. Inspect outstanding flows, protocol failures, retransmits,
port counters, mbuf exhaustion and successful response counts together.
Before sharing a capture, inspect it for host paths, command lines, process maps,
IP addresses and profile data. Private keys and raw perf.data are not required.
