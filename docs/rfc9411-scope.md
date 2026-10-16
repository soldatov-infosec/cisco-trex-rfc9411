# RFC 9411: capability and scope

[RFC 9411](https://www.rfc-editor.org/rfc/rfc9411.html) describes a benchmarking
methodology for network security devices. This extension supplies traffic and
measurement primitives; it does not certify a DUT or automate the entire method.

| Area | Engine capability | Experiment responsibility or limit |
|---|---|---|
| Real HTTPS | TLS 1.2/1.3 client/server, certificates, verification and SNI | Fix and report version, cipher, group, signature and certificate chain |
| Full handshakes | Resumption disabled by default | Do not silently substitute resumed connections in a full-handshake workload |
| HTTP validation | Opt-in HTTP/1 status/completeness checks; native HTTP/2 validation | Enable checks, define the expected response and report failures |
| HTTP/2 | Concurrent streams, ALPN with TLS, cleartext prior knowledge | Select workload parameters; cleartext is not evidence for an encrypted benchmark |
| Latency | SYN-based TTFB/TTLB, carried software RX timestamps | Explain record-level TLS attribution and observation boundaries |
| Load phases | ASTF scheduling and counters | Orchestrate phases and report the actual measurement interval |
| Security effectiveness | Actual traffic through the DUT | Configure/validate DUT security policy and effectiveness separately |
| Test report | API counters and text capture | Describe topology, hardware, load, negotiated parameters and validity criteria |

Relevant method sections: [traffic definitions](https://www.rfc-editor.org/rfc/rfc9411.html#section-4.3.3),
[load profile](https://www.rfc-editor.org/rfc/rfc9411.html#section-4.3.4),
[KPIs](https://www.rfc-editor.org/rfc/rfc9411.html#section-6.3), and
[HTTPS tests](https://www.rfc-editor.org/rfc/rfc9411.html#section-7.6).

## Gaps to preserve in reports

- There is no complete RFC phase controller or sustain-only latency epoch.
- HTTP/2 supports sequential inter-request pauses and a final hold, but no
  automatic hold-until-ramp-down controller. Custom H2 User-Agent/header
  configuration is not exposed.
- TLS_AES_128_CCM_SHA256 is not implemented in the current cipher policy. Supported
  suites are listed in the profile documentation; do not infer that every IANA
  suite or every RFC recommendation is implemented.
- QUIC/HTTP3 is not implemented. UDP transaction RTT is an additional diagnostic,
  not a replacement for TCP/HTTPS latency semantics.
- A full TCP standards-conformance audit and all DUT security-effectiveness
  procedures are outside the evidence supplied by this repository.

Avoid the labels “RFC 9411 certified” or “fully RFC 9411 compliant” for the engine.
Use “TRex extension for RFC 9411-oriented testing” and identify the actual test
procedure and deviations in the resulting report.
