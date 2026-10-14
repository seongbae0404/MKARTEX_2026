import copy
import json
import os
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import patch

from cms_guard.config import validate, ConfigError
from cms_guard.transport import Transport, ScopeError, BudgetError, allowed_ip
from cms_guard.engine import run

CANARY = 'CMS-GUARD-SYNTHETIC-8f14e45f'

class Handler(BaseHTTPRequestHandler):
    calls = []
    def log_message(self, *args): pass
    def do_GET(self):
        self.calls.append(self.path)
        token = self.headers.get('Authorization')
        if self.path == '/redirect':
            self.send_response(302); self.send_header('Location', '/secret'); self.end_headers(); return
        if self.path == '/large': body, status = b'X' * 70000, 200
        elif self.path == '/login': body, status = b'<html>Login</html>', 200
        elif self.path == '/broken': body, status = b'Unavailable', 503
        elif self.path == '/leak' or token == 'Bearer synthetic-a': body, status = CANARY.encode(), 200
        else: body, status = b'Forbidden', 403
        self.send_response(status); self.send_header('Content-Length', str(len(body))); self.end_headers()
        self.wfile.write(body)


def config(port, path='/doc'):
    origin = f'http://127.0.0.1:{port}'
    return {'version': 1, 'mode': 'lab', 'limits': {'rps': 50},
            'roles': {'anonymous': {}, 'employee': {'header': 'Authorization', 'env': 'GUARD_A', 'origin': origin}},
            'targets': [{'id': 'document', 'url': origin + path, 'canary': CANARY,
                         'access': {'employee': 'allow', 'anonymous': 'deny'}}]}

class CoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True); cls.thread.start()
    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown(); cls.server.server_close(); cls.thread.join()
    def setUp(self):
        self.env = patch.dict(os.environ, {'GUARD_A': 'Bearer synthetic-a'}); self.env.start()
        self.cfg = config(self.server.server_port); Handler.calls = []
    def tearDown(self): self.env.stop()
    def rows(self, path):
        self.cfg['targets'][0]['url'] = f'http://127.0.0.1:{self.server.server_port}{path}'
        return run(self.cfg)['results']
    def test_authorized_control_and_denial_pass(self):
        rows = self.rows('/doc'); self.assertEqual([r['status'] for r in rows], ['pass','pass'])
    def test_leaked_canary_is_failure(self):
        rows = self.rows('/leak'); self.assertEqual(rows[1]['status'], 'fail')
    def test_login_200_not_access_success(self):
        self.assertTrue(all(r['status'] == 'inconclusive' for r in self.rows('/login')))
    def test_server_error_is_not_safe(self):
        self.assertNotIn('pass', [r['status'] for r in self.rows('/broken')])
    def test_redirect_not_followed(self):
        self.rows('/redirect'); self.assertNotIn('/secret', Handler.calls)
    def test_exact_url_scope(self):
        t = Transport(validate(self.cfg))
        with self.assertRaises(ScopeError): t.request('http://127.0.0.1:1/not-configured', {})
    def test_request_budget(self):
        self.cfg['limits']['max_requests'] = 1
        report = run(self.cfg); self.assertEqual(report['metrics']['requests'], 1)
        self.assertEqual(report['results'][1]['status'], 'error')
    def test_large_response_inconclusive(self):
        self.assertTrue(all(r['status'] == 'inconclusive' for r in self.rows('/large')))
    def test_missing_credential_stops_before_requests(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ConfigError): run(self.cfg)
        self.assertEqual(Handler.calls, [])
    def test_credentials_bound_to_origin(self):
        self.cfg['roles']['employee']['origin'] = 'https://example.org'
        with self.assertRaises(ConfigError): validate(self.cfg)
    def test_remote_http_rejected(self):
        self.cfg['mode'] = 'remote'
        with self.assertRaises(ConfigError): validate(self.cfg)
    def test_unsafe_url_rejected(self):
        for suffix in ['/a#frag', '/a\nX-Test:yes']:
            c = copy.deepcopy(self.cfg); c['targets'][0]['url'] += suffix
            with self.assertRaises(ConfigError): validate(c)
    def test_ip_policy(self):
        self.assertFalse(allowed_ip('169.254.169.254', 'remote', ['0.0.0.0/0']))
        self.assertFalse(allowed_ip('127.0.0.1', 'remote', ['0.0.0.0/0']))
        self.assertFalse(allowed_ip('10.0.0.1', 'remote', []))
        self.assertTrue(allowed_ip('10.0.0.1', 'remote', ['10.0.0.0/24']))
        self.assertTrue(allowed_ip('127.0.0.1', 'lab', []))
    def test_report_excludes_secrets_body_url(self):
        report = json.dumps(run(self.cfg))
        for secret in [CANARY, 'synthetic-a', self.cfg['targets'][0]['url']]: self.assertNotIn(secret, report)
    def test_remote_post_blocked(self):
        t = Transport(validate(self.cfg))
        with self.assertRaises(ScopeError): t.request(self.cfg['targets'][0]['url'], {}, method='POST', body=b'x')
    def test_no_allow_control_rejected(self):
        self.cfg['targets'][0]['access'] = {'anonymous':'deny'}
        with self.assertRaises(ConfigError): validate(self.cfg)
    def test_invalid_limits_rejected(self):
        for value in [0,-1,True,float('nan')]:
            c=copy.deepcopy(self.cfg); c['limits']['rps']=value
            with self.assertRaises(ConfigError): validate(c)

if __name__ == '__main__': unittest.main()
