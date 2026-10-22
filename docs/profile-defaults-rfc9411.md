# Profile defaults review — 1.1.0

Reviewed against [RFC 9411](https://www.rfc-editor.org/rfc/rfc9411.html), sections
4.3.1.1, 4.3.1.4, 4.3.2.1 and 4.3.2.4, on 2026-10-22.

The RFC lists AES-128-GCM for TLS 1.3 and ECDHE-ECDSA-AES128-GCM-SHA256 with
P-256 for TLS 1.2. It requires full handshakes without resumption. Its TCP
recommendations include IPv4 MSS 1460 (IPv6 1440), initial windows 65535, and
initial congestion window at most ten MSS, with comparable server settings.
Delayed ACKs are permitted within stated limits. Report negotiated security
parameters, certificate/key characteristics and deviations with benchmark results.

## Implementation choices

The standalone workloads select AES-128 explicitly; this avoids silently taking
the engine's AES-256-first policy. User cipher/group/signature overrides remain
available. TLS 1.2's default group is P-256; TLS 1.3 group and signature defaults
are unchanged. TLS 1.2 ECDSA suites require an appropriate ECDSA certificate;
RSA users must select the compatible RSA suite. The engine's global TLS policy
is unchanged, so custom profiles are unaffected.

MSS 1460 and initwnd 10 are now explicit profile settings, matching engine defaults
(`src/44bsd/netinet/tcp.h`, `src/44bsd/tcp.h`). Existing 65535-byte socket buffers
are retained. The value refers to configured capacity: advertised windows depend
on queued data and TCP processing. No change to ACK scheduling, timestamps,
flow lifecycle, request counts, object sizes or body validation is included.

## Limits found during the review

This is a profile configuration review, not a complete RFC compliance claim.
The transport defines `TCP_MAXRXTSHIFT=5` in `tcp_timer.h`, whereas the RFC's TCP
paragraph allows up to three retries before timeout. The exposed `rexmtthresh`
is the duplicate-ACK fast-retransmit threshold, not a retry limit; setting it to
three would not solve that difference. This revision does not alter TCP retry
semantics. Loss-injection and a separate transport change would be needed.

Actual SYN/window negotiation, PSH placement, ACK timing, source-port range,
loss recovery and DUT-facing changes should be validated on captured traffic.
Profile settings alone do not prove these wire behaviors. DSCP/IP allocation,
DUT setup and test load phases also remain part of the operator's methodology.
No engine-wide tuning or forced ACK changes were made to claim conformance.

## Reproduction

Run `tests/test_profiles.py` with `TREX_ROOT` pointing to the patched tree.
It covers all 33 profiles, both TLS version defaults, RSA/cipher/group overrides
and explicit TCP settings. Run `tools/test_profile_smoke.py --release --cc-defaults`
for complete TLS/HTTP exchanges, using a freshly built simulator.

Version remains 1.1.0. This update changes standalone Python workloads and their
documentation/tests; existing TRex installations do not need recompilation.
