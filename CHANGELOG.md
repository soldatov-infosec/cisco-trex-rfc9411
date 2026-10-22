# Changelog

## 1.1.0

- Add opt-in HTTP/1.1 request and response message receives over TCP and TLS.
- Parse fixed-length, chunked and close-delimited framing without relying on header byte counts.
- Validate request framing, expected response status and optional exact body length.
- Add bounded receive deadlines, timeout diagnostics and lifecycle regression tests.
- Migrate standalone HTTPS workloads to message receives, preserving CC pauses.

See [release notes](docs/release-1.1.0.md) for compatibility and validation limits.

## 1.0.1

- Process TCP input and submit transport ACKs before deferred TLS work in each RX burst.
- Bound both worker-local queues to 64 entries; cancel queued pointers before flow destruction and process immediately on capacity exhaustion.
- Preserve synchronous TLS consumption for small receive windows and zero-window reopening.
- Keep receive timestamp propagation and HTTP/UDP measurement definitions unchanged.
- Avoid unsolicited repeated FIN when acknowledging input after a TLS close; preserve loss-driven FIN retransmission.
- Add queue-lifetime, delayed empty-ACK, closure-gap and FIN-loss regression coverage.

Built directly from 1.0.0 plus the NIC-tested RX-phase change. See
[release notes](docs/release-1.0.1.md) and [queue review](validation/rx-queue-review.md).

## 1.0.0

First public release of the Cisco TRex RFC 9411 extension.

- Native AWS-LC TLS 1.2/1.3 with certificate verification, mTLS and session resumption.
- HTTP/1.1 validation and native HTTP/2 over TCP or TLS.
- Connection and request latency statistics, plus UDP transaction RTT.
- Timer-driven HTTP/2 CC workloads and nine standalone CPS/TP/CC profiles.
- Nine subsystem patches for TRex v3.06, application tools, tests and documentation.

See [validation](validation/README.md) for evidence and its limits.
