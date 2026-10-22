# Upgrade released 1.0.1 to 1.1.0

This patch targets a TRex v3.06 tree with the released 1.0.1 extension already
applied. Do not apply it to clean TRex or combine it with the consolidated series.
Keep a backup of the source tree and use the existing AWS-LC build configuration.

From the TRex root, first check and then apply using the absolute patch path:

```sh
patch --dry-run --batch --fuzz=0 -p1 < /path/to/upgrade.patch
patch --batch --fuzz=0 -p1 < /path/to/upgrade.patch
cd linux_dpdk
./b build --targets=_t-rex-64 -j4
```

Copy the standalone profiles from this repository's `profiles/rfc9411` into
your chosen profile directory. Existing custom byte-count profiles retain
their behavior; migrate both endpoints explicitly to use message receives.
See [the API guide](../../docs/http-message-api.md).

For a clean TRex tree use the nine consolidated patches through the normal
[installation procedure](../../docs/getting-started.md), not this upgrade.
