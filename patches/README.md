# Consolidated patch series

Apply to clean TRex v3.06. `manifest.json` records the exact upstream revision,
before/after SHA-256 for every path, patch hashes, and provenance. `series` is the
only authoritative application order. Each path belongs to exactly one patch,
which makes an all-series dry-run against the unmodified base valid.

| Patch | Ownership |
|---|---|
| 0001-wire-layout.patch | Common packet-header layout/alignment fixes; affects ordinary traffic too |
| 0002-tls-engine-and-build.patch | AWS-LC flow engine, BIO helpers, Waf dependency integration |
| 0003-http-engines.patch | HTTP/1 parser and transactions, nghttp2 session adapter |
| 0004-astf-transport-and-latency.patch | TCP/UDP integration, reassembly, mbufs, timestamps, statistics |
| 0005-profile-api-and-loading.patch | Python API, schema, configuration loading and validation |
| 0006-scheduler-and-diagnostics.patch | ASTF catch-up scheduling, cost metrics and RPC metadata |
| 0007-tests-and-simulator.patch | Engine, simulator, fault, interop, API and diagnostic tests |
| 0008-documentation-and-examples.patch | Installed TRex documentation and profile examples |
| 0009-nic-validation-toolkit.patch | Four-file NIC smoke/load capture toolkit |

The manifest records the upstream base, patch hashes and the expected contents
of all 147 installed paths. Apply the complete series to a clean TRex v3.06 tree.
Keep future changes in their owning subsystem patch and regenerate the manifest.
