# SPDX-License-Identifier: Apache-2.0
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
def sha(b): return hashlib.sha256(b).hexdigest()

class ApplyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root / 'extension'; self.repo.mkdir()
        shutil.copytree(ROOT / 'tools', self.repo / 'tools', ignore=shutil.ignore_patterns('__pycache__'))
        (self.repo / 'patches').mkdir()
        self.target = self.root / 'trex'; self.target.mkdir()
        (self.target / 'VERSION').write_text('v3.06\n')
        (self.target / 'a.txt').write_text('before\n')
        patch = ('diff --git a/a.txt b/a.txt\n--- a/a.txt\n+++ b/a.txt\n@@ -1 +1 @@\n-before\n+after\n'
                 'diff --git a/new/b.txt b/new/b.txt\nnew file mode 100644\n--- /dev/null\n+++ b/new/b.txt\n@@ -0,0 +1 @@\n+added\n')
        (self.repo / 'patches/one.patch').write_text(patch)
        (self.repo / 'patches/series').write_text('one.patch\n')
        manifest = dict(schema=1, patches=[dict(path='one.patch',sha256=sha(patch.encode()))], files=[
            dict(path='a.txt',base_sha256=sha(b'before\n'),result_sha256=sha(b'after\n'),patch='one.patch'),
            dict(path='new/b.txt',base_sha256=None,result_sha256=sha(b'added\n'),patch='one.patch')])
        (self.repo / 'patches/manifest.json').write_text(json.dumps(manifest))
    def run_apply(self, *args):
        return subprocess.run([sys.executable,str(self.repo/'tools/apply.py'),str(self.target),*args],capture_output=True,text=True)
    def test_dry_run_then_apply_and_repeat(self):
        self.assertEqual(self.run_apply('--check').returncode,0)
        self.assertEqual((self.target/'a.txt').read_text(),'before\n')
        self.assertFalse((self.target/'new').exists())
        self.assertEqual(self.run_apply().returncode,0)
        self.assertEqual(self.run_apply('--verify').returncode,0)
        self.assertNotEqual(self.run_apply().returncode,0)
        self.assertEqual((self.target/'a.txt').read_text(),'after\n')
    def test_modified_base_rejected_before_new_files(self):
        (self.target/'a.txt').write_text('user changes\n')
        self.assertNotEqual(self.run_apply().returncode,0)
        self.assertEqual((self.target/'a.txt').read_text(),'user changes\n')
        self.assertFalse((self.target/'new').exists())
    def test_added_file_collision_rejected(self):
        (self.target/'new').mkdir(); (self.target/'new/b.txt').write_text('user data\n')
        self.assertNotEqual(self.run_apply().returncode,0)
        self.assertEqual((self.target/'a.txt').read_text(),'before\n')
    def test_symlink_parent_rejected(self):
        outside=self.root/'outside';outside.mkdir()
        (self.target/'new').symlink_to(outside, target_is_directory=True)
        self.assertNotEqual(self.run_apply().returncode,0)
        self.assertEqual(list(outside.iterdir()),[])
        self.assertEqual((self.target/'a.txt').read_text(),'before\n')
    def test_tampered_patch_rejected(self):
        with (self.repo/'patches/one.patch').open('a') as f: f.write('tampering\n')
        self.assertNotEqual(self.run_apply().returncode,0)
        self.assertEqual((self.target/'a.txt').read_text(),'before\n')

    def test_regenerate_existing_and_added_paths(self):
        dev = self.root / 'dev'
        shutil.copytree(self.target, dev)
        (dev / 'a.txt').write_text('updated without newline')
        (dev / 'new').mkdir()
        (dev / 'new/b.txt').write_text('added\n')
        (dev / 'c.txt').write_text('explicit new file\n')
        result = subprocess.run([sys.executable, str(self.repo / 'tools/regenerate.py'),
            '--base', str(self.target), '--modified', str(dev),
            '--add', 'one.patch:c.txt'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.run_apply().returncode, 0)
        self.assertEqual(self.run_apply('--verify').returncode, 0)
        self.assertEqual((self.target / 'a.txt').read_bytes(), (dev / 'a.txt').read_bytes())
        self.assertEqual((self.target / 'c.txt').read_bytes(), (dev / 'c.txt').read_bytes())

if __name__ == '__main__': unittest.main()
