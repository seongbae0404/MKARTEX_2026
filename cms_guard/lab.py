"""Ephemeral loopback-only CMS fixture with synthetic data and credentials."""
import html
import json
import os
import secrets
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

TOKENS={'CMS_GUARD_LAB_A':'Bearer lab-employee-a','CMS_GUARD_LAB_B':'Bearer lab-employee-b',
        'CMS_GUARD_LAB_ADMIN':'Bearer lab-admin','CMS_GUARD_LAB_REVOKED':'Bearer lab-revoked'}

class Lab:
    def __init__(self,vulnerable=False):
        self.vulnerable=vulnerable; self.canary='CMS-GUARD-'+secrets.token_hex(16)
        self.server=None; self.previous={}
    def __enter__(self):
        lab=self
        class Handler(BaseHTTPRequestHandler):
            def log_message(self,*args): pass
            def reply(self,status,body,ctype='text/plain; charset=utf-8'):
                data=body.encode(); self.send_response(status)
                self.send_header('Content-Type',ctype); self.send_header('Content-Length',str(len(data)))
                self.send_header('X-Content-Type-Options','nosniff'); self.send_header('Cache-Control','no-store')
                self.end_headers(); self.wfile.write(data)
            def do_GET(self):
                token=self.headers.get('Authorization','')
                if self.path not in ('/doc','/file','/admin','/session'): return self.reply(404,'Not found')
                required='Bearer lab-admin' if self.path=='/admin' else 'Bearer lab-employee-a'
                if token==required or lab.vulnerable: return self.reply(200,lab.canary)
                return self.reply(403,'Forbidden')
            def do_POST(self):
                try:
                    n=int(self.headers.get('Content-Length','0'))
                    if not 0<n<=4096: return self.reply(413,'Too large')
                    data=json.loads(self.rfile.read(n))
                except (ValueError,UnicodeError): return self.reply(400,'Bad request')
                if self.path=='/lab/upload':
                    if not lab.vulnerable and (data.get('filename')!='sample.txt' or len(data.get('content',''))>1024): return self.reply(415,'Rejected')
                    return self.reply(201,'Accepted synthetic file')
                if self.path=='/lab/render':
                    text=data.get('text','')
                    return self.reply(200,text if lab.vulnerable else html.escape(text), 'text/html; charset=utf-8')
                return self.reply(404,'Not found')
        self.server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True); self.thread.start()
        self.origin=f'http://127.0.0.1:{self.server.server_port}'
        for name,value in TOKENS.items(): self.previous[name]=os.environ.get(name); os.environ[name]=value
        return self
    def __exit__(self,*args):
        self.server.shutdown(); self.server.server_close(); self.thread.join()
        for name,value in self.previous.items():
            if value is None: os.environ.pop(name,None)
            else: os.environ[name]=value

def demo_config(lab):
    roles={'anonymous':{}}
    for name,env in [('employee_a','CMS_GUARD_LAB_A'),('employee_b','CMS_GUARD_LAB_B'),('admin','CMS_GUARD_LAB_ADMIN'),('revoked','CMS_GUARD_LAB_REVOKED')]:
        roles[name]={'header':'Authorization','env':env,'origin':lab.origin}
    targets=[]
    for id_,path in [('document','/doc'),('attachment','/file')]:
        targets.append({'id':id_,'url':lab.origin+path,'canary':lab.canary,'access':{'employee_a':'allow','employee_b':'deny','anonymous':'deny'}})
    targets.extend([
        {'id':'admin','url':lab.origin+'/admin','canary':lab.canary,'access':{'admin':'allow','employee_a':'deny'}},
        {'id':'revoked_session','kind':'session','url':lab.origin+'/session','canary':lab.canary,'access':{'employee_a':'allow','revoked':'deny'},'revocation_confirmed':True},
        {'id':'upload','kind':'lab_upload','url':lab.origin+'/lab/upload'},
        {'id':'render','kind':'lab_render','url':lab.origin+'/lab/render'}])
    return {'version':1,'mode':'lab','limits':{'rps':50},'roles':roles,'targets':targets}
