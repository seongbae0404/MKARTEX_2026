import json
import tempfile
import unittest
from pathlib import Path
from cms_guard.lab import Lab, demo_config
from cms_guard.engine import run
from cms_guard.audit import audit_snapshot
from cms_guard.report import write_report, html_report
from cms_guard.llm import summary_payload
from cms_guard.benchmark import benchmark

class Workflows(unittest.TestCase):
    def test_fixed_lab_all_checks_pass(self):
        with Lab(vulnerable=False) as lab:
            report=run(demo_config(lab))
        self.assertEqual(report['summary']['fail'],0)
        self.assertEqual(report['summary']['error'],0)
        self.assertEqual(report['summary']['inconclusive'],0)
        self.assertGreater(report['summary']['pass'],10)
    def test_vulnerable_lab_detects_all_seeded_cases(self):
        with Lab(vulnerable=True) as lab:
            report=run(demo_config(lab))
        failed={r['target'] for r in report['results'] if r['status']=='fail'}
        self.assertTrue({'document','attachment','admin','revoked_session','upload','render'} <= failed)
    def test_snapshot_missing_not_pass(self):
        rows=audit_snapshot({})
        self.assertGreater(len(rows),5)
        self.assertTrue(all(r['status']=='manual' for r in rows))
    def test_snapshot_invalid_type_not_truthy(self):
        rows=audit_snapshot({'db':{'tls_required':'false'}})
        self.assertEqual(next(r for r in rows if r['target']=='db_tls_required')['status'],'inconclusive')
    def test_snapshot_false_detected(self):
        rows=audit_snapshot({'db':{'tls_required':False}})
        self.assertEqual(next(r for r in rows if r['target']=='db_tls_required')['status'],'fail')
    def test_html_escapes_untrusted_text(self):
        report={'summary':{'pass':1},'metrics':{},'results':[{'target':'<script>alert(1)</script>','role':'x','status':'pass','reason':'<img src=x>','evidence':{}}],'limitations':[]}
        page=html_report(report)
        self.assertNotIn('<script>alert',page);self.assertIn('&lt;script&gt;',page)
    def test_report_files_and_no_raw_material(self):
        with Lab() as lab: report=run(demo_config(lab))
        with tempfile.TemporaryDirectory() as temp:
            write_report(report,Path(temp))
            self.assertEqual(json.loads((Path(temp)/'report.json').read_text())['summary'],report['summary'])
            self.assertTrue((Path(temp)/'report.html').exists()); self.assertTrue((Path(temp)/'report.md').exists())
            for p in Path(temp).iterdir(): self.assertNotIn('Bearer',p.read_text())
    def test_llm_payload_aggregate_only(self):
        payload=summary_payload({'summary':{'fail':2},'metrics':{'requests':4},'results':[{'secret':'SECRET'}]})
        self.assertNotIn('SECRET',json.dumps(payload));self.assertIn('summary',payload)
    def test_benchmark_scores_seeded_checks(self):
        output=benchmark(1)
        self.assertEqual(output['precision'],1.0);self.assertEqual(output['recall'],1.0)
        self.assertEqual(output['false_positives'],0)
        self.assertEqual(output['cases'],12)

if __name__=='__main__': unittest.main()
