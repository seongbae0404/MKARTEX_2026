import copy
import json
import os
import socket
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from unittest.mock import patch
from cms_guard.config import validate,ConfigError
from cms_guard.engine import run
from cms_guard.transport import Transport,BudgetError
from test_core import config,Handler

class Edges(unittest.TestCase):
    def test_dns_timeout_enforced(self):
        c=validate(config(1234));c['limits']['timeout']=0.05
        def slow(*a,**k):time.sleep(.25);return []
        before=time.monotonic()
        with patch('socket.getaddrinfo',slow):
            with self.assertRaises(BudgetError): Transport(c).request(c['targets'][0]['url'],{})
        self.assertLess(time.monotonic()-before,.2)
    def test_session_rejects_anonymous_revoked_role(self):
        c=config(1234);c['targets'][0].update(kind='session',revocation_confirmed=True)
        with self.assertRaises(ConfigError):validate(c)
    def test_session_rejects_identical_credential_values(self):
        c=config(1234);c['roles']['old']={'header':'Authorization','env':'GUARD_OLD','origin':'http://127.0.0.1:1234'}
        c['targets'][0].update(kind='session',revocation_confirmed=True,access={'employee':'allow','old':'deny'})
        with patch.dict(os.environ,{'GUARD_A':'Bearer same','GUARD_OLD':'Bearer same'}):
            with self.assertRaises(ConfigError):run(c)
    def test_invalid_config_is_config_error(self):
        for bad in [None, [], 12, '<text>']:
            c=config(1234);c['targets'][0]['id']=bad
            with self.assertRaises(ConfigError):validate(c)
    def test_http_protocol_error_becomes_result(self):
        class Broken(BaseHTTPRequestHandler):
            def log_message(self,*a):pass
            def do_GET(self): self.connection.sendall(b'garbage\r\n\r\n');self.close_connection=True
        server=ThreadingHTTPServer(('127.0.0.1',0),Broken)
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        try:
            with patch.dict(os.environ,{'GUARD_A':'Bearer a'}):report=run(config(server.server_port))
            self.assertEqual(report['summary']['error'],2)
        finally:server.shutdown();server.server_close();thread.join()
    def test_slow_header_wall_deadline(self):
        class Slow(BaseHTTPRequestHandler):
            def log_message(self,*a):pass
            def do_GET(self):
                try:
                    for chunk in [b'HTTP/1.1 200 OK\r\n',b'X-1: a\r\n',b'X-2: a\r\n',b'Content-Length: 0\r\n\r\n']:
                        self.connection.sendall(chunk);time.sleep(.09)
                except OSError:pass
        server=ThreadingHTTPServer(('127.0.0.1',0),Slow)
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        try:
            c=validate(config(server.server_port));c['limits']['timeout']=.12
            before=time.monotonic()
            try:Transport(c).request(c['targets'][0]['url'],{})
            except Exception:pass
            self.assertLess(time.monotonic()-before,.25)
        finally:server.shutdown();server.server_close();thread.join()

    def test_partial_content_length_is_error(self):
        class Partial(BaseHTTPRequestHandler):
            def log_message(self,*a):pass
            def do_GET(self):
                self.connection.sendall(b'HTTP/1.1 200 OK\r\nContent-Length: 1000\r\nConnection: close\r\n\r\nCMS-GUARD-SYNTHETIC-8f14e45f')
                self.close_connection=True
        server=ThreadingHTTPServer(('127.0.0.1',0),Partial)
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        try:
            with patch.dict(os.environ,{'GUARD_A':'Bearer a'}):report=run(config(server.server_port))
            self.assertEqual(report['summary']['error'],2)
            self.assertEqual(report['summary']['pass'],0)
        finally:server.shutdown();server.server_close();thread.join()
