# Release 1.1.0

This release builds on the published 1.0.1 transport and TLS implementation.
It adds HTTP/1.1 message-aware receive commands for profiles traversing devices
that rewrite HTTP headers or transfer framing, including TLS inspection.

## Behavior

`recv_http_request()` and `recv_http_response()` wait for a complete validated
message rather than a fixed wire-byte count. Both endpoints must opt in.
Existing byte-count profiles remain unchanged. The shipped HTTPS CPS, TP, CC
and mixed-object profiles use the new commands. HTTP/2, UDP and cryptographic
policy are unchanged.

Fixed-length and chunked bodies, trailers, informational responses and
close-delimited responses are supported. Explicit HEAD mode is available.
Unexpected status, malformed framing, truncated bodies or failed content checks
fail the exchange rather than being counted as successful responses. Redirects
are not followed, and compressed content is not decompressed.

Inspection still requires the client to trust the DUT's signing CA. Message
framing does not bypass certificate validation or turn the scripted server into
a general-purpose HTTP server. See [API and limitations](http-message-api.md)
and [architecture](http-message-design.md).

## Installation

For clean TRex v3.06 use the [consolidated series](getting-started.md).
For released 1.0.1 use the separate [upgrade patch](../upgrades/1.0.1-to-1.1.0/README.md).
Do not apply both routes to the same tree.

## Validation and resource costs

See the [1.1.0 validation report](../validation/http-message-1.1.0.md).
No physical-NIC performance or real-NGFW inspection result is claimed for 1.1.0.
Earlier 1.0.1 results are historical measurements, not measurements of this release.
The new request parser reserves a header buffer per server flow (16,385 bytes
by default), in addition to metadata. Size concurrency and memory accordingly.
