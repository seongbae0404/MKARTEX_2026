import http.client
"""Deterministic checks; an HTTP 200 alone never proves document access."""
import time
from datetime import datetime, timezone
from .config import validate, credentials
from .transport import Transport

def result(target,role,status,reason,**evidence):
    return {'target':target,'role':role,'status':status,'reason':reason,'evidence':evidence}

def access_check(t,transport,creds):
    observations={}; rows=[]
    for role in t['access']:
        try:
            resp=transport.request(t['url'],creds[role])
            observations[role]=(resp,t['canary'].encode() in resp.body,None)
        except (OSError,ValueError,RuntimeError,http.client.HTTPException) as exc:
            observations[role]=(None,False,type(exc).__name__)
    positive=any(resp is not None and 200<=resp.status<300 and marker and not resp.truncated
                 for role,(resp,marker,_) in observations.items() if t['access'][role]=='allow')
    for role,(resp,marker,error) in observations.items():
        if error:
            rows.append(result(t['id'],role,'error','요청을 완료하지 못했습니다.',error_type=error)); continue
        status='inconclusive'; reason='응답만으로 접근 여부를 확인할 수 없습니다.'
        if resp.truncated: reason='응답 크기 상한을 초과했습니다.'
        elif marker and t['access'][role]=='deny':
            status='fail'; reason='접근 불가 계정에 테스트 자료 표식이 반환됐습니다.'
        elif marker and 200<=resp.status<300:
            status='pass'; reason='허용 계정의 테스트 자료 열람을 확인했습니다.'
        elif positive and t['access'][role]=='deny' and resp.status in (401,403,404):
            status='pass'; reason='양성 대조군 성공 후 접근 거부를 확인했습니다.'
        elif not positive: reason='양성 대조군 열람이 확인되지 않았습니다. 계정·경로·표식을 확인하세요.'
        rows.append(result(t['id'],role,status,reason,http_status=resp.status,canary_seen=marker,truncated=resp.truncated,elapsed_ms=resp.elapsed_ms))
    return rows

def header_check(t,transport):
    try: resp=transport.request(t['url'],{})
    except (OSError,ValueError,RuntimeError,http.client.HTTPException) as exc: return [result(t['id'],'anonymous','error','헤더 조회 실패',error_type=type(exc).__name__)]
    if not 200<=resp.status<300: return [result(t['id'],'anonymous','inconclusive','리다이렉트·오류 응답의 헤더로 앱 전체 정책을 판정하지 않습니다.',http_status=resp.status)]
    missing=[]
    if t['url'].startswith('https:') and 'strict-transport-security' not in resp.headers: missing.append('HSTS')
    if resp.headers.get('x-content-type-options','').lower()!='nosniff': missing.append('nosniff')
    if 'text/html' in resp.headers.get('content-type','') and 'content-security-policy' not in resp.headers: missing.append('CSP')
    return [result(t['id'],'anonymous','inconclusive' if missing else 'pass','헤더 누락은 하드닝 검토 사항입니다. 취약점 확정이 아닙니다.' if missing else '확인 대상 헤더가 존재합니다. 정책 내용의 적절성은 별도 검토하세요.',missing=missing,http_status=resp.status)]

def run(raw, progress=None):
    from .audit import audit_snapshot
    from .lab_checks import lab_check
    c=validate(raw); creds=credentials(c); transport=Transport(c); start=time.monotonic(); rows=[]
    for target in c['targets']:
        if target['kind'] in ('access','session'): new=access_check(target,transport,creds)
        elif target['kind']=='headers': new=header_check(target,transport)
        else: new=lab_check(target,transport)
        rows.extend(new)
        if progress: progress(target['id'],new)
    if 'snapshot' in c: rows.extend(audit_snapshot(c['snapshot']))
    counts={s:sum(r['status']==s for r in rows) for s in ('pass','fail','inconclusive','error','manual')}
    return {'schema_version':1,'tool_version':'0.1.0','created_at':datetime.now(timezone.utc).isoformat(),
            'mode':c['mode'],'results':rows,'summary':counts,
            'metrics':{'requests':transport.requests,'duration_seconds':round(time.monotonic()-start,3),'llm_calls':0},
            'limitations':['지정된 사례만 평가합니다. 전체 서비스의 안전을 보장하지 않습니다.',
                            'SSO/MFA 로그인과 계정 무효화는 운영자가 준비합니다.',
                            '설정 스냅샷은 제공된 주장에 대한 검토이며 실제 서버 동작의 증명이 아닙니다.']}
