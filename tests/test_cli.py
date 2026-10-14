import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

class CLITests(unittest.TestCase):
    def call(self,*args):return subprocess.run([sys.executable,'-m','cms_guard',*args],capture_output=True,text=True,timeout=20)
    def test_demo_creates_reports(self):
        with tempfile.TemporaryDirectory() as d:
            r=self.call('demo','--output',d)
            self.assertEqual(r.returncode,0,r.stderr)
            data=json.loads((Path(d)/'report.json').read_text())
            self.assertEqual(data['summary']['fail'],0)
    def test_vulnerable_demo_exits_two(self):
        with tempfile.TemporaryDirectory() as d:
            r=self.call('demo','--vulnerable','--output',d)
            self.assertEqual(r.returncode,2,r.stderr)
    def test_invalid_json_no_traceback(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'bad.json';p.write_text('{broken')
            r=self.call('run',str(p),'--output',d)
            self.assertEqual(r.returncode,1);self.assertNotIn('Traceback',r.stderr)
    def test_snapshot_only_command(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'policy.json';p.write_text('{}')
            r=self.call('audit',str(p),'--output',str(Path(d)/'result'))
            self.assertEqual(r.returncode,3,r.stderr)
            data=json.loads((Path(d)/'result/report.json').read_text())
            self.assertEqual(data['metrics']['requests'],0)
    def test_validate_does_not_need_credentials(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'task.json';p.write_text(json.dumps({'version':1,'mode':'remote','roles':{'a':{'header':'Cookie','env':'NOT_SET_GUARD','origin':'https://example.invalid'}},'targets':[]}))
            r=self.call('validate',str(p));self.assertEqual(r.returncode,0,r.stderr)

if __name__=='__main__':unittest.main()
