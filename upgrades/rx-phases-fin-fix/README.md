# FIN hotfix for the RX-phase experiment

Apply this small production-only fix if your source already has either the
NIC-tested `rx-phases-on-1.0.0.patch` or the initial, unpublished 1.0.1 bundle
without the FIN fix. It changes three source files; no Git is required.
Do not apply it to clean upstream TRex or unmodified extension 1.0.0.

From the TRex source root:

```sh
patch --dry-run --fuzz=0 -p1 < /path/to/fin-ack-fix.patch
patch --fuzz=0 -p1 < /path/to/fin-ack-fix.patch
```

Rebuild TRex with the existing dependency configuration and hardware targets:

```sh
cd linux_dpdk
./b build --targets=_t-rex-64,mlx5-64 -j4
```

Keep your existing PMD targets if different from mlx5. Restart the rebuilt
server and repeat the same workload. Do not raise CPS for the comparison.
If dry-run fails, do not force the patch; use the complete series on clean
TRex v3.06. The complete series already includes this fix.

`manifest.json` records input/output hashes. This hotfix changes production
code only; new regression tests are included in the full release series.
Consequently, the full release's all-file verifier may report different test
files on a hotfixed experimental checkout. Use a clean full-series installation
to reproduce every file in the full release manifest.

See the [cause, validation and NIC qualification limits](../../validation/tls-fin-review.md).
