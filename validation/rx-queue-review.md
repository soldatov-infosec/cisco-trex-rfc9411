# RX queue and flow-lifetime review — 1.0.1

## Scope and outcome

Reviewed the 11 source paths in the NIC-tested RX-phase patch against extension
1.0.0, including the surrounding destruction, timer, TCP output and DPC paths.
No blocking defect was identified in this review. This is a scoped engineering
review with regression evidence, not a proof that all bugs have been excluded.
The subsequent [TLS FIN fix](tls-fin-review.md) changes TCP closure output;
the RX queue implementation itself remains the NIC-tested version.

| Area | Checked invariant and result |
|---|---|
| Ownership | ACK/TLS queues hold non-owning TCP pointers on the owning worker; mbuf ownership remains in the existing TLS RX FIFO. No cross-thread transfer. |
| Bounds | Both queues have 64 slots. Repeated enqueue is idempotent. Full queues return false to continue immediate service; cancelled slots are not reused until drain, preserving bounded indexing. |
| Destruction | `free_flow` cancels both slots before TCP/application destruction. Normal close, RST and profile-wide termination converge on this cleanup. |
| Callback lifetime | Drain clears the queue cell and flow slot before invoking TLS work. Deferred callbacks execute before final closed-flow release; drain never accesses the pointer afterwards. |
| Timers | Queue lifetime is one synchronous RX burst. Timer handling does not interrupt the worker's burst. TLS teardown stops work/close timers; scheduling remains bounded by the existing work budget. |
| TCP output | ACKs are drained and TX submitted before deferred crypto. Production `on_flush_tx` flushes output; it does not recursively service RX. FIN/RST and window reopening do not qualify for ordinary-data ACK aggregation. |
| Flow identity | New TCP blocks are zero-initialized, including both slots. Cancellation precedes deletion, preventing allocator address reuse from retaining a stale queue entry. |
| Backpressure | TLS ciphertext remains charged to the socket until consumed. Small receive windows and zero-window reopening use immediate TLS processing. Deferred consumption preserves normal TCP window-update thresholds. |
| Timestamps | Existing TCP/reassembly/TLS receive timestamp propagation is retained. No substitution with queue-drain time. |
| Burst exits | The production RX loop drains after every nonempty burst, before throttling/break and later software-LRO flush. No queue crosses a scheduler yield. |

## Local checks for this release

- Optimized Linux/amd64 simulator rebuilt against AWS-LC 5.11.0 in Docker emulation.
- 111/111 TCP/ASTF/scheduler tests passed in normal simulator mode.
- 111/111 passed with RX batching enabled for all simulator receive deliveries.
- Coverage includes TLS 1.2/1.3, small/zero windows, resource failures, partial
  records with FIN/RST, overlap/reordering, retransmissions, deadlines, active
  stop, cleartext HTTP/2, TLS HTTP/2, HTTP validation and UDP RTT statistics.
- The new real-flow destruction test queues and frees 192 flows over three
  bursts, exercising allocator reuse and both cancellation paths.
- The delayed empty-ACK test covers both directions and both TLS versions. It
  reproduces a duplicate-only packet count with zero duplicate payload bytes;
  it does not prove the origin of the NIC counters.

- TLS engine/protocol/resumption/policy, RX timestamp and fuzzer-smoke checks passed.
- 13/13 repository/profile tests and 4/4 UDP RTT API tests passed.
- Full and incremental patch application passed with exact output hashes.

See [normal](rx-queues-normal.txt), [batched](rx-queues-batched.txt),
[source provenance](source-provenance.txt) and [results](results.json).

The new destruction test initially hit the simulator's deliberately unsupported
`on_flush_tx` stub when supplied a production-style context. It now drains using
the simulator's established no-context path. This was a test-harness setup error,
not a production queue fix. Actual TX submission is covered by the physical-NIC
experiment, not that synthetic destruction test.

## Limits

The simulator uses its own clock and cannot reproduce CPU-induced physical wire
latency. This final queue suite was not run under ASan/TSan. The local optimized
build uses two pre-existing harness accommodations: suppression of GCC's
`maybe-uninitialized` warning-as-error and a larger HTTP/2 status formatting
scratch buffer. Neither is exported in the release patches. Production sources
otherwise match the manifest; the two accommodations are outside the RX changes.
A fresh production DPDK build and multi-profile NIC campaign of the packaged
release were not performed locally. The physical-NIC evidence applies to the
identical production RX changes and the workload documented in the
[release notes](../docs/release-1.0.1.md).

A follow-up review reproduced unsolicited repeated FIN and added a scoped
[TLS closure correction](tls-fin-review.md). Its physical-NIC impact remains to
be checked. Counters were not suppressed and TCP validation was not relaxed.
