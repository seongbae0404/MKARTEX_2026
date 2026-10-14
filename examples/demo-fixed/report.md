# CMS Guard Lite 점검 결과

지정 사례만 평가하며 서비스 전체의 안전을 보장하지 않습니다.

## document / employee_a
- 결과: 기대 충족
- 설명: 허용 계정의 테스트 자료 열람을 확인했습니다.
- 근거: `{"http_status": 200, "canary_seen": true, "truncated": false, "elapsed_ms": 1.93}`

## document / employee_b
- 결과: 기대 충족
- 설명: 양성 대조군 성공 후 접근 거부를 확인했습니다.
- 근거: `{"http_status": 403, "canary_seen": false, "truncated": false, "elapsed_ms": 1.55}`

## document / anonymous
- 결과: 기대 충족
- 설명: 양성 대조군 성공 후 접근 거부를 확인했습니다.
- 근거: `{"http_status": 403, "canary_seen": false, "truncated": false, "elapsed_ms": 1.31}`

## attachment / employee_a
- 결과: 기대 충족
- 설명: 허용 계정의 테스트 자료 열람을 확인했습니다.
- 근거: `{"http_status": 200, "canary_seen": true, "truncated": false, "elapsed_ms": 1.57}`

## attachment / employee_b
- 결과: 기대 충족
- 설명: 양성 대조군 성공 후 접근 거부를 확인했습니다.
- 근거: `{"http_status": 403, "canary_seen": false, "truncated": false, "elapsed_ms": 1.66}`

## attachment / anonymous
- 결과: 기대 충족
- 설명: 양성 대조군 성공 후 접근 거부를 확인했습니다.
- 근거: `{"http_status": 403, "canary_seen": false, "truncated": false, "elapsed_ms": 1.21}`

## admin / admin
- 결과: 기대 충족
- 설명: 허용 계정의 테스트 자료 열람을 확인했습니다.
- 근거: `{"http_status": 200, "canary_seen": true, "truncated": false, "elapsed_ms": 1.39}`

## admin / employee_a
- 결과: 기대 충족
- 설명: 양성 대조군 성공 후 접근 거부를 확인했습니다.
- 근거: `{"http_status": 403, "canary_seen": false, "truncated": false, "elapsed_ms": 1.26}`

## revoked_session / employee_a
- 결과: 기대 충족
- 설명: 허용 계정의 테스트 자료 열람을 확인했습니다.
- 근거: `{"http_status": 200, "canary_seen": true, "truncated": false, "elapsed_ms": 1.69}`

## revoked_session / revoked
- 결과: 기대 충족
- 설명: 양성 대조군 성공 후 접근 거부를 확인했습니다.
- 근거: `{"http_status": 403, "canary_seen": false, "truncated": false, "elapsed_ms": 1.39}`

## upload / lab
- 결과: 기대 충족
- 설명: 로컬 실험의 정상 파일 수락·금지 형식 거부를 확인했습니다.
- 근거: `{"control_status": 201, "probe_status": 415}`

## render / lab
- 결과: 기대 충족
- 설명: 로컬 HTML 텍스트 문맥의 이스케이프를 확인했습니다.
- 근거: `{"http_status": 200}`
