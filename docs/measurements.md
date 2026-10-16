# Measurement semantics

Latency is measured from actual workload traffic. It is separate from TRex's
optional probe-stream latency. A successful TCP handshake alone is not a valid
HTTP latency sample.

| Metric family | Origin | Completion and scope |
|---|---|---|
| `tcps_ttfb_*` | First SYN send attempt; retransmits do not restart it | First response data for a successfully validated connection |
| `tcps_ttlb_*` | Same SYN origin | Completion of required HTTP responses; excludes later shutdown/control traffic |
| `tcps_http_req_ttfb_*`, `tcps_http_req_ttlb_*` | Explicit `http_request_start()` | HTTP/1 transaction response, sequential supported exchange |
| `tcps_http2_ttfb_*`, `tcps_http2_ttlb_*` | Connection SYN origin | Successful HTTP/2 connection, not each stream as an independent RFC connection sample |
| `udps_rtt_*` | `udp_request()` send | Next received datagram in a sequential exchange |

HTTP/2 response HEADERS start the response interval; DATA/CONTINUATION and response
completion determine its end. PING, SETTINGS, WINDOW_UPDATE, GOAWAY and connection
shutdown must not extend the completed response's TTLB. Refused, reset or incomplete
responses are not silently counted as successful connection samples.

## Where the clock is sampled

Receive timestamps enter at TCP payload processing, after NIC polling/flow lookup,
and travel through reassembly. For TLS they are attributed at record granularity:
the first wire byte and latest required fragment of the authenticated record.
The measured interval therefore excludes later application-processing delay but
includes work before that observation point and may include TLS record overhead.
It is not a hardware timestamp or an exact plaintext-byte wire timestamp.

A reassembled record's latest required arrival may belong to a lower sequence
number. Timestamp propagation respects the accepted overlap policy. Verification
still occurs before plaintext is delivered or a successful sample is published.

## Histograms and snapshots

Counters provide counts, totals/averages, min/max and logarithmic histograms.
Reported percentile values are bucket-derived estimates, not exact per-sample
quantiles. State the bucket granularity when reporting p95/p99.

Stats snapshots are cumulative. Rates use collection intervals; latency summaries
cover accumulated successful samples. Do not subtract min/max or percentiles to
invent a sustain-only result. There is no measurement-phase epoch in this engine;
a connection may begin, receive its response and close in different phases.

Verbose negotiation and failure counters remain in `get_stats()` even where the
live console omits them. `global.tx_bps` aggregates port traffic; it is not equal
to delivered HTTP body throughput. Record payload size, direction and accounting
boundary in every benchmark report.

Cost metrics under `utilization.cpu[*].tls_cost` are optional diagnostics.
`TREX_ASTF_COST_SHIFT=off` disables probes; `8` samples approximately 1/256 calls;
`0` samples every call. Nested sampled times are not additive CPU breakdowns.
The old no-op LibraryScope fields were removed; server-own-signature fields are
zero where AWS-LC does not expose that metadata.

## UDP interpretation

`udp_request` does not add a correlation header. Use it for a single outstanding
request followed by its response. Reordered, unsolicited, duplicated or unrelated
datagrams can defeat that assumption. Timeout is a failed transaction and closes
the flow. Automatic inference from EMIX/PCAP exchanges is not implemented.

## Completion and errors

Count successful handshakes, validated responses, completed RTT transactions,
timeouts, aborts, active flows, port errors and resource failures together.
A nonzero RX throttle counter means an RX processing bound was reached; it is
not itself a packet-loss count. Compare datagram/transaction balance and TCP
retransmission evidence before attributing loss. An apparently low CPU average
also does not rule out a saturated individual worker.
