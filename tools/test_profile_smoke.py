#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Run workload profiles through an already built ASTF simulator, without a NIC."""
import argparse
from pathlib import Path
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def counter(log, name):
    match = re.search(r'^\s*' + re.escape(name) + r'\s*\|\s*(\d+)\s*\|', log, re.M)
    return int(match.group(1)) if match else 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cc-defaults', action='store_true', help='Use ten requests and 30-second holds instead of shortened CC')
    parser.add_argument('--named-groups', action='store_true', help='Exercise simulator template-group statistics')
    parser.add_argument('--trex', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True, help='New directory for text logs; no keys retained')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    scripts = args.trex.resolve() / 'scripts'
    failures = []
    with tempfile.TemporaryDirectory(prefix='trex-profile-smoke-') as tmp:
        tmp = Path(tmp)
        cert, key = tmp / 'cert.pem', tmp / 'key.pem'
        subprocess.run(['openssl', 'req', '-x509', '-newkey', 'ec', '-pkeyopt',
            'ec_paramgen_curve:P-256', '-nodes', '-keyout', str(key), '-out', str(cert),
            '-days', '1', '-subj', '/CN=localhost', '-addext', 'subjectAltName=DNS:localhost'],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for profile in sorted((ROOT / 'profiles/rfc9411').glob('*_max_*.py')):
            for version in (['1.2', '1.3'] if profile.name.startswith('https') else ['clear']):
                name = profile.stem + '-' + version
                source = profile
                if args.named_groups:
                    source = tmp / profile.name
                    source.write_text(profile.read_text().replace('template = ASTFTemplate(',
                        "template = ASTFTemplate(tg_name='smoke',"))
                cmd = ['./astf-sim', '-v', '-f', str(source), '-o', str(tmp / name)]
                opts = []
                if version != 'clear':
                    opts += ['--version', version, '--cert', str(cert), '--key', str(key), '--ca', str(cert)]
                expected = 1 if '_cps_' in profile.name else 10
                if '_cc_' in profile.name and not args.cc_defaults:
                    opts += ['--delay', '0.01', '--flow_size', '3']
                    expected = 3
                if opts:
                    cmd += ['-t'] + opts
                result = subprocess.run(cmd, cwd=scripts, capture_output=True, text=True, timeout=120)
                log = result.stdout + result.stderr
                (args.output / (name + '.log')).write_text(log)
                metric = 'tcps_http_responses' if profile.name.startswith('https_') else 'tcps_http2_responses'
                ok = result.returncode == 0 and counter(log, metric) == expected
                # The live/simulator table hides diagnostic *_count fields.
                ok = ok and counter(log, 'm_active_flows') == 0
                for error in ('tcps_http2_errors', 'tcps_http2_timeouts', 'tcps_tls_errors', 'tcps_http_errors'):
                    match = re.search(r'^\s*' + error + r'\s*\|\s*(\d+)\s*\|\s*(\d+)', log, re.M)
                    if match and (int(match.group(1)) or int(match.group(2))):
                        ok = False
                ok = ok and all(re.search(r'^\s*' + metric + r'\s*\|', log, re.M)
                                for metric in ('tcps_ttfb_avg_ms', 'tcps_ttlb_avg_ms'))
                if version != 'clear':
                    ok = ok and counter(log, 'tcps_tls_handshakes') == 1
                if not ok:
                    failures.append(name)
                print(('PASS: ' if ok else 'FAIL: ') + name, flush=True)
    if failures:
        raise SystemExit('Failed scenarios: ' + ', '.join(failures))


if __name__ == '__main__':
    main()
