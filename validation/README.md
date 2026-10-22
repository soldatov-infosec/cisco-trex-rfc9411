# Validation

Current release: see the [1.1.0 HTTP message validation](http-message-1.1.0.md).
The [1.0.1 queue review](rx-queue-review.md) and [results](results.json) are
historical evidence. The table below records inherited 1.0.0 validation, not
newly repeated checks.


Validation is split by scope. A passing simulator test is not a physical-NIC
capacity result, and these checks do not certify an RFC 9411 experiment.

| Scope | Evidence |
|---|---|
| Protocol implementation | 103/103 TCP/ASTF/scheduler simulator tests |
| Profile scenarios | 45/45 runs: standard, named-group and full CC holds |
| HTTP/2 engine | Pacing, timestamp, flow-control, framing and GOAWAY tests; python-h2 interoperability |
| Memory instrumentation | HTTP/2 ASan/UBSan; leak detection disabled under emulation |
| Profile API | 7/7 standalone-profile tests and 4/4 HTTP/2 API tests |
| Build configuration | 3/3 dependency-prefix and public-option tests |
| Repository tooling | 6/6 tests; patch and Git application with exact result hashes |

The protocol test evidence covers the implementation. The final public metric
identifiers and configure option were checked through focused tests; a complete
compiler/linker build and physical-NIC qualification of the final release artifact
remain pending. A long coverage-guided fuzz campaign is not claimed. Hosted
GitHub Actions has not yet run for this repository.

See [profile validation](profiles.md), [1.0.0 machine-readable evidence](results-1.0.0.json)
and [repeatable commands](../docs/testing.md). No headline throughput or maximum
CPS claim is made. Collect fresh results with your hardware, NUMA placement,
profiles and DUT configuration before drawing performance conclusions.
