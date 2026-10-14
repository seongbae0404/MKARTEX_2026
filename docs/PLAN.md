# CMS Guard Lite Implementation Plan

**Goal:** 직원용 CMS의 재현 가능한 경량 점검 코드와 로컬 실험을 제공한다.
**Architecture:** 명시적 작업 목록을 단일 실행기가 수행하고 구조화한 증거를 한국어 보고서로 만든다.
**Tech Stack:** Python 3.11+ standard library, unittest, JSON, HTML.
**Spec:** DESIGN.md

## Global Constraints
운영 대상 GET only, HTTPS, 정확한 URL scope, 인증 환경 변수, 리다이렉트 미추적, LLM 집계만 사용. 실제 회사 도메인 미포함.

## Review Focus
로그인 200 오인, 인증/원문 유출, DNS·리다이렉트 scope 이탈, 불완전 응답/오류의 안전 판정, 잘못 준비된 세션 테스트.

## Task 1: 설정·네트워크·권한 비교
- [x] tests/test_core.py에서 실제 루프백 서버를 대상으로 실패 테스트 작성 및 실행.
- [x] config.py, transport.py, engine.py 구현: validate(config), Transport.request(target, role), run(config).
- [x] 전체 unittest 실행.

## Task 2: 로컬 실험·정책·보고서·요약
- [x] tests/test_workflows.py: 정상/취약 실험, 스냅샷 unknown, 민감정보 제외, HTML escaping, benchmark 테스트 작성 및 실패 확인.
- [x] lab.py, audit.py, report.py, llm.py, benchmark.py, __main__.py 구현.
- [x] 전체 unittest, demo와 benchmark 명령 실행.

## Task 3: 문서·배포 패키지
- [x] 한국어 README, 설정 예시, 연구 프로토콜, 출처, MIT, CI 작성.
- [x] 독립 코드 리뷰 및 발견사항 회귀 테스트.
- [x] 최종 테스트와 zip 검증 후 제공.
