# SPDX-License-Identifier: Apache-2.0
"""Standalone RFC 9411-oriented ASTF workload; see README.md."""
import argparse
import math
from pathlib import Path

from trex.astf.api import (ASTFProgram, ASTFIPGen, ASTFIPGenDist, ASTFIPGenGlobal,
                          ASTFGlobalInfo, ASTFTCPClientTemplate,
                          ASTFTCPServerTemplate, ASTFAssociationRule,
                          ASTFTemplate, ASTFProfile)


class Profile:
    protocol = 'http2'
    objective = 'cps'

    def get_profile(self, tunables, **kwargs):
        encrypted = self.protocol != 'http2'
        h2 = self.protocol != 'https'
        cc = self.objective == 'cc'
        p = argparse.ArgumentParser(description='RFC 9411-oriented %s %s workload' %
                                    (self.protocol, self.objective),
                                    formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        p.add_argument('--response_size_kb', type=float, default=2,
                       help='Response body in KiB; excludes HTTP/TLS/frame overhead')
        p.add_argument('--flow_size', type=int, default=1 if self.objective == 'cps' else 10,
                       help='Requests per TCP connection; CPS requires one')
        p.add_argument('--delay', type=float, default=30 if cc else 0,
                       help='CC: client pause after each response in seconds; otherwise server delay in microseconds')
        p.add_argument('--ramp_up', type=int, default=0, help='ASTF connection-rate ramp in seconds')
        p.add_argument('--authority', default='localhost', help='HTTP authority and TLS SNI/verification name')
        p.add_argument('--port', type=int, default=443 if encrypted else 80)
        if cc:
            p.add_argument('--limit', type=int, default=60000000,
                           help='Total connection creation limit, NOT simultaneous connection count')
        if h2:
            p.add_argument('--concurrency', type=int, default=1,
                           help='Maximum concurrent HTTP/2 streams per connection')
            p.add_argument('--timeout_ms', type=int, default=None, help='HTTP/2 session deadline')
        if encrypted:
            p.add_argument('--cert', required=True)
            p.add_argument('--key', required=True)
            p.add_argument('--ca', required=True)
            p.add_argument('--version', choices=['1.2', '1.3'], default='1.3')
            p.add_argument('--cipher-suite', help='Default: TLS_AES_128_GCM_SHA256 (1.3), ECDHE-ECDSA-AES128-GCM-SHA256 (1.2)')
            p.add_argument('--groups', nargs='+')
            p.add_argument('--signature-algorithms', nargs='+')
        a = p.parse_args(tunables)
        if not math.isfinite(a.response_size_kb) or not 1 <= a.response_size_kb * 1024 <= 1048576:
            p.error('response_size_kb must specify 1..1048576 bytes')
        size = int(a.response_size_kb * 1024)
        if size != a.response_size_kb * 1024:
            p.error('response_size_kb must resolve to an integral byte count')
        if not 1 <= a.flow_size <= 1000000 or (self.objective == 'cps' and a.flow_size != 1):
            p.error('flow_size must be 1..1000000; CPS requires exactly one')
        if not math.isfinite(a.delay) or not 0 <= a.delay <= (3600 if cc else 1000000):
            p.error('delay outside supported range')
        if cc and int(a.delay * 1000000) == 0:
            p.error('CC requires a positive hold interval')
        if h2 and a.delay and not cc:
            p.error('HTTP/2 server delay is not supported; use --delay 0')
        if not 0 <= a.ramp_up <= 600 or not 1 <= a.port <= 65535:
            p.error('ramp_up must be 0..600 and port 1..65535')
        if not a.authority or len(a.authority) > 253 or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-' for c in a.authority):
            p.error('authority must be a DNS name or IPv4 address without a port')
        if cc and not 1 <= a.limit <= 2147483647:
            p.error('limit must be 1..2147483647')
        if h2 and a.timeout_ms is None:
            a.timeout_ms = int(a.flow_size * a.delay * 1000) + 30000 if cc else 30000
        if h2 and cc and (a.concurrency != 1 or a.delay * 1000 != int(a.delay * 1000) or a.delay < 0.001):
            p.error('HTTP/2 CC requires concurrency=1 and whole-millisecond positive pauses')
        if h2 and cc and a.flow_size * a.delay * 1000 >= a.timeout_ms:
            p.error('HTTP/2 deadline must exceed total intentional hold time')
        if h2 and (not 1 <= a.concurrency <= min(128, a.flow_size) or not 1 <= a.timeout_ms <= 600000):
            p.error('concurrency must be 1..min(128, flow_size); timeout_ms 1..600000')

        client_tls = server_tls = None
        if encrypted:
            for name in ('cert', 'key', 'ca'):
                value = Path(getattr(a, name)).expanduser().resolve()
                if not value.is_file():
                    p.error('%s file does not exist: %s' % (name, value))
                setattr(a, name, str(value))
            policy = dict(version=a.version, resumption=False,
                          cipher_suite='TLS_AES_128_GCM_SHA256' if a.version == '1.3'
                          else 'ECDHE-ECDSA-AES128-GCM-SHA256')
            if a.version == '1.2':
                policy['groups'] = ['P-256']
            for option in ('cipher_suite', 'groups', 'signature_algorithms'):
                value = getattr(a, option)
                if value is not None:
                    policy[option] = value
            client_tls = dict(policy, sni=a.authority, ca=a.ca, verify=True)
            server_tls = dict(policy, cert=a.cert, key=a.key)

        if h2:
            client = ASTFProgram(tls=client_tls, http2=dict(authority=a.authority, path='/index.html',
                requests=a.flow_size, concurrency=a.concurrency, expected_status=200,
                body_size=size, max_body_size=size, timeout_ms=a.timeout_ms,
                **({'request_interval_ms': int(a.delay * 1000), 'final_hold_ms': int(a.delay * 1000)} if cc else {})))
            server = ASTFProgram(side='s', tls=server_tls, http2=dict(body_size=size, status=200,
                concurrency=a.concurrency, timeout_ms=a.timeout_ms))
        else:
            client = ASTFProgram(tls=client_tls, http=dict(responses=a.flow_size,
                expected_status=200, max_body_bytes=size, transactions=True, body_contains='x'))
            server = ASTFProgram(side='s', tls=server_tls)
            request = ('GET /index.html HTTP/1.1\r\nHost: %s\r\n'
                       'User-Agent: trex-rfc9411\r\nAccept: */*\r\n'
                       'Connection: %s\r\n\r\n' %
                       (a.authority, 'close' if self.objective == 'cps' else 'keep-alive')).encode('ascii')
            response = ('HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n'
                        'Content-Length: %d\r\n\r\n' % size).encode('ascii') + b'x' * size
            for program in (client, server):
                program.set_var('remaining', a.flow_size)
                program.set_label('exchange')
            client.http_request_start()
            client.send(request)
            client.recv(len(response))
            if cc:
                # Preserve the source CC profile's final hold as well as inter-request pauses.
                client.delay(int(a.delay * 1000000))
            client.jmp_nz('remaining', 'exchange')
            server.recv(len(request))
            if a.delay and not cc:
                server.delay(int(a.delay))
            server.send(response)
            server.jmp_nz('remaining', 'exchange')
            server.wait_for_peer_close()

        distribution = 'seq' if cc else 'rand'
        ip = ASTFIPGen(glob=ASTFIPGenGlobal(ip_offset='1.0.0.0'),
            dist_client=ASTFIPGenDist(ip_range=['16.0.0.1', '16.0.255.199'], distribution=distribution),
            dist_server=ASTFIPGenDist(ip_range=['48.0.0.1', '48.1.255.199'], distribution=distribution))
        cg, sg = ASTFGlobalInfo(), ASTFGlobalInfo()
        for glob in (cg, sg):
            # IPv4 defaults from RFC 9411 sections 4.3.1.1 and 4.3.2.1.
            glob.tcp.mss = 1460
            glob.tcp.initwnd = 10
            glob.tcp.rxbufsize = 65535
            glob.tcp.txbufsize = 65535
            if cc:
                glob.tcp.keepidle = 5000
                glob.tcp.keepintvl = 5000
        if a.ramp_up:
            cg.scheduler.rampup_sec = a.ramp_up
        template = ASTFTemplate(
            client_template=ASTFTCPClientTemplate(program=client, ip_gen=ip, cps=1, port=a.port,
                **({'limit': a.limit} if cc else {})),
            server_template=ASTFTCPServerTemplate(program=server, assoc=ASTFAssociationRule(port=a.port)))
        return ASTFProfile(default_ip_gen=ip, default_c_glob_info=cg,
                           default_s_glob_info=sg, templates=template)


def register():
    return Profile()
