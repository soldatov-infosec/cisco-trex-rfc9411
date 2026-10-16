# Getting started

Use a dedicated Linux traffic-generator host and an isolated testbed. This guide
assumes you already know how to configure TRex interfaces, hugepages, PMDs, and
NUMA placement. Keep the upstream [TRex documentation](https://trex-tgn.cisco.com/)
alongside this extension's instructions.

## 1. Obtain the exact upstream base

Use the official [v3.06 release](https://github.com/cisco-system-traffic-generator/trex-core/releases/tag/v3.06),
commit `46be64bedbe9d505dfb55099c38119d6e86267ca`.

```sh
git clone --branch v3.06 --depth 1 \
  https://github.com/cisco-system-traffic-generator/trex-core.git trex-core
python3 cisco-trex-rfc9411/tools/apply.py trex-core --check
python3 cisco-trex-rfc9411/tools/apply.py trex-core
```

For a source archive, extract it to a new directory and pass that directory to
the same helper. Only Python 3 and `patch` are required for applying the series.
Apply to the clean source tree, not an installed TRex binary bundle.

The helper rejects mismatching source hashes and pre-existing added files before
writing. It then dry-runs all patches and verifies the final hashes. OS interruption
or an I/O failure during application is not transactional: discard that temporary
checkout and retry from a clean copy. It does not install packages or run traffic.

Manual application from the clean source root is supported after preflight:

```sh
# Set this to the absolute path of this extension repository.
EXTENSION=/path/to/cisco-trex-rfc9411
python3 "$EXTENSION/tools/apply.py" "$PWD" --check
while IFS= read -r file; do
    patch --batch --forward --fuzz=0 -p1 < "$EXTENSION/patches/$file" || exit 1
done < "$EXTENSION/patches/series"
python3 "$EXTENSION/tools/apply.py" "$PWD" --verify
```

## 2. Build the dependencies

Use a C/C++ toolchain, Python 3 compatible with TRex 3.06, CMake, OpenSSL CLI for
lab certificates, and nghttp2 development headers/libraries. TRex 3.06's Python API
uses `imp`; use Python 3.10/3.11, not Python 3.12+, unless you separately port upstream.
The runtime nghttp2 package must expose `nghttp2_option_set_max_continuations` and
receive distribution security updates. The configure check rejects older packages.

AWS-LC is installed into a dedicated prefix, leaving system OpenSSL intact:

```sh
git clone --branch v5.11.0 --depth 1 https://github.com/aws/aws-lc.git aws-lc
# From the patched TRex source root; adapt these absolute paths.
sh tests/tls/build_aws_lc.sh /path/to/aws-lc /opt/trex-aws-lc-5.11.0
```

The tested AWS-LC revision is `fa9bc8d6f7cfb2cf849b247fb06bbbfc41ecc9d6`.
The install prefix needs to be writable; the helper does not invoke sudo or change
system packages. Build shared libraries. External PSK, an OpenSSL backend, crypto_mb and QAT are not supported.

## 3. Build TRex and the NIC PMD

From the patched source tree:

```sh
cd linux_dpdk
./b configure --rfc9411 --aws-lc-prefix=/opt/trex-aws-lc-5.11.0
# Example for mlx5; retain the appropriate PMD targets for your hardware.
./b build --targets=_t-rex-64,mlx5-64 -j4
cd ../scripts
ldd ./_t-rex-64
```

Keep any additional configure options required by your established TRex/NIC
setup. Both libssl and libcrypto must resolve to your AWS-LC prefix. nghttp2 is
also a runtime dependency. Configuration checks the AWS-LC headers, shared
libraries and runtime version together; it must not fall back to system OpenSSL.

The native HTTP/2 feature, including cleartext mode, is built with `--rfc9411`.
A build without that flag retains ordinary TRex behavior and rejects TLS/HTTP2
profiles. No changes to the system TLS stack or kernel TLS are needed.

## 4. Smoke test, then load

From `scripts`, using your existing NIC configuration:

```sh
TREX_ASTF_COST_SHIFT=8 ./_t-rex-64 -i --astf -c 32 --mlx5-so
```

`32` and `--mlx5-so` describe the validated mlx5 setup, not universal settings.
Choose cores local to your NIC and leave room for TRex control/RX duties. Use your
usual `--cfg` and driver flags. In another terminal, also from `scripts`:

```sh
python3 astf/nic_validation/run.py --plan
python3 astf/nic_validation/run.py --smoke --output /tmp/trex-smoke
# Only after the smoke result is clean:
python3 astf/nic_validation/run.py --output /tmp/trex-load
```

The suite installs through patch 0009. It discovers the matching local TRex API,
generates a local ECDSA lab certificate, executes six cases, and stores text/JSON
statistics in an output directory and ZIP. It does not require `pip install trex`
or perf.data. Output directories must be new. Runs wait for natural completion;
`-d` ends offered flow creation, not necessarily every existing connection.

Defaults are 300 seconds, 30,000 new TCP flows/s and 100,000 UDP flows/s, ten
transactions per connection/flow. These are reproducibility settings from the
validation host, not guaranteed safe loads for another machine. Start with smoke
or use `--cases tls13 --mult 1000 --duration 30`.

Lab profiles use synthetic IP ranges. Check routing/ARP and your DUT rules.
The NIC UDP profile uses client addresses `16.0.0.1..16.0.255.199`.
Never publish the generated `certs/*.key` files or unreviewed capture archives.

