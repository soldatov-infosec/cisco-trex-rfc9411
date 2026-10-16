# Profile API

Options extend `ASTFProgram`; existing profiles need no migration. These are
building blocks for complete client/server templates, not standalone Python programs.

## TLS

```python
policy = dict(version='1.3', cipher_suite='TLS_AES_128_GCM_SHA256',
              groups=['P-256'], signature_algorithms=['ecdsa_secp256r1_sha256'],
              resumption=False)
client = ASTFProgram(tls=dict(policy, sni='localhost', ca='/path/ca.pem'))
server = ASTFProgram(side='s', tls=dict(policy,
    cert='/path/server.pem', key='/path/server.key'))
```

| Option | Meaning |
|---|---|
| `version` | Exactly `1.2` or `1.3`; not a min/max negotiation range |
| `sni` | Client SNI and verification hostname; server checks the offered name against its certificate |
| `cert`, `key` | PEM paths on the TRex host; required for the server and optional on the client for mTLS |
| `ca`, `verify` | Trust and client certificate-chain/hostname verification; verification defaults on |
| `require_client_cert` | Server requires and validates a client certificate; explicit server CA required |
| `cipher_suite` | One supported suite for the selected TLS version |
| `groups` | Ordered subset of X25519, P-256, P-384, P-521 |
| `signature_algorithms` | Ordered supported signature schemes; choose ones compatible with your certificate |
| `resumption`, `session_timeout` | Optional ticket/session reuse; resumption defaults off |
| `alpn` | `http/1.1` or `h2`; native HTTP/2 sets and verifies h2 |
| `handshake_timeout_ms`, `close_timeout_ms` | Bounded connection setup and close waits |

TLS 1.3 suites: `TLS_AES_128_GCM_SHA256`, `TLS_AES_256_GCM_SHA384`,
`TLS_CHACHA20_POLY1305_SHA256`. TLS 1.2 policy uses supported ECDHE RSA/ECDSA
AES-GCM or ChaCha20 suites. See the installed schema/API for the exact allowlist;
unsupported or duplicate values are rejected before running traffic.

Full certificate validation remains enabled in normal use. For an inspecting
NGFW, configure the client to trust the inspection CA as appropriate to the test.
The proxy usually presents a replacement **server** certificate to the client;
client certificates are a separate mTLS concern.

Mandatory mTLS adds client credentials and server trust:

```python
client = ASTFProgram(tls=dict(policy, sni='localhost', ca='/path/server-ca.pem',
    cert='/path/client.pem', key='/path/client.key'))
server = ASTFProgram(side='s', tls=dict(policy,
    cert='/path/server.pem', key='/path/server.key',
    ca='/path/client-ca.pem', require_client_cert=True))
```

Encrypted private keys are not supported. External PSK options retained for
parsing fail with a clear configuration error. Session tickets are a
separate supported mechanism. Ticket/context ownership does not guarantee reuse
across unrelated server contexts; measure actual resumed/full handshake counts.

## Validated HTTP/1.1

```python
client = ASTFProgram(http=dict(responses=10, expected_status=200,
                              body_contains='expected marker', transactions=True))
client.http_request_start()
client.send(request)
client.recv(expected_response_wire_length)
```

Use `tls=...` on the same program for HTTPS. Repeat the marker for every logical
request in loops. Status and completeness are checked; `body_contains` optionally
checks an exact UTF-8 substring in each dechunked body, not a full-body hash or
content decompression. GET response validation does not implement a general
browser, CONNECT tunnel or protocol Upgrade. See the ready `http_verified.py` and
`https_verified.py` profiles for complete loops and templates.

## Native HTTP/2

```python
client = ASTFProgram(http2=dict(requests=10, concurrency=4, authority='localhost'))
server = ASTFProgram(side='s', http2=dict(concurrency=4, body_size=16384))
```

This is cleartext prior knowledge. Add `tls` to both programs for encrypted H2.
`http2` accepts requests, concurrency, body_size, timeout_ms, request_interval_ms,
final_hold_ms, max_body_size,
max_header_size, status, expected_status, authority and path. Requests are GETs;
concurrency is bounded to 1..128. An H2 program owns its session and rejects extra
ASTF commands, PCAP input, addons and simultaneous HTTP/1 validator options.

## UDP RTT

```python
client = ASTFProgram(stream=False)
client.udp_request(b'query', timeout_ms=1000)
server = ASTFProgram(side='s', stream=False)
server.recv_msg(1)
server.send_msg(b'reply')
```

The request command consumes the reply itself; do not append another recv_msg for
that response. Payload bytes remain unchanged. Only client-side sequential
request/response flows without addons are supported. TTFB/TTLB are TCP metrics.

HTTP/2 pacing is client-only. A nonzero request interval requires concurrency=1.
Both pacing values are milliseconds in 0..3600000; the absolute session timeout
(1..600000 ms) must cover all pauses and traffic. Final hold does not extend TTLB.

## Mixed response bodies

`http2.body_sizes` is an optional list of 1..128 integer byte lengths. It overrides
`body_size`; sizes cycle by client stream ID: stream 1 uses element 0, stream 3
element 1, and so on. Set the same list on both endpoints. This keeps the mapping
stable under concurrent responses and does not depend on completion order.
The server generates each selected length; the client checks that exact length
before counting a successful response. Every length must satisfy `max_body_size`;
204/304 responses must have zero length. Without a list, fixed-size behavior is
unchanged. The list is stored in program configuration, without per-request allocation.
