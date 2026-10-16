# Contributing

Contributions from networking, TLS, performance and test-methodology engineers
are welcome. Reproducible findings matter more than a particular toolchain or NIC.

## Before changing code

Read docs/architecture.md and docs/measurements.md. Open an issue describing the
problem, a minimal profile and expected/actual behavior. Separate correctness
fixes from performance changes. For security-sensitive findings, use SECURITY.md.
Do not attach private keys or unreviewed production captures.

## Development model

The repository owns a patch series, not a second copy of TRex. Apply it to a clean
supported upstream checkout, edit that development tree, run appropriate tests,
then regenerate the owning patch with tools/regenerate.py. Keep all before/after
hashes and patch hashes current. See docs/maintainers.md for the exact workflow.

A pull request should contain:

- The trigger and changed behavior, with a reproducer or regression test.
- Ownership/lifetime implications for flow, context, mbuf, BIO and callbacks.
- Test commands/results and relevant limitations.
- For performance: identical workload/negotiation, hardware/NUMA, repeat count,
  CPU/CPS/throughput, error balance and measurement interval.
- Documentation updates when API, counters or measurement semantics change.

Avoid speculative rewrites, weaker certificate verification, retries that violate
SSL_write requirements, unbounded queues, packet-path assertions on external data,
and moving crypto out of the flow without an explicit design discussion.
Do not present sample rates as hardware capacity or cumulative percentiles as
sustain-only measurements.

## Review and collaboration

Use small commits and descriptive pull requests. Preserve upstream notices and
state the origin/license of third-party code. Do not copy a new crypto library
into this repository. Discuss new dependencies and incompatible profile/API
changes before implementation. Follow CODE_OF_CONDUCT.md.

There is no promised review SLA or paid support commitment. Independent test
reports, documentation corrections, and well-scoped failing tests are valuable
contributions even without a complete fix.
