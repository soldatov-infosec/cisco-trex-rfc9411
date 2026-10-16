# Licensing and third-party notices

Original repository tooling and documentation are distributed under Apache-2.0.
The root LICENSE preserves the TRex server license text. Patches modify existing
upstream files and retain their applicable notices and terms; this is not a blanket
relicensing of TRex or its Python client.

| Project | Relationship |
|---|---|
| Cisco TRex | Upstream base; server license in LICENSE; Python client notice preserved in licenses/LICENSE_Python_Client |
| AWS-LC | Direct TLS/crypto dependency, downloaded and built separately; retain its own LICENSE/NOTICE when redistributing binaries |
| nghttp2 | Direct HTTP/2 dependency, supplied separately; retain its own licensing notices |
| OpenSSL CLI, python-h2, GnuTLS test tools | Optional certificate generation/interoperability/testing tools, not vendored libraries |

The upstream repository contains additional component licenses. Review those when
redistributing a complete TRex build; the patch repository does not replace them.
No claim of copyright ownership over upstream code is made. No Cisco affiliation
or endorsement is implied. RFC text is referenced by link, not republished here.
