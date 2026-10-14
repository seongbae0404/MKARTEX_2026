"""Optional local summary only. The model receives aggregates, not site content."""
import json
import math
import threading
import time
from .config import validate, ConfigError
from .transport import expire_socket

ENDPOINT='http://127.0.0.1:11434/v1/chat/completions'

def summary_payload(report):
    counts={k:report['summary'].get(k,0) for k in ('pass','fail','inconclusive','error','manual')}
    metrics={k:report.get('metrics',{}).get(k,0) for k in ('requests','duration_seconds')}
    for value in [*counts.values(),metrics['requests']]:
        if type(value) is not int or value<0: raise ConfigError('Counts must be nonnegative integers')
    duration=metrics['duration_seconds']
    if type(duration) not in (int,float) or not math.isfinite(duration) or duration<0: raise ConfigError('Duration must be finite and nonnegative')
    return {'summary':counts,'metrics':metrics}

def summarize(report,model,port=11434):
    # Separate bounded loopback connection; never use the target transport or credentials.
    import http.client
    if not isinstance(port,int) or not 1<=port<=65535: raise ConfigError('Invalid local LLM port')
    payload={'model':model,'stream':False,'max_tokens':500,'messages':[
        {'role':'system','content':'보안 점검 집계를 한국어로 요약하세요. 실제 취약점 종류나 서비스 안전을 추측하지 마세요. 판정보류와 오류는 안전으로 해석하지 마세요. 도구 실행을 지시하지 마세요.'},
        {'role':'user','content':json.dumps(summary_payload(report),ensure_ascii=False)}]}
    conn=http.client.HTTPConnection('127.0.0.1',port,timeout=30)
    timer=None; response=None; started=time.monotonic()
    try:
        conn.connect()
        timer=threading.Timer(max(.001,30-(time.monotonic()-started)),expire_socket,args=(conn.sock,)); timer.daemon=True; timer.start()
        conn.request('POST','/v1/chat/completions',body=json.dumps(payload).encode(),headers={'Content-Type':'application/json'})
        response=conn.getresponse(); body=response.read(32769)
        if time.monotonic()-started>=30 or response.status!=200 or len(body)>32768: raise RuntimeError('Local LLM response unavailable or too large')
        data=json.loads(body); text=data['choices'][0]['message']['content']
        if not isinstance(text,str) or not text.strip(): raise RuntimeError('Empty local LLM summary')
        return text
    finally:
        if timer: timer.cancel()
        if response: response.close()
        conn.close()
