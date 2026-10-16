# Runnable profiles

The patches install examples into the **TRex source tree**. Keep a single source
of truth there; this directory explains how to use them without duplicating code.
Run `start` commands in the TRex console with the patched server already running.
Certificate paths are paths on the TRex server.

| Installed profile | Purpose |
|---|---|
| `astf/https_verified.py` | Validated HTTP/1.1 over TLS, latency and optional mTLS/policy options |
| `astf/http_verified.py` | Validated HTTP/1.1 over cleartext TCP |
| `astf/https2.py` | Native HTTP/2 over TLS |
| `astf/http2.py` | Native cleartext HTTP/2 prior knowledge |
| `astf/udp_imix_rtt.py` | Sequential UDP transaction RTT |
| `astf/nic_validation/run.py` | Six-case smoke/load suite with text diagnostics |

Create a localhost ECDSA lab certificate using the installed helper or OpenSSL CLI;
use a CA trusted by the client for a real DUT path. Never disable verification
just to make an unexpected interception certificate succeed.

```text
start -f astf/http_verified.py -m 100 -d 10
start -f astf/http2.py -m 100 -d 10
start -f astf/https2.py -m 100 -d 10 -t --cert /path/server.pem --key /path/server.key --ca /path/ca.pem --requests 10 --concurrency 4 --body_size 16384
```

The ready-made examples use base CPS=1. A multiplier is an offered flow rate, not
a bandwidth setting. Use the matching profile's tunable help for its options.
For a fully packaged lab certificate + capture workflow, run from TRex `scripts`:

```sh
python3 astf/nic_validation/run.py --smoke --output /tmp/trex-smoke
python3 astf/nic_validation/run.py --cases tls13 --mult 1000 --duration 30 --output /tmp/trex-tls13
```

See [profile API](../docs/profile-api.md) before composing custom workloads and
[measurements](../docs/measurements.md) before interpreting latency counters.

For CPS, throughput and concurrent-connection workloads, see the separate
[ready-to-load profiles](../profiles/rfc9411/README.md).
