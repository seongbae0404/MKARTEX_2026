# CMS Guard Lite 점검 결과

지정 사례만 평가하며 서비스 전체의 안전을 보장하지 않습니다.

## document / employee_a
- 결과: 기대 충족
- 설명: 허용 계정의 테스트 자료 열람을 확인했습니다.
- 근거: `{"http_status": 200, "canary_seen": true, "truncated": false, "elapsed_ms": 2.0}`

## document / employee_b
- 결과: 위반 발견
- 설명: 접근 불가 계정에 테스트 자료 표식이 반환됐습니다.
- 근거: `{"http_status": 200, "canary_seen": true, "truncated": false, "elapsed_ms": 1.46}`

## document / anonymous
- 결과: 위반 발견
- 설명: 접근 불가 계정에 테스트 자료 표식이 반환됐습니다.
- 근거: `{"http_status": 200, "canary_seen": true, "truncated": false, "elapsed_ms": 1.95}`

## attachment / employee_a
- 결과: 기대 충족
- 설명: 허용 계정의 테스트 자료 열람을 확인했습니다.
- 근거: `{"http_status": 200, "canary_seen": true, "truncated": false, "elapsed_ms": 1.63}`

## attachment / employee_b
- 결과: 위반 발견
- 설명: 접근 불가 계정에 테스트 자료 표식이 반환됐습니다.
- 근거: `{"http_status": 200, "canary_seen": true, "truncated": false, "elapsed_ms": 1.47}`

## attachment / anonymous
- 결과: 위반 발견
- 설명: 접근 불가 계정에 테스트 자료 표식이 반환됐습니다.
- 근거: `{"http_status": 200, "canary_seen": true, "truncated": false, "elapsed_ms": 1.31}`

## admin / admin
- 결과: 기대 충족
- 설명: 허용 계정의 테스트 자료 열람을 확인했습니다.
- 근거: `{"http_status": 200, "canary_seen": true, "truncated": false, "elapsed_ms": 1.39}`

## admin / employee_a
- 결과: 위반 발견
- 설명: 접근 불가 계정에 테스트 자료 표식이 반환됐습니다.
- 근거: `{"http_status": 200, "canary_seen": true, "truncated": false, "elapsed_ms": 1.33}`

## revoked_session / employee_a
- 결과: 기대 충족
- 설명: 허용 계정의 테스트 자료 열람을 확인했습니다.
- 근거: `{"http_status": 200, "canary_seen": true, "truncated": false, "elapsed_ms": 1.3}`

## revoked_session / revoked
- 결과: 위반 발견
- 설명: 접근 불가 계정에 테스트 자료 표식이 반환됐습니다.
- 근거: `{"http_status": 200, "canary_seen": true, "truncated": false, "elapsed_ms": 1.21}`

## upload / lab
- 결과: 위반 발견
- 설명: 로컬 실험에서 허용하지 않은 파일 형식을 수락했습니다.
- 근거: `{"control_status": 201, "probe_status": 201}`

## render / lab
- 결과: 위반 발견
- 설명: 로컬 HTML 문맥에서 무해한 태그가 이스케이프 없이 반환됐습니다.
- 근거: `{"http_status": 200}`
