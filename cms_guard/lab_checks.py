import http.client
"""Only the bundled local fixture protocol; no remote upload or injection."""
import html
import json
from .engine import result

def lab_check(target,transport):
    def post(data):
        return transport.request(target['url'],{'Content-Type':'application/json'},'POST',json.dumps(data).encode())
    try:
        if target['kind']=='lab_upload':
            good=post({'filename':'sample.txt','content':'Synthetic upload control'})
            bad=post({'filename':'sample.bin','content':'Harmless disallowed-extension sample'})
            if good.truncated or bad.truncated or good.status!=201:
                status,reason='inconclusive','정상 업로드 대조군 또는 응답이 확인되지 않았습니다.'
            elif 200<=bad.status<300:
                status,reason='fail','로컬 실험에서 허용하지 않은 파일 형식을 수락했습니다.'
            elif bad.status in (400,413,415,422):
                status,reason='pass','로컬 실험의 정상 파일 수락·금지 형식 거부를 확인했습니다.'
            else: status,reason='inconclusive','파일 형식 거부 여부를 확인하지 못했습니다.'
            return [result(target['id'],'lab',status,reason,control_status=good.status,probe_status=bad.status)]
        probe='<span data-cms-guard="synthetic">CMS-GUARD-TEXT</span>'
        resp=post({'text':probe}); body=resp.body.decode('utf-8',errors='replace')
        if resp.truncated or resp.status!=200: status,reason='inconclusive','렌더링 응답을 확인하지 못했습니다.'
        elif probe in body: status,reason='fail','로컬 HTML 문맥에서 무해한 태그가 이스케이프 없이 반환됐습니다.'
        elif html.escape(probe) in body: status,reason='pass','로컬 HTML 텍스트 문맥의 이스케이프를 확인했습니다.'
        else: status,reason='inconclusive','예상한 원문·이스케이프 표식을 찾지 못했습니다.'
        return [result(target['id'],'lab',status,reason,http_status=resp.status)]
    except (OSError,ValueError,RuntimeError,http.client.HTTPException) as exc:
        return [result(target['id'],'lab','error','로컬 검증 실패',error_type=type(exc).__name__)]
