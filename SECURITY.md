# Security policy

This release targets isolated traffic-generator testbeds and still processes
untrusted network data. TLS verification, parser bounds, reassembly ownership and
resource exhaustion are security-relevant parts of the implementation.

For a suspected exploitable vulnerability, use GitHub's **Report a vulnerability**
option if the repository owner has enabled private reporting. If it is unavailable,
ask a maintainer for a private reporting channel without posting exploit details
or secrets. Do not put private keys, production payloads or credentials in issues.

Include the extension/upstream revisions, dependency versions, affected path,
minimal reproducer and impact. There is no guaranteed response SLA. Only the
pinned release is validated here; dependency security advisories must still be
monitored, and an upgrade requires compatibility testing.

Repository owners: enable private vulnerability reporting and configure a working
maintainer contact before advertising a supported private reporting channel.
