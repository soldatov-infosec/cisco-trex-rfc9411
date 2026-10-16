# Traffic profiles

The [RFC 9411-oriented workloads](rfc9411/README.md) provide ready-to-load ASTF
profiles for connection rate, throughput and concurrent-connection experiments.
They require this repository's extension applied to TRex v3.06.

These are editable profile sources, separate from the engine patch series.
Each profile is self-contained. Copy the desired files from `rfc9411` into
TRex `scripts/astf/rfc9411`. HTTP/2 CC requires the extension's engine patches.
