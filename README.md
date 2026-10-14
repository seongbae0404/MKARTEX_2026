# CMS Guard Lite

직원용 CMS의 문서·첨부파일·권한·세션을 지정된 테스트 사례로 점검하는 경량 연구용 프로젝트입니다. **Python 3.11 이상만 있으면 데모가 실행되며 런타임 외부 패키지는 없습니다.**

PentAGI의 작업·실행·기록·보고 구조를 참고한 **독립 구현**입니다. PentAGI를 그대로 줄인 포크나 동일 성능의 대체품은 아닙니다. 규칙 기반 검증이 판정을 담당하며 선택적인 로컬 AI는 결과 집계만 한국어로 요약합니다. 원본 에이전트의 임의 셸 실행·공격 체인은 구현하지 않습니다.

## 1분 데모

압축을 풀고 프로젝트 폴더에서 실행하세요. Windows에서는 `python` 대신 `py -3`도 가능합니다.

```bash
python -m cms_guard demo
```

가짜 CMS를 127.0.0.1의 임시 포트에서 시작하고 검사 후 종료합니다. `reports/demo/report.html`을 브라우저에서 열면 검색·상태 필터·판정 근거가 있는 한국어 대시보드가 나타납니다. JSON과 Markdown도 함께 저장됩니다. 이미 생성한 예시는 `examples/demo-fixed/`와 `examples/demo-vulnerable/`에 있습니다.

취약 모드와 비교:

```bash
python -m cms_guard demo --vulnerable --output reports/vulnerable
python -m cms_guard benchmark --repeats 3
python -m unittest discover -s tests -v
```

취약 모드 명령은 발견 사항이 있으므로 **종료 코드 2가 정상**입니다. 벤치마크는 동봉한 합성 사례만 평가합니다. PentAGI 대비 우수성을 증명하지 않습니다.

## 구현 범위

| 항목 | v0.1 구현 | 판정의 한계 |
|---|---|---|
| 문서·첨부파일 권한 | 지정 URL을 허용/비허용/미인증 역할로 조회 | 가짜 자료의 고유 표식이 필요. URL 수집·ID 열거 없음 |
| 관리자 권한 | 읽기 전용 관리자 테스트 리소스의 역할 비교 | 승인·수정·삭제 기능 자체는 실행하지 않음 |
| 세션 회수 | 활성 자격과 수동으로 회수한 이전 자격 비교 | SSO 로그인/MFA/계정 회수는 운영자가 준비 |
| 업로드 | 로컬 실험의 정상/금지 형식 비교, 설정 체크리스트 | 실제 CMS 업로드 API에 바로 연결하는 어댑터 없음 |
| 입력 처리 | 로컬 HTML 문맥에서 무해한 태그 escaping 확인 | 실제 브라우저 XSS 실행·다른 출력 문맥 검증 없음 |
| DB/SSO 정책 | 제공된 boolean 설정 스냅샷 검토 | DB 접속·SQL 실행·라이브 설정 수집 없음 |
| HTTP 헤더 | 지정 공개 페이지의 HSTS·CSP·nosniff 존재 검토 | 존재만으로 정책 효과·서비스 안전을 보장하지 않음 |
| AI | 로컬 OpenAI 호환 서버에 결과 개수·요청 수·시간만 전달 | 계획·도구 선택·공격 수행을 AI에 맡기지 않음 |

## 실제 CMS에 맞추기

외부에서 URL을 알면 접근 가능한 CMS도 지원합니다. 서버가 공개되어 있다는 사실과 문서가 공개되어 있다는 사실은 구분해야 합니다. 개발 과정에서 실제 회사 사이트를 요청하거나 검사하지 않았습니다.

1. 담당자와 합의한 **읽기 전용 테스트 문서·첨부파일**을 준비합니다. 실제 업무 자료 대신 가짜 보고서에 임의 표식을 넣으세요. PDF/압축 문서 안의 텍스트는 직접 검색하지 못하므로 처음에는 plain text 응답을 사용합니다.
2. `examples/remote.json`을 `config.local.json`으로 복사합니다. 도메인·정확한 테스트 URL·역할별 기대 권한을 수정합니다. 회사 주소와 식별 정보를 공개 저장소에 올리지 않습니다.
3. `canary`는 16~256 byte 고유 표식입니다. 문서 제목이나 사용자명이 아닌 임의 값을 사용하세요. 생성 예: `python -c "import secrets; print('CMS-GUARD-'+secrets.token_hex(16))"`.
4. 테스트 계정으로 정상 로그인하고, 조직에서 허용한 방식으로 발급한 세션 쿠키 또는 토큰을 환경 변수에 넣습니다. `.env` 자동 로딩은 하지 않습니다. 개인 운영 계정 대신 제한된 테스트 계정을 사용합니다.
5. URL은 로그인 시작 페이지가 아니라 **테스트 자료를 반환하는 정확한 조회 URL**입니다. 프런트엔드가 JavaScript로 내용을 불러오면 테스트용 조회 API를 지정합니다. 리다이렉트는 따라가지 않습니다.
6. 설정을 확인하고 실행합니다.

```bash
python -m cms_guard validate config.local.json
python -m cms_guard run config.local.json --output reports/first-run
```

Bash에서 값을 화면에 남기지 않고 입력:

```bash
read -rs -p '테스트 A 쿠키: ' CMS_GUARD_A_COOKIE
export CMS_GUARD_A_COOKIE
read -rs -p '테스트 B 쿠키: ' CMS_GUARD_B_COOKIE
export CMS_GUARD_B_COOKIE
```

PowerShell 7:

```powershell
$env:CMS_GUARD_A_COOKIE = Read-Host '테스트 A 쿠키' -MaskInput
$env:CMS_GUARD_B_COOKIE = Read-Host '테스트 B 쿠키' -MaskInput
```

`Cookie` 값은 `session=...` 형태의 전체 요청 쿠키 헤더입니다. Bearer 토큰은 역할의 `header`를 `Authorization`으로 바꾸고 환경 변수에 `Bearer ...`를 넣습니다. 인증은 역할의 `origin`과 일치하는 대상에만 적용합니다. SSO 도메인과 CMS 도메인은 별도 범위로 다룹니다. 로그인 URL의 `state`/`nonce`를 고정해 재사용하지 않습니다.

GET도 시스템에 따라 부작용이 있을 수 있습니다. 로그아웃·삭제·승인 같은 URL을 조회 대상으로 넣지 마세요. scope의 정확한 URL 목록은 코드로 강제하지만 네트워크 격리 자체를 대신하지는 않습니다.

## 세션 만료·퇴사자 계정 검사

관리자가 테스트 계정의 기존 세션을 로그아웃·비활성화하고, 회수가 반영되는 유예 시간을 확인한 다음 **회수 전 자격**을 별도 환경 변수로 준비하세요. 활성 대조군은 같은 문서를 볼 수 있는 다른 테스트 세션입니다. 프로그램이 계정을 비활성화하지 않습니다.

```json
{
  "id": "revoked_session",
  "kind": "session",
  "url": "https://cms.example.invalid/test-document/known-id",
  "canary": "RANDOM-SYNTHETIC-CANARY-HERE",
  "access": {"active": "allow", "revoked": "deny"},
  "revocation_confirmed": true
}
```

`active`와 `revoked`를 `roles`에 별도로 정의하세요. `revocation_confirmed`는 운영자의 확인값이지 자동 입증이 아닙니다. 역할의 접근 정책은 회사의 실제 정책으로 정해야 합니다.

## DB·SSO·파일 정책의 오프라인 검토

```bash
python -m cms_guard audit examples/snapshot.json --output reports/policy
```

스냅샷의 `null`은 미점검, `true`는 제공된 설정상 충족, `false`는 미충족입니다. 실제 설정이나 확인한 감사 자료를 근거로 값을 채우세요. true 입력만으로 실서비스의 보안이 증명되지는 않습니다. DB 사용자/비밀번호/연결 문자열은 필요하지 않습니다.

## 선택적 로컬 AI 요약

이미 운영 중인 Ollama 등 로컬 OpenAI 호환 서버와 설치한 모델을 사용합니다.

```bash
python -m cms_guard summarize reports/demo/report.json --model YOUR_LOCAL_MODEL --port 11434
```

`127.0.0.1`로만 연결합니다. 모델 이름은 사용자가 설치한 이름으로 바꿉니다. 원문, URL, 쿠키, 토큰, 대상 별칭, 개별 발견 내용은 전달하지 않고 집계만 보냅니다. 요약은 판정 근거가 아닙니다. 실제 모델 추론은 이 배포본 제작 시 실행하지 않았습니다.

## 제한·출력

- 기본 100요청 / 전체 120초 / 요청 5초 / 본문 64 KiB / 초당 2요청. config에서 낮출 수 있습니다.
- Remote는 HTTPS GET만 사용합니다. DNS 해석 후 IP를 검증하고 그 IP로 직접 연결하며 TLS 인증서와 호스트를 확인합니다. 프록시 환경 변수와 리다이렉트를 사용하지 않습니다.
- 기본 공인 IP만 허용합니다. 사설 HTTPS는 `allowed_networks`에 정확한 CIDR을 추가합니다. loopback/link-local/metadata 주소는 remote에서 차단합니다.
- `lab`의 HTTP와 POST는 루프백 및 정해진 실험 경로로 제한됩니다.
- 본문·URL·인증 헤더·표식은 보고서에 저장하지 않습니다. 대상/역할의 별칭에도 기밀 문자열을 넣지 마세요.
- 로컬 저장 권한은 POSIX에서 파일 0600입니다. Windows ACL은 별도로 관리해야 합니다.
- 과대 응답, 로그인 200, redirect, 오류, 대조군 실패는 안전으로 판정하지 않습니다.
- 종료 코드: 0=모든 지정 사례 충족, 1=실행 오류, 2=위반 발견, 3=판정보류/미점검, 130=사용자 중단. 오류가 있으면 1이 우선합니다.

## 구조와 연구

`cms_guard/`에 엔진, 네트워크, 정책, 보고서, 데모, 벤치마크가 분리되어 있습니다. [설계](docs/DESIGN.md), [구현 계획](docs/PLAN.md), [비교 실험 프로토콜](docs/BENCHMARK.md), [참고 프로젝트](REFERENCES.md), [검증 기록](docs/VALIDATION.md)을 읽어보세요.

## GitHub에 올리기

새 빈 저장소를 만든 뒤 이 폴더에서 아래처럼 업로드할 수 있습니다. `<YOUR_REPOSITORY_URL>`은 본인 저장소 주소로 바꿉니다.

```bash
git init
git add .
git commit -m "Initial CMS Guard Lite research prototype"
git branch -M main
git remote add origin <YOUR_REPOSITORY_URL>
git push -u origin main
```

`.gitignore`는 로컬 설정·보고서·환경 파일을 제외합니다. 공개 전 파일 목록을 확인하세요. CI는 Linux/Windows의 Python 3.11~3.13 테스트 구성을 포함합니다. CI 실행 결과는 아직 없습니다. MIT 라이선스이며 상류 프로젝트의 코드·프롬프트·화면 자산은 복사하지 않았습니다.
