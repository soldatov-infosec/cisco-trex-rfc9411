# HTTP/1.1 message receive validation — 1.1.0

Local validation dated 2026-10-22. Linux simulator and software-port tests used
an amd64 container on a macOS host. These are functional tests, not NIC capacity
measurements or tests of a real NGFW inspection implementation.

## Coverage

- All 11 Python API tests passed in the Linux TRex environment.
- Both consolidated application methods reproduced all 154 expected source hashes;
  the 20-path upgrade applied with zero fuzz and matched its result hashes.

- 115 simulator regression tests passed with normal RX processing, and again
  with `TREX_RX_PHASE_ALL=1`. The benchmark test is inert unless explicitly enabled.
- Message tests include plain TCP, TLS 1.2/1.3, fixed and chunked framing,
  informational responses, EOF, truncation, status/content rejection, early
  input, fragmentation/retransmission and a 700-second simulated CC pause.
- Reassembly allocation failure tests cover six failure sites on three transports;
  teardown checks empty timer wheels and advances timers after program destruction.
- Profile loader tests repeat teardown/reload 20 times using the same profile ID.
- All 55 standalone workload configurations passed the release simulator,
  including default CC pauses, HTTP/2 and HTTPS/2 regression profiles.
- Live DPDK software-port RPC checks passed on isolated veth interfaces with
  external networking disabled: two stop/remove iterations in each receive
  direction on TCP/TLS 1.2/TLS 1.3, while an unrelated owned profile remains active.
  Fixed/chunked success, rejected body content and receive timeout counters also
  passed through the stats API on all three transports.
- Standalone parser tests run with AddressSanitizer and UndefinedBehaviorSanitizer;
  this is not a sanitizer run of the complete DPDK process.

The initial profile smoke invocation selected an old debug simulator and failed
to recognize the server parser configuration. The successful complete run used
the freshly rebuilt release binary with the tool's explicit `--release` option.

## CPU and memory scope

An opt-in simulator benchmark compares legacy byte receives with message receives
within the same engine, using ten 16-KiB responses per flow. Five paired repeats
of 64 flows gave a median message/legacy thread-CPU ratio of 1.035 for TCP and
1.034 for TLS 1.3. Ranges were 0.748–1.152 and 0.970–1.062 respectively; this
variance, emulation and concurrent build activity prevent a reliable NIC cost
prediction. Setup/context creation and teardown are outside the timed region.
ACK counts were identical within every pair. The raw summary is in
[message-cost-summary.json](message-cost-summary.json).

The new server parser reserves `max_header_bytes + 1` bytes per flow, 16,385 by
default, plus metadata and allocator overhead. It retains no complete message
body. This is allocated capacity, not measured resident memory. Use the API's
header limit and size concurrency for available memory.

## Reproduction

Build the simulator using the normal extension build procedure, then run:

```sh
python3 tools/test_profile_smoke.py --release --cc-defaults --trex /path/to/trex --output /new/log/directory
```

`tests/tls/http_message_test.cpp` and `http_test.cpp` compile with a C++11 compiler
and `-I src`; add `-fsanitize=address,undefined` for the standalone sanitizer run.
Run `tests/tls/api_test.py` with the interactive Python API on `PYTHONPATH`.
The simulator regression filter is `gt_tcp.*:gt_astf_inter.*:astf_scheduler.*`;
TLS test certificate/key environment variables are required for TLS cases.

The live helper requires a dedicated Linux network namespace/container with
NET_ADMIN, NET_RAW, iproute2 and the Python client dependencies. Set
`TREX_TLS_TEST_BINARY=./_t-rex-64` and
`TREX_TLS_LIVE_CLIENT=../tests/tls/http_message_live.py`, then run
`sh tests/tls/run_interactive_veth.sh --iterations 2`. It creates and removes
only its own test interfaces and server process. Keep generated test keys local.

The full binary was compiled with the Mellanox PMD disabled in the local test
container. Local compiler accommodations for upstream warnings were excluded
from the distributed patch. Production NIC drivers, real inspection changes,
high-concurrency memory use and sustained CPS require physical-host validation.

## Profile defaults refresh (same release)

All 55 workload scenarios were repeated successfully after selecting AES-128-GCM
by default, TLS 1.2 P-256 and explicit IPv4 MSS/initial congestion window. Eight
profile API tests passed, including every TLS workload's default and override
policies. No production C++ source or library change was needed.
