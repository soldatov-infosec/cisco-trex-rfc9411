# Profile and engine validation

All profile files contain their own implementation and can be copied alone.
API checks cover independent loading, policy/ALPN, CC defaults, body sizes,
parameter bounds and invalid combinations.

The recorded CLI run covered the original nine size/transport combinations: fifteen scenarios,
repeated with named groups and with full CC holds. Full CC uses ten exchanges
with a 30-second pause after each response. All 45 scenarios passed, with the
expected response counts, latency fields and natural connection completion.

HTTP/2 pacing tests keep scheduler time separate from RX timestamps and verify
that the final hold does not extend TTLB. Reload tests exercise load/clear/reload
without mutating command arrays. Named-group tests cover statistics allocation
before flow creation. These are local functional checks, not capacity measurements.

The protocol implementation passed 103 simulator regression tests, HTTP/2
ASan/UBSan tests and python-h2 interoperability checks. Leak detection was disabled
under emulation. A complete build and NIC qualification of the final release
artifact remain pending; see [validation scope](README.md).

Commands and results: [results.json](results.json). Profile usage:
[workloads](../profiles/rfc9411/README.md).

## Response-size matrix and mixed objects

The distribution includes 33 standalone profiles: CPS 1/2/4/16/64 KiB,
TP 1/16/64/256 KiB and mixed objects, and CC 1 KiB for each transport.
All use client addresses 16.0.0.1 through 16.0.255.199.
Seven profile serialization tests load all 33 files and check independent loading,
body sizes, addresses and TLS options. Five HTTP/2 API tests check validation
including list bounds and caller-list isolation. These passed on Python 3.9/macOS;
the unused live RPC client import was stubbed because bundled Linux ZMQ does not
load on macOS arm64. Real ASTF profile construction and serialization were used.

The HTTP/2 C++ regression suite passed with ASan/UBSan and nghttp2 1.68.0 built
locally. Mixed-object cases cover sequential and concurrent streams (1/4/10),
fragmentation, cyclic size-list reuse and rejection of a validly framed response
whose length differs from the configured mix. Existing pacing, GOAWAY, timestamp
and fixed-body tests also passed. This run did not instrument nghttp2 itself.

Full TRex compilation, loader integration and NIC validation of mixed HTTP/2
remain pending. The recorded simulator results above do not qualify every new
size or the mixed-object engine extension.
