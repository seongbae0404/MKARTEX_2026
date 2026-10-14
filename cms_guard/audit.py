"""Review operator-supplied policy assertions, not a live DB scanner."""
RULES={
    'db':{'tls_required':'DB 접속 TLS 필수','public_access_blocked':'DB 외부 접근 차단',
          'least_privilege':'서비스 계정 최소 권한','backups_encrypted':'백업 암호화'},
    'sso':{'mfa_enabled':'MFA 적용','redirect_uris_exact':'리다이렉트 URI 정확한 목록 사용',
           'pkce_s256_enforced':'PKCE S256 적용','revocation_tested':'퇴사·비활성 계정 세션 회수 검증'},
    'uploads':{'extension_allowlist':'파일 확장자 허용 목록','signature_validation':'파일 내용·형식 검증',
               'size_limit':'파일 크기 제한','outside_webroot':'실행 경로 외부에 저장','download_authz':'다운로드 권한 검사'},
    'content':{'contextual_encoding':'출력 문맥별 인코딩','sanitization':'허용 HTML 정제'},
}

def audit_snapshot(snapshot):
    from .engine import result
    rows=[]
    if not isinstance(snapshot,dict):
        return [result('snapshot','operator','error','설정 스냅샷은 JSON 객체여야 합니다.')]
    for section,rules in RULES.items():
        source=snapshot.get(section,{})
        for key,label in rules.items():
            value=source.get(key) if isinstance(source,dict) else 'invalid'
            if value is None: state='manual'; reason=label+': 자료가 없어 미점검입니다.'
            elif type(value) is not bool: state='inconclusive'; reason=label+': true/false/null 값이 필요합니다.'
            else: state='pass' if value else 'fail'; reason=label+(': 제공된 설정에서 충족.' if value else ': 제공된 설정에서 미충족.')
            rows.append(result(section+'_'+key,'operator',state,reason,source='operator_snapshot',live_verified=False))
    return rows
