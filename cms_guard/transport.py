"""Small HTTP transport: exact scope, pinned DNS, no redirects or proxies."""
import http.client
import ipaddress
import socket
import ssl
import time
import threading
import queue
from dataclasses import dataclass
from urllib.parse import urlsplit

class ScopeError(ValueError): pass
class BudgetError(RuntimeError): pass

@dataclass
class Response:
    status: int
    body: bytes
    headers: dict
    truncated: bool
    elapsed_ms: float

def allowed_ip(value,mode,networks):
    ip=ipaddress.ip_address(value)
    if mode=='lab': return ip == ipaddress.ip_address('127.0.0.1')
    if ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_unspecified or ip.is_reserved: return False
    return ip.is_global or any(ip in ipaddress.ip_network(n) for n in networks)

def resolve(host, port, timeout):
    answers=queue.Queue(maxsize=1)
    def work():
        try: answers.put((socket.getaddrinfo(host,port,type=socket.SOCK_STREAM),None))
        except OSError as exc: answers.put((None,exc))
    threading.Thread(target=work,daemon=True).start()
    try: records,error=answers.get(timeout=max(.001,timeout))
    except queue.Empty: raise BudgetError('DNS timeout') from None
    if error: raise error
    return list(dict.fromkeys(x[4][0] for x in records))

def expire_socket(sock):
    try: sock.shutdown(socket.SHUT_RDWR)
    except OSError: pass

class Transport:
    def __init__(self,config):
        self.config=config; self.limits=config['limits']; self.start=time.monotonic(); self.last=None; self.requests=0
        self.context=ssl.create_default_context()
    def request(self,url,headers,method='GET',body=None):
        if url not in self.config['_urls']: raise ScopeError('URL outside exact scope')
        p=urlsplit(url)
        if method!='GET' and not (method=='POST' and self.config['mode']=='lab' and p.hostname=='127.0.0.1' and p.path in ('/lab/upload','/lab/render') and not p.query): raise ScopeError('Method outside scope')
        if self.requests>=self.limits['max_requests']: raise BudgetError('Request budget exhausted')
        end=self.start+self.limits['total_seconds']
        delay=0 if self.last is None else max(0,1/self.limits['rps']-(time.monotonic()-self.last))
        if time.monotonic()+delay>=end: raise BudgetError('Time budget exhausted')
        if delay: time.sleep(delay)
        begin=time.monotonic(); deadline=min(end,begin+self.limits['timeout'])
        port=p.port or (443 if p.scheme=='https' else 80)
        # Resolve once, reject mixed safe/unsafe answers, connect to a numeric address.
        ips=resolve(p.hostname,port,deadline-time.monotonic())
        if not ips or any(not allowed_ip(ip,self.config['mode'],self.config['allowed_networks']) for ip in ips): raise ScopeError('Resolved IP outside network policy')
        if time.monotonic()>=deadline: raise BudgetError('DNS consumed request budget')
        sock=None; conn=None; response=None; timer=None
        self.requests+=1; self.last=time.monotonic()
        try:
            sock=socket.create_connection((ips[0],port),timeout=max(.001,deadline-time.monotonic()))
            if p.scheme=='https':
                sock.settimeout(max(.001,deadline-time.monotonic()))
                sock=self.context.wrap_socket(sock,server_hostname=p.hostname)
            timer=threading.Timer(max(.001,deadline-time.monotonic()),expire_socket,args=(sock,)); timer.daemon=True; timer.start()
            conn=http.client.HTTPConnection(p.hostname,port,timeout=self.limits['timeout']); conn.sock=sock
            safe_headers={'User-Agent':'CMS-Guard-Lite/0.1','Accept-Encoding':'identity','Connection':'close'}|headers
            sock.settimeout(max(.001,deadline-time.monotonic()))
            conn.request(method,(p.path or '/')+('?' + p.query if p.query else ''),body=body,headers=safe_headers)
            sock.settimeout(max(.001,deadline-time.monotonic()))
            response=conn.getresponse(); chunks=[]; remaining=self.limits['max_bytes']+1
            while remaining and not response.isclosed():
                left=deadline-time.monotonic()
                if left<=0: raise BudgetError('Response time budget exhausted')
                sock.settimeout(left)
                block=response.read1(min(8192,remaining))
                if not block: break
                chunks.append(block); remaining-=len(block)
            data=b''.join(chunks)
            if time.monotonic()>=deadline: raise BudgetError('Request deadline exceeded')
            if len(data)<=self.limits['max_bytes'] and response.length not in (None,0):
                raise http.client.IncompleteRead(data)
            # Only the small header subset used by checks survives the transport.
            selected={k.lower():v for k,v in response.getheaders() if k.lower() in ('content-type','content-security-policy','strict-transport-security','x-content-type-options','cache-control')}
            return Response(response.status,data[:self.limits['max_bytes']],selected,len(data)>self.limits['max_bytes'],round((time.monotonic()-begin)*1000,2))
        finally:
            if timer: timer.cancel()
            if response: response.close()
            if conn: conn.close()
            elif sock: sock.close()
