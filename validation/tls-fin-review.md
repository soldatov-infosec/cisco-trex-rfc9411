# TLS close ACK / FIN review

## Finding

The transport-first receive path exposed an unnecessary FIN retransmission in
TRex's inherited TCP output path. It is not a false positive in
`tcps_rcvduppack`, nor evidence of repeated TLS application bytes.

When an ACK acknowledges the local TLS close_notify before the peer's
close_notify arrives, the application can send its TCP FIN first. Later input
requires an ACK while the connection is still in FIN_WAIT_1, CLOSING or LAST_ACK.
The TCP state supplies TH_FIN; the old output code resends the already-sent FIN
at its original sequence number while acknowledging this new input. The peer
counts the repeated FIN as a duplicate-only packet, with zero duplicate bytes.
The corresponding path can occur on either endpoint during crossing closes.

```mermaid
sequenceDiagram
    participant C as Client
    participant S as Server
    C->>S: TLS close_notify
    S->>C: Early TCP ACK
    C->>S: FIN at sequence F
    S->>C: TLS close_notify
    Note over C: Local FIN remains unacknowledged
    alt Before fix
        C->>S: Repeated FIN at F plus ACK
        Note over S: Duplicate-only packet; zero duplicate bytes
    else After fix
        C->>S: ACK at F+1, without another FIN
    end
```

The `tcps_sndacks` name is also easy to misinterpret: the existing TCP code
counts a zero-payload packet there when TF_ACKNOW is set, even when it also
carries FIN. These counts are not exclusively pure ACKs.

## Change

For TLS sockets only, TCP output clears TH_FIN on a zero-payload, non-SACK
output when a FIN was already sent and `snd_nxt == snd_max`. The packet can
still acknowledge input or advertise the receive window. Its sequence number
uses the existing ACK-only path. The first FIN is unchanged. Actual loss
recovery rewinds snd_nxt below snd_max, so FIN retransmission remains enabled.
The receive-side counters and duplicate checks are unchanged.

The production change touches only tcp_output.c and the internal socket helper
in tcp_socket.cpp/netinet/tcp_socket.h. It does not change RX phase ordering,
TLS cryptography, application parsing, latency timestamps or the TCP behavior
of non-TLS applications. It also applies to HTTP/2 over TLS.

## Reproduction and validation

No packet duplication, loss or reordering is injected in the service-delay
reproducer. It adds a gap to the simulator's monotonically increasing TX delay
at close_notify or the first FIN; later transmissions retain packet order.
This models a gap between early transport output and later close processing;
it is not a CPU performance or latency-accuracy benchmark.

| Test | Before | After |
|---|---|---|
| 64 closure scenarios: TLS 1.2/1.3, both directions, zero/10/100/1000 us gap, sequence wrap, delayed close_notify/FIN | 24 cases produce extra FIN; 12 cases duplicate at both endpoints and 12 at the server only | All 64 send exactly one FIN per endpoint, no duplicate-only packets |
| Eight first-FIN loss scenarios: both TLS versions/directions, sequence wrap | Not repeated in the paired comparison | Actual FIN is retransmitted by RTO; both endpoints close without RST or TLS error |
| TCP/ASTF/scheduler regression | Existing evidence in queue review | 111/111 normal and 111/111 with batched RX |

See [before](fin-before.txt), [after](fin-after.txt), [loss recovery](fin-loss.txt)
and [final regression](rx-queues-batched.txt). The before test intentionally
fails the new assertions; that failure establishes the regression's sensitivity.
The existing delayed empty-ACK test still observes and counts a duplicate-only
packet, confirming that the fix does not hide receive-side diagnostics.

## Physical-NIC qualification

This is a confirmed local cause consistent with the zero-byte duplicate counts
in the submitted NIC run. Without packet-level evidence from that run, it does
not prove that every NIC event had this origin. The fixed code has not yet been
qualified on the physical NIC. Repeat the same 45,000 CPS workload and compare
client/server `tcps_rcvduppack`, `tcps_rcvdupbyte`, retransmissions, close counts,
TLS/HTTP errors, CPU, completed responses and completion tail before publishing.
The earlier CPU reduction was measured with the RX-phase change before this fix;
no new CPU improvement is claimed for this small closure-path change.
