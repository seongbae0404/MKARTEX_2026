# 참고 프로젝트와 구현 경계

2026-10-12 GitHub 플러그인으로 아래 저장소의 README와 LICENSE를 확인했다. 이 프로젝트는 설명된 아키텍처에서 아이디어를 얻어 새로 작성했다. 상류 코드·프롬프트·로고·화면 자산을 복사하지 않았다. 상류의 기능·성능을 계승했다고 주장하지 않는다.

| 저장소 | 확인한 README 파일의 Git blob SHA (commit SHA 아님) |
|---|---|
| [vxcontrol/pentagi](https://github.com/vxcontrol/pentagi) | `731dfe269aabcfbdd01a2dd7c8c0b5b1b07542ae` |
| [Armur-Ai/Pentest-Swarm-AI](https://github.com/Armur-Ai/Pentest-Swarm-AI) | `b227836fb252b8cf68947a2535349e4deb6b892c` |
| [jiwoochris/artex-ko](https://github.com/jiwoochris/artex-ko) | `6f495eebeaaccf1a767be8f89fa2b4b65e48bb98` |

## 설계에 반영한 아이디어
- PentAGI: 작업을 나누고 실행 결과를 남겨 보고하는 흐름. 상시 서비스·장기 벡터 메모리 대신 단일 실행과 JSON 결과를 선택했다.
- Pentest Swarm AI: 명시적 scope, 도구 실행 관찰, 로컬 실험 환경. swarm 스케줄링은 도입하지 않았다.
- ARTEX-KO: 한국어 산출물, 작업 결과 목록, 상태·집계 중심 화면. 화면은 독립적인 HTML 보고서로 구현했다.

확인한 상류 라이선스 표기는 PentAGI MIT, Pentest Swarm AI 및 ARTEX-KO AGPL-3.0이다. 이 독립 구현의 새 코드는 MIT로 제공한다. 이후 상류 코드나 자산을 직접 가져오는 변경에는 해당 파일의 라이선스·저작권 고지를 별도로 검토하고 포함해야 한다.

## 점검 기준 참고
- [OWASP File Upload Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html)
- [OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)
- [OWASP Session Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html)

README와 기능 설명은 시점에 따라 바뀐다. 재현 실험에서는 실제 실행하는 저장소 commit과 모델 버전을 별도로 고정한다.
