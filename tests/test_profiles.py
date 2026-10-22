# SPDX-License-Identifier: Apache-2.0
"""Set TREX_ROOT to a patched v3.06 source tree to run real ASTF API checks."""
import base64
import contextlib
import io
import os
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
TREX = os.environ.get('TREX_ROOT')
if TREX:
    sys.path.insert(0, str(Path(TREX) / 'scripts/automation/trex_control_plane/interactive'))
    from trex.astf.api import ASTFProfile


@unittest.skipUnless(TREX, 'set TREX_ROOT to run against the real patched ASTF API')
class Profiles(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        # Serialization tests only: certificate loading is a server-side operation.
        self.fixture = Path(self.tmp.name) / 'fixture'
        self.fixture.write_text('serialization fixture, not a certificate')

    def load(self, name, args=()):
        opts = list(args)
        if name.startswith('https'):
            opts += ['--cert', str(self.fixture), '--key', str(self.fixture), '--ca', str(self.fixture)]
        return ASTFProfile.load(str(ROOT / 'profiles/rfc9411' / name), tunables=opts).to_json()

    def test_all_entries(self):
        entries = sorted((ROOT / 'profiles/rfc9411').glob('*_max_*.py'))
        self.assertEqual(len(entries), 33)
        for path in entries:
            with self.subTest(profile=path.name):
                doc = self.load(path.name)
                programs = doc['program_list']
                mixed = path.stem.endswith('_mix')
                sizes = [204, 6144, 8192, 9216, 10240, 25600, 26624, 35840, 60416, 355328]
                size = max(sizes) if mixed else int(path.stem.rsplit('_', 1)[1][:-2]) * 1024
                self.assertIn('16.0.0.1', str(doc))
                self.assertIn('16.0.255.199', str(doc))
                self.assertNotIn('10.0.0.1', str(doc))
                count = 1 if '_cps_' in path.name else 10
                client = next(p for p in programs if 'http' in p or
                              ('http2' in p and not p['http2']['server']))
                if path.name.startswith('https'):
                    self.assertFalse(client['tls']['resumption'])
                    self.assertTrue(client['tls']['verify'])
                    for program in programs:
                        self.assertEqual(program['tls']['cipher_suite'], 'TLS_AES_128_GCM_SHA256')
                else:
                    self.assertNotIn('tls', client)
                if 'http2' in client:
                    if mixed:
                        self.assertEqual(client['http2']['body_sizes'], sizes)
                        server = next(p for p in programs if 'http2' in p and p['http2']['server'])
                        self.assertEqual(server['http2']['body_sizes'], sizes)
                    else:
                        self.assertEqual(client['http2']['body_size'], size)
                    self.assertEqual(client['http2']['requests'], count)
                    self.assertEqual(client['http2']['concurrency'], 1)
                    if 'tls' in client:
                        self.assertEqual(client['tls']['alpn'], 'h2')
                else:
                    response = next(base64.b64decode(b) for b in doc['buf_list'] if base64.b64decode(b).startswith(b'HTTP/1.1'))
                    if mixed:
                        bodies = [base64.b64decode(b).split(b'\r\n\r\n', 1)[1] for b in doc['buf_list'] if base64.b64decode(b).startswith(b'HTTP/1.1')]
                        self.assertEqual([len(b) for b in bodies], sizes)
                    else:
                        self.assertEqual(len(response.split(b'\r\n\r\n', 1)[1]), size)
                    self.assertEqual(client['http']['responses'], count)
                    self.assertTrue(client['http']['transactions'])
                temp = doc['templates'][0]
                self.assertEqual(temp['client_template']['cps'], 1)
                for side in ('c_glob_info', 's_glob_info'):
                    tcp = doc[side]['tcp']
                    self.assertEqual(tcp['mss'], 1460)
                    self.assertEqual(tcp['initwnd'], 10)
                    self.assertEqual(tcp['rxbufsize'], 65535)
                    self.assertEqual(tcp['txbufsize'], 65535)

    def test_cipher_defaults_and_overrides_all_tls_profiles(self):
        for path in (ROOT / 'profiles/rfc9411').glob('https*_max_*.py'):
            for args, cipher, groups in (
                (['--version', '1.2'], 'ECDHE-ECDSA-AES128-GCM-SHA256', ['P-256']),
                (['--cipher-suite', 'TLS_AES_256_GCM_SHA384', '--groups', 'X25519'],
                 'TLS_AES_256_GCM_SHA384', ['X25519']),
                (['--version', '1.2', '--cipher-suite', 'ECDHE-RSA-AES128-GCM-SHA256'],
                 'ECDHE-RSA-AES128-GCM-SHA256', ['P-256']),
            ):
                with self.subTest(profile=path.name, args=args):
                    for program in self.load(path.name, args)['program_list']:
                        self.assertEqual(program['tls']['cipher_suite'], cipher)
                        self.assertEqual(program['tls']['groups'], groups)

    def test_cc_hold_and_no_delayed_ack_override(self):
        doc = self.load('https_max_cc_1kb.py')
        client = next(p for p in doc['program_list'] if 'http' in p)
        delays = [c for c in client['commands'] if c['name'] == 'delay']
        self.assertEqual(delays, [{'name': 'delay', 'usec': 30000000}])
        self.assertNotIn('delay_ack_msec', str(doc))
        self.assertEqual(doc['templates'][0]['client_template']['limit'], 60000000)

    def test_response_length_and_small_body(self):
        doc = self.load('https_max_tp_16kb.py', ['--response_size_kb', '0.015625', '--flow_size', '2'])
        responses = [base64.b64decode(b) for b in doc['buf_list']]
        response = next(b for b in responses if b.startswith(b'HTTP/1.1'))
        headers, body = response.split(b'\r\n\r\n', 1)
        self.assertEqual(len(body), 16)
        self.assertIn(b'Content-Length: 16', headers)

    def test_tls12_and_parallel_h2(self):
        doc = self.load('https2_max_tp_16kb.py', ['--version', '1.2', '--concurrency', '4'])
        client = next(p for p in doc['program_list'] if 'http2' in p and not p['http2']['server'])
        self.assertEqual(client['tls']['version'], '1.2')
        self.assertEqual(client['http2']['concurrency'], 4)

    def test_h2_cc_pacing_and_deadline(self):
        for name in ('http2_max_cc_1kb.py', 'https2_max_cc_1kb.py'):
            doc = self.load(name)
            client = next(p for p in doc['program_list'] if 'http2' in p and not p['http2']['server'])
            self.assertEqual(client['http2']['request_interval_ms'], 30000)
            self.assertEqual(client['http2']['final_hold_ms'], 30000)
            self.assertEqual(client['http2']['timeout_ms'], 330000)

    def test_each_profile_is_standalone(self):
        import shutil
        for entry in (ROOT / 'profiles/rfc9411').glob('*_max_*.py'):
            path = Path(self.tmp.name) / entry.name
            shutil.copyfile(entry, path)
            opts = []
            if entry.name.startswith('https'):
                opts = ['--cert', str(self.fixture), '--key', str(self.fixture), '--ca', str(self.fixture)]
            self.assertTrue(ASTFProfile.load(str(path), tunables=opts).to_json()['templates'])

    def test_invalid_workloads_rejected(self):
        for name, args in [
            ('http2_max_cps_1kb.py', ['--flow_size', '2']),
            ('http2_max_tp_16kb.py', ['--delay', '1']),
            ('http2_max_tp_16kb.py', ['--concurrency', '129']),
            ('http2_max_cc_1kb.py', ['--concurrency', '2']),
            ('http2_max_cc_1kb.py', ['--timeout_ms', '300000']),
            ('https_max_cc_1kb.py', ['--delay', '0']),
            ('https_max_cps_1kb.py', ['--response_size_kb', 'nan']),
            ('https_max_cps_1kb.py', ['--authority', 'bad\r\nHost']),
        ]:
            with self.subTest(name=name, args=args), contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises((Exception, SystemExit)):
                    self.load(name, args)

if __name__ == '__main__':
    unittest.main()
