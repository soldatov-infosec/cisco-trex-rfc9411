# HTTP/1.1 message receives

Available in the RFC 9411 extension starting with 1.1.0.

```python
client = ASTFProgram(http=dict(responses=10, transactions=True,
                               expected_status=200, expected_body_bytes=1024))
server = ASTFProgram(side='s', http=dict(requests=10))

# Repeat the following commands using normal ASTF loop commands as needed.
client.http_request_start()
client.send(request)
client.recv_http_response(timeout_ms=30000)
server.recv_http_request(timeout_ms=30000)
server.send(response)
```

The same commands work with TLS options on both programs. Request and response
counts describe the entire program, including loop iterations. The timeout is
per receive command, in milliseconds (1..86400000), beginning when that command
executes. It does not replace the TLS handshake timeout.

A receive consumes one completed message. Input is parsed as it arrives, even
while a blocking send is waiting for acknowledgment. Completed messages and
partial parser state survive until the program reaches the receive command.
Payloads are not retained in full. ASTF continuation never occurs inside the
parser event callback. Byte-count receives and HTTP-message receives cannot be
mixed in one program.

`expected_body_bytes` checks the decoded framing payload length: chunk-size
lines and trailers do not contribute. It does not decompress Content-Encoding.
`max_body_bytes` limits accepted body size. `body_contains` searches body bytes
across fragments and chunks, as in 1.0.1. Unexpected status or content fails the
transaction; redirects are not followed. A client may opt into `head_response`
for a program issuing only HEAD requests; automatic mixed-method association is
not implemented yet.

Server parsing uses `requests`, not `responses`; it does not contribute client
response or latency samples. The server must consume the full request body
before sending the scripted response. HTTP/1.1 headers may change length without
changing program synchronization.

Current scope excludes CONNECT, protocol Upgrade, Expect/100-continue request
handling and HTTP pipelining guarantees. The parser rejects CONNECT, Upgrade
and Expect requests rather than waiting indefinitely for an unsupported exchange.
Close-delimited responses complete only at EOF; a subsequent request on that
connection cannot be fulfilled. TLS EOF must come through the existing TLS
closure validation, not be inferred from an arbitrary TCP reset.

## Diagnostics

`tcps_http_timeouts` counts expired HTTP-message receives, on either endpoint.
The same event increments `tcps_http_errors`; it is not a request-tracking error.
`tcps_http_transaction_errors` remains reserved for invalid latency request
tracking. `tcps_http_bad_status`, `tcps_http_bad_content`, `tcps_http_truncated`
and `tcps_http_framing` retain separate failure categories. Request-side
failures appear in server statistics. Failed exchanges do not add successful
response or TTLB samples. Transport aborts may additionally increment TLS and
HTTP-aborted counters; these categories must not be summed as distinct flows.

The request parser is a framing validator, not a general-purpose HTTP server:
it does not route requests by Host/path, decompress content, or synthesize
HTTP error pages. It discards trailer metadata after syntax validation and
never merges it into framing headers. Chunk extensions accept whitespace,
tokens and quoted values according to [RFC 9112 section 7.1.1](https://www.rfc-editor.org/rfc/rfc9112.html#section-7.1.1);
their semantics are ignored. Ambiguous framing is rejected.

## Memory and CPU scope

Each enabled endpoint owns a bounded header buffer of `max_header_bytes + 1`
bytes (16,385 bytes by default). Parsing a message performs no buffer growth or
body allocation. Enabling request parsing therefore adds a server-side header
buffer; the response-side allocation already existed in 1.0.1. Body matching
also owns a prefix array proportional to the configured search string.

The header buffer is not zero-initialized: every inspected byte has already
been written by the incremental scanner. This removes a full-buffer clear at
flow creation. It does not reduce the configured memory capacity. The parser
microbenchmark is `tests/tls/http_bench.cpp`, built with a normal C++11 compiler
and `-O3 -I src`. It measures construction plus one or ten 16-KiB responses
fragmented into 1460-byte inputs. It is not an estimate of end-to-end CPU usage.

## Standalone example

`scripts/astf/http_messages.py` uses message receives on both endpoints. The
plain TCP default uses ten 16-KiB responses. Add `--chunked` for chunk framing
and trailers, or `--tls --cert SERVER_CERT --key SERVER_KEY --ca CLIENT_TRUST`
for TLS 1.3. With inspection, CLIENT_TRUST must trust the CA used by the DUT to
sign the certificate presented to the client; `--authority` controls Host/SNI.
See the release validation report for simulator, live software-port and NIC coverage.

## Concurrent-connection profiles and long deadlines

HTTP-message deadlines accept up to one day (86,400,000 ms). Production arms
at most ten minutes at a time and checks the absolute deadline before failure;
the simulator uses shorter slices to remain within its serviced timer level.
This avoids overflow when converting milliseconds to the timer's microseconds.

The staged standalone HTTPS profiles expose `--http-timeout-ms` (default 30000).
The server request deadline includes the configured CC pause automatically.
The client response deadline excludes the intentional pause, because its next
receive command executes only after the next request. The original final CC
hold and maximum one-hour pause are preserved. Mixed-object TP continues to
validate framing, status and body content; its per-program size limit does not
assert each individual object's expected size.
