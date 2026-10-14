"""Portable reports with no external assets or raw responses."""
import html
import json
import os
from pathlib import Path

LABEL={'pass':'기대 충족','fail':'위반 발견','inconclusive':'판정 보류','error':'실행 오류','manual':'미점검'}

def save_private(path,text):
    path=Path(path)
    fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_TRUNC,0o600)
    try:
        if hasattr(os,'fchmod'): os.fchmod(fd,0o600)
        with os.fdopen(fd,'w',encoding='utf-8') as stream: stream.write(text)
    except BaseException:
        try: os.close(fd)
        except OSError: pass
        raise

def html_report(report):
    esc=lambda x:html.escape(str(x),quote=True)
    cards=''.join(f'<div class="metric {esc(k)}"><span>{LABEL[k]}</span><strong>{v}</strong></div>' for k,v in report['summary'].items())
    rows=''.join(f'<tr data-status="{esc(r["status"])}"><td><b>{esc(r["target"])}</b><small>{esc(r["role"])}</small></td><td><span class="badge {esc(r["status"])}">{esc(LABEL.get(r["status"],r["status"]))}</span></td><td>{esc(r["reason"])}<details><summary>판정 근거</summary><pre>{esc(json.dumps(r["evidence"],ensure_ascii=False,indent=2))}</pre></details></td></tr>' for r in report['results'])
    metrics=report.get('metrics',{})
    notes=''.join('<li>'+esc(n)+'</li>' for n in report.get('limitations',[]))
    return '''<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; base-uri 'none'; form-action 'none'">
<title>CMS Guard Lite · 점검 보고서</title><style>
:root{font-family:system-ui,-apple-system,'Segoe UI',sans-serif;color:#17233d;background:#f4f6fa}*{box-sizing:border-box}body{margin:0}main{max-width:1160px;margin:auto;padding:48px 24px}header{display:flex;justify-content:space-between;align-items:start;border-bottom:1px solid #dce1eb;padding-bottom:24px}.eyebrow{color:#3862cf;font-size:12px;font-weight:800;letter-spacing:2px}h1{font-size:36px;margin:12px 0}p{line-height:1.7;color:#5d687d}.version{background:#e7edfc;color:#3459b2;padding:8px 14px;border-radius:20px;font-size:12px}.metrics{display:grid;grid-template-columns:repeat(5,1fr);gap:14px;margin:26px 0}.metric{border:1px solid #e1e6ef;border-top:3px solid #91a0ba;border-radius:10px;background:white;padding:18px}.metric span{color:#5d687d;font-size:13px}.metric strong{display:block;font-size:32px;margin-top:8px}.metric.fail{border-top-color:#d74759}.metric.pass{border-top-color:#269579}.metric.error{border-top-color:#c17b24}.toolbar{display:flex;gap:12px;margin:24px 0 14px}input,select{border:1px solid #d7dfed;border-radius:6px;padding:11px;background:white;font:inherit}input{flex:1}table{width:100%;border-collapse:collapse;background:white;border:1px solid #e1e6ef}th{text-align:left;background:#edf1f8;font-size:12px;color:#61708a;padding:13px 18px}td{padding:18px;border-top:1px solid #edf0f5;vertical-align:top;font-size:14px}small{display:block;margin-top:7px;color:#76829a}td:first-child{width:24%}.badge{white-space:nowrap;border-radius:20px;padding:5px 10px;background:#edf0f5;font-size:12px}.badge.pass{background:#e3f5ee;color:#197559}.badge.fail{background:#ffeaec;color:#ae3044}.badge.error{background:#fff0db;color:#9c641c}details{margin-top:12px;color:#687690}summary{cursor:pointer;font-size:12px}pre{white-space:pre-wrap;font-size:12px}aside{margin-top:28px;background:#eaf0fb;padding:18px 24px;border-radius:10px;font-size:13px;line-height:1.8}footer{font-size:12px;color:#7d889c;margin-top:22px}[hidden]{display:none}@media(max-width:700px){main{padding:24px 12px}h1{font-size:27px}.metrics{grid-template-columns:repeat(2,1fr)}td,th{padding:12px 8px}.toolbar{flex-direction:column}}
</style><main><header><div><div class="eyebrow">CMS GUARD LITE / RESEARCH EDITION</div><h1>직원용 CMS 점검 보고서</h1><p>계정별 접근 결과와 검증 근거를 한곳에서 확인하세요.</p></div><span class="version">v0.1.0</span></header>''' + f'''
<div class="metrics">{cards}</div><p>HTTP 요청 <b>{esc(metrics.get('requests',0))}</b>회 · 실행 <b>{esc(metrics.get('duration_seconds',0))}</b>초 · {esc(report.get('created_at',''))}</p>
<div class="toolbar"><input id="search" aria-label="결과 검색" placeholder="대상 또는 판정 내용 검색"><select id="filter" aria-label="상태 필터"><option value="">모든 결과</option>''' + ''.join(f'<option value="{k}">{v}</option>' for k,v in LABEL.items()) + f'''</select></div>
<table><thead><tr><th>점검 대상 / 역할</th><th>결과</th><th>설명과 근거</th></tr></thead><tbody>{rows}</tbody></table><aside><b>보고서 읽는 법</b><ul>{notes}</ul>‘기대 충족’은 이 사례의 결과입니다. 설정 검토는 실제 동작 검증과 구분됩니다.</aside><footer>원문 · 인증 값 · 실제 URL은 보고서에 포함하지 않습니다. 별칭에도 기밀 정보를 넣지 마세요.</footer></main>''' + '''<script>
const q=document.querySelector('#search'),f=document.querySelector('#filter');function apply(){for(const row of document.querySelectorAll('tbody tr'))row.hidden=Boolean((f.value&&row.dataset.status!==f.value)||!row.textContent.toLowerCase().includes(q.value.toLowerCase()));}q.addEventListener('input',apply);f.addEventListener('change',apply);
</script></html>'''

def write_report(report,directory):
    d=Path(directory); d.mkdir(parents=True,exist_ok=True,mode=0o700)
    save_private(d/'report.json',json.dumps(report,ensure_ascii=False,indent=2))
    save_private(d/'report.html',html_report(report))
    lines=['# CMS Guard Lite 점검 결과','', '지정 사례만 평가하며 서비스 전체의 안전을 보장하지 않습니다.','']
    for r in report['results']:
        lines.extend([f'## {r["target"]} / {r["role"]}',f'- 결과: {LABEL[r["status"]]}',f'- 설명: {r["reason"]}',f'- 근거: `{json.dumps(r["evidence"],ensure_ascii=False)}`',''])
    save_private(d/'report.md','\n'.join(lines))
    return d/'report.html'
