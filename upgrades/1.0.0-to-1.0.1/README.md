# Upgrade 1.0.0 to 1.0.1

This patch targets the unmodified 1.0.0 extension on TRex v3.06. It is not for a
clean upstream tree or a tree already carrying the experimental RX patch.
Back up your source tree and run from the TRex source root:

```sh
patch --dry-run --fuzz=0 -p1 < /path/to/cisco-trex-rfc9411/upgrades/1.0.0-to-1.0.1/upgrade.patch
patch --fuzz=0 -p1 < /path/to/cisco-trex-rfc9411/upgrades/1.0.0-to-1.0.1/upgrade.patch
python3 /path/to/cisco-trex-rfc9411/tools/apply.py . --verify
```

Then rebuild with the same AWS-LC/nghttp2 configuration as 1.0.0; see
[build instructions](../../docs/getting-started.md). No new dependency or runtime
option is required. If dry-run fails, do not force application: use clean v3.06
and the complete 1.0.1 series. `manifest.json` records every changed file's input
and output SHA-256, plus the incremental patch checksum.
