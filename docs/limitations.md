# Known limitations

- Exact supported base: TRex v3.06; newer upstream versions require a deliberate port.
- AWS-LC only; external PSK, 0-RTT, crypto_mb, QAT and kTLS are not supported paths.
- Synchronous crypto runs on the DP worker. A pump iteration budget cannot preempt
  a costly signature or create more compute capacity.
- Buffering is bounded and includes copies/allocations. End-to-end zero-copy TLS
  is not claimed. Resource-failure handling is tested but does not eliminate limits.
- Cleartext HTTP/2 requires prior knowledge. Server push, Upgrade, arbitrary custom
  H2 request headers and general browser behavior are outside the workload API.
- UDP RTT assumes one outstanding request and the next datagram as its response.
- Plain profiles need explicit HTTP validation/measurement commands; PCAP/EMIX
  transaction boundaries are not inferred automatically.
- Software timestamps and TLS record attribution have the boundaries documented
  in measurements.md. Histograms do not retain exact per-sample quantiles.
- The throughput profile tcp_https_16KB_ecdsa.py can be loaded through
  ASTF; its direct-execution hook references a separate run_https_stats helper
  that is not bundled here. Use nic_validation/run.py for supported capture.
- Standalone build/tests need Python 3.10/3.11 for the upstream API. A release
  simulator build on the local GCC toolchain encountered an upstream
  tuple_gen_test.cpp maybe-uninitialized warning under -Werror; debug tests passed.
- Device-specific PMDs, topology and maximum rates must be validated on the target
  host. The supplied NIC evidence is one reproducible workload, not a capacity guarantee.

