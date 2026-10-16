---
name: Performance analysis
about: A comparable measurement or a concrete optimization proposal
title: ""
labels: ""
assignees: ""
---

## Workload and negotiated parameters
Profile hash, offered/actual CPS, requests/connection, response size, concurrency,
TLS version/cipher/group/signature, resumption, verification and DUT policy.

## Environment
CPU model and clock policy, worker affinity, NUMA, NIC/firmware/PMD, dependency versions.

## Method and results
Warmup/measurement interval, repeat count, baseline, CPU, throughput, successful
transactions, latency, completion tail, errors. Distinguish aggregate port traffic
from useful application throughput. Explain what evidence supports the bottleneck.

## Proposed change
Expected mechanism, resource/lifetime risks and validation plan.
