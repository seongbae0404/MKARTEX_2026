import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from cms_guard.llm import summary_payload,summarize
from cms_guard.config import ConfigError

class LLMTests(unittest.TestCase):
    def test_non_numeric_aggregate_rejected(self):
        for value in ['SECRET',{'raw':'secret'},float('nan'),True,-1]:
            with self.assertRaises(ConfigError):summary_payload({'summary':{'fail':value},'metrics':{}})
    def test_local_stub_receives_only_aggregates(self):
        requests=[]
        class Stub(BaseHTTPRequestHandler):
            def log_message(self,*a):pass
            def do_POST(self):
                requests.append(json.loads(self.rfile.read(int(self.headers['Content-Length']))))
                data=json.dumps({'choices':[{'message':{'content':'합성 요약입니다.'}}]}).encode()
                self.send_response(200);self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
        server=ThreadingHTTPServer(('127.0.0.1',0),Stub)
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        try:
            answer=summarize({'summary':{'fail':2},'metrics':{'requests':3},'results':[{'secret':'DO-NOT-SEND'}]},'fake-model',server.server_port)
            self.assertEqual(answer,'합성 요약입니다.')
            self.assertNotIn('DO-NOT-SEND',json.dumps(requests))
            self.assertEqual(len(requests),1)
        finally:server.shutdown();server.server_close();thread.join()
