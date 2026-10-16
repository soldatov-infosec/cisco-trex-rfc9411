# RFC 9411-oriented traffic workloads

These profiles adapt the workload shapes of the supplied `http_max_cps_1kb.py`,
`http_max_tp_16kb.py`, and `http_max_cc_1kb.py` examples to native TLS and HTTP/2.
They are new profile implementations using the existing extension API. They do
not automate the complete [RFC 9411 methodology](https://www.rfc-editor.org/rfc/rfc9411.html).
See the [scope document](../../docs/rfc9411-scope.md) for experiment responsibilities.
Names containing `max` identify the intended experiment, not a measured maximum.

## Workload matrix

| Transport / filename prefix | CPS sizes (KiB) | TP sizes (KiB) | CC sizes (KiB) |
|---|---|---|---|
| HTTP/1.1 over TLS: `https` | 1, 2, 4, 16, 64 | 1, 16, 64, 256 | 1 |
| HTTP/2 cleartext: `http2` | 1, 2, 4, 16, 64 | 1, 16, 64, 256 | 1 |
| HTTP/2 over TLS: `https2` | 1, 2, 4, 16, 64 | 1, 16, 64, 256 | 1 |

Each combination has a separate file named `<prefix>_max_<objective>_<size>kb.py`,
for example `https_max_cps_2kb.py` or `https2_max_tp_256kb.py`.
All 33 files are standalone: copy any one profile without a shared helper.
The filename selects the default response body size. CPS sends one response per
connection; TP sends ten; CC sends ten with 30-second pauses.

HTTP/2 CC uses sequential requests with a client pause after each response,
including a final hold before GOAWAY. HTTP/2 CPS and TP reject nonzero server `--delay`;
server-side HTTP/2 response delay is not implemented.

## Install and prepare certificates

Copy the desired `.py` files into `TREX/scripts/astf/rfc9411`.
HTTP/2 CC requires the extension's engine patches and matching Python API.
Use the matching patched TRex client API, not an unrelated pip package. The engine
requires AWS-LC and nghttp2 as described in [getting started](../../docs/getting-started.md).

Generate an ECDSA P-256 lab certificate on the TRex host (the examples assume
the console runs on that host too):

```sh
mkdir -p /tmp/trex-rfc9411-certs
openssl req -x509 -newkey ec -pkeyopt ec_paramgen_curve:P-256 -nodes \
  -keyout /tmp/trex-rfc9411-certs/server.key \
  -out /tmp/trex-rfc9411-certs/server.pem -days 30 \
  -subj /CN=localhost -addext subjectAltName=DNS:localhost
```

Certificate paths must be readable by the profile loader and by the TRex server
at the same absolute paths; remote clients must arrange this explicitly.
The examples verify certificates and names. TLS defaults to 1.3 and **full
handshakes** (`resumption=False`). Use `--version 1.2` to test TLS 1.2. A real PKI
can replace the lab certificate: provide the server chain, key and trusted CA.
When testing TLS inspection, the client trust bundle must trust the certificate
chain actually presented by the inspecting device. Do not disable verification
just to conceal an inspection setup error. Keep keys out of the repository.

## Run

Start the patched TRex in ASTF interactive mode with your normal NIC/NUMA settings.
Run these commands in the TRex console from `scripts`. Initial multipliers are
small smoke-test loads, **not capacity recommendations**:

```text
start -f astf/rfc9411/https_max_cps_1kb.py -m 100 -d 30 -t --cert /tmp/trex-rfc9411-certs/server.pem --key /tmp/trex-rfc9411-certs/server.key --ca /tmp/trex-rfc9411-certs/server.pem
start -f astf/rfc9411/https_max_tp_16kb.py -m 100 -d 30 -t --cert /tmp/trex-rfc9411-certs/server.pem --key /tmp/trex-rfc9411-certs/server.key --ca /tmp/trex-rfc9411-certs/server.pem
start -f astf/rfc9411/https_max_cc_1kb.py -m 10 -d 30 -t --cert /tmp/trex-rfc9411-certs/server.pem --key /tmp/trex-rfc9411-certs/server.key --ca /tmp/trex-rfc9411-certs/server.pem --delay 1 --flow_size 3
start -f astf/rfc9411/http2_max_cps_1kb.py -m 100 -d 30
start -f astf/rfc9411/http2_max_tp_16kb.py -m 100 -d 30
start -f astf/rfc9411/http2_max_cc_1kb.py -m 10 -d 30 -t --delay 1 --flow_size 3
start -f astf/rfc9411/https2_max_cps_1kb.py -m 100 -d 30 -t --cert /tmp/trex-rfc9411-certs/server.pem --key /tmp/trex-rfc9411-certs/server.key --ca /tmp/trex-rfc9411-certs/server.pem
start -f astf/rfc9411/https2_max_tp_16kb.py -m 100 -d 30 -t --cert /tmp/trex-rfc9411-certs/server.pem --key /tmp/trex-rfc9411-certs/server.key --ca /tmp/trex-rfc9411-certs/server.pem
start -f astf/rfc9411/https2_max_cc_1kb.py -m 10 -d 30 -t --cert /tmp/trex-rfc9411-certs/server.pem --key /tmp/trex-rfc9411-certs/server.key --ca /tmp/trex-rfc9411-certs/server.pem --delay 1 --flow_size 3
```

Run one case at a time and wait for natural completion. Remove the CC smoke
`--delay 1 --flow_size 3` overrides for the original 300-second hold workload (all CC transports).
Use `--concurrency 4` on an HTTP/2 TP profile to enable multiplexing explicitly;
the default is one stream at a time to retain the source workload's sequential
transactions. Encrypted HTTP/2 negotiates `h2` through ALPN. Cleartext HTTP/2 uses
prior knowledge on port 80, not HTTP/1.1 Upgrade. TLS defaults to port 443.

## Tunables and units

| Option | Default / meaning |
|---|---|
| `--response_size_kb` | Size in the filename; **body** size in KiB (1024 bytes), maximum 1 MiB |
| `--flow_size` | 1 for CPS (enforced), 10 for TP/CC; requests per connection |
| `--delay` | CPS/TP: server delay in **microseconds**, default 0; CC: client pause in **seconds**, default 30 |
| `--ramp_up` | 0; ASTF offered connection-rate ramp, seconds; not a complete RFC phase controller |
| `--authority` | `localhost`; HTTP Host/authority, TLS SNI and certificate verification name |
| `--port` | 80 for cleartext, 443 for TLS |
| `--limit` | CC only: 60,000,000 total connection creations; **not** a simultaneous-flow target |
| `--concurrency` | HTTP/2 only: 1, maximum min(128, request count) |
| `--timeout_ms` | HTTP/2: 30000 for CPS/TP; CC defaults to total holds + 30000 (330000 at defaults); absolute deadline, maximum 600000 |
| `--cert`, `--key`, `--ca` | Required for TLS; readable local files, resolved to absolute paths |
| `--version` | TLS only: `1.3` or `1.2` |
| `--cipher-suite` | Optional version-compatible cipher policy |
| `--groups`, `--signature-algorithms` | Optional lists accepted by the extension's TLS API |

IP ranges: clients `16.0.0.1..16.0.255.199`, servers
`48.0.0.1..48.1.255.199`, offset `1.0.0.0`. Adapt the selected profile for your routing and
address plan. CPS/TP use random addresses; CC uses sequential addresses. Both
sides use 65,535-byte TCP buffers. The source CC profile's four-second delayed ACK
and long connection-establishment timeout are not carried over; they are unrelated
to application hold time. CC retains extended idle/keepalive intervals.

## Interpret load and measurements

Each template has `cps=1`: `-m N` requests N **new TCP connections/s**, not requests/s,
concurrent sessions or Gbit/s. With TP defaults, nominal server body load is
`N × 10 × size_kib × 1024 × 8` bits/s before HTTP, TLS and network overhead. Actual useful
throughput depends on successful completions and the DUT. HTTP/2 concurrency is
streams per connection, not a multiplier of the requested connection rate.

CC deliberately pauses after **every** response, including the final one, matching
the source profile. At defaults, a healthy flow lives roughly 300 seconds plus
handshake and response time. Steady active connections are approximately offered
CPS × lifetime only once the population has stabilized and absent failures/limits.
`-d` stops new flow creation; the final CC flows can drain for another 300 seconds.
That expected tail must not be confused with scheduler overload or forcibly hidden.

HTTP status 200 and response framing/completeness are validated. HTTP/1 also
checks for an `x` body marker; this is not a full payload checksum. Bodies have an
exact Content-Length, including for small custom sizes. HTTP/2 uses the native
engine's response generator and Content-Length validation. Body sizes exclude
headers, TLS records and HTTP/2 frames.

Connection TTFB/TTLB use the extension's SYN-based semantics. Thus multi-response
CC connection TTLB includes earlier intentional pauses; the final post-response
hold affects connection lifetime but not the last-byte timestamp. HTTP/1 transaction
metrics use explicit request markers and exclude preceding think-time. Do not
compare these two latency populations as if they measured the same interval.
See [measurement semantics](../../docs/measurements.md).

Record successful handshakes, validated responses, active flows, protocol errors,
TCP retransmissions, CPU, negotiated TLS parameters and actual offered/completed
rates. The existing NIC suite is a separate fixed workload: it does not automatically
run these entry profiles. Use the ASTF stats API with your experiment controller.

HTTP/2 CC requires `--concurrency 1` and whole-millisecond pauses. Its session
deadline must exceed `flow_size × delay` plus actual exchange time, on both ends.
The default adds 30 seconds of margin; it does not hide timeouts or extend the
budget when progress occurs. Pauses use the timer wheel, not busy waiting. As
with ordinary HTTP/2, peer GOAWAY/EOF may shorten the hold; inspect active flows
and completed responses when evaluating CC results.

See [validation](../../validation/profiles.md) for simulator and regression results.

## Mixed-object throughput

`https_max_tp_mix.py`, `http2_max_tp_mix.py` and `https2_max_tp_mix.py`
implement the equal request weights of [RFC 9411 Table 5](https://www.rfc-editor.org/rfc/rfc9411.html#table-5).
Each connection requests ten objects, one of each size, in the listed order:
0.2, 6, 8, 9, 10, 25, 26, 35, 59 and 347 KB. We use the same 1024-byte KB
convention as the fixed-size profiles and the supplied HTTP example; the smallest
body is truncated to 204 bytes. All sizes exclude protocol headers. Document this
conversion when reporting results. These are equal request weights, not equal byte shares.

The mixed profiles accept the same certificate, TLS policy, ramp and port options.
`--response_size_kb` and `--flow_size` are intentionally unavailable: each completed
connection contains exactly the ten objects. HTTP/2 accepts `--concurrency`;
objects are assigned in stream-ID order, independently of response completion order.
The HTTP/2 client verifies each response's expected body length. Mixed HTTP/2
requires the matching engine patches with `http2.body_sizes` support; rebuild TRex
if using a previously built binary. The extension version remains 1.0.0.

Example (cleartext):

```text
start -f astf/rfc9411/http2_max_tp_mix.py -m 100 -d 30
```

For HTTPS, select `https_max_tp_mix.py` or `https2_max_tp_mix.py` and supply
`--cert`, `--key` and `--ca` as in the fixed-size examples. Client addresses remain
`16.0.0.1..16.0.255.199`. The total response body per complete connection is
537804 bytes; nominal body throughput at multiplier N is `N × 537804 × 8` bits/s.
