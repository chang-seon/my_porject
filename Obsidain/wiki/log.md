# 위키 활동 로그

> **규칙**: append-only. 기존 항목 절대 삭제·수정 금지.
> 파싱 팁: `grep "^## \[" log.md | tail -5` 로 최근 5개 항목 확인.

---

## [2026-05-25] create | work_orders/ 폴더 생성 및 문서 A·B 작성

- D:\IT\Agentic_AI\work_orders\ 폴더 신설 (영문명)
- document_A_전과정정리.md — 세 채팅방 전 회의 흐름·결정 경위·번복 수정 내역 정리
- document_B_Opus_인수인계.md — 누락 없는 최종 Opus용 인수인계 프롬프트

---

## [2026-05-25] ingest | 옵시디언 전면 재정비 — 종합 문서 기준

- 소스: 구직에이전트_종합_코워크용.md (결정사항 53개 + 페르소나 + 흐름도)
- overview.md 전면 갱신 — 11단계 파이프라인 흐름도 포함
- concepts/검증AI.md 전면 갱신 — D 하이브리드 구조 흐름도, Q3~Q7 상세
- concepts/메타원칙.md 전면 갱신 — 7개 원칙 실무 적용법, 체크리스트, 충돌 해소 이력
- concepts/작동흐름.md 신규 — 셋업·반복 사이클 흐름도, HITL, 패스 처리, 알림
- concepts/데이터전략.md 신규 — 3-소스, 3-풀, 문체 마커 6종, 안티패턴 4종, 페르소나 11섹션
- concepts/학습시스템.md 신규 — 신호 5층, RAG, 자체AI 진화, 자동화 전환
- concepts/미결사항.md 전면 갱신 — 우선순위별 분류, 충돌 해소 이력, #54 아이디어
- index.md 전면 갱신 — 신규 페이지 전체 등록
- 기존 검증AI-구조.md는 검증AI.md로 통합 (중복 파일 정리 필요)

## [2026-05-25] ingest | 구직 에이전트 기획 내용 반영

- 소스: 코워크_인수인계.md, 코워크_시작프롬프트.md
- overview.md 갱신 — 구직 에이전트 기획 내용으로 전면 교체
- concepts/검증AI-구조.md 신규 — D 하이브리드, Q3·Q5·Q6·Q7 정리
- concepts/메타원칙.md 신규 — 확정 헌법 7개(#20·#30·#36·#37·#38·#39·#50)
- concepts/미결사항.md 신규 — M4~M10, Q3·Q4·Q6, 원칙 충돌 추적
- index.md 갱신 — 신규 페이지 3개 등록
- 참고: 옵시디언 볼트 12개 노트는 미인제스트 (다음 세션에서 진행 권장)

## [2026-05-31] dev | MVP v1.0.0 완성 — 287/287 테스트 통과

- DAY 23: document pipeline.py (생성→검증→HITL2), orchestrator.py 갱신 — 8/8
- DAY 24: application recorder.py + link_handler.py, orchestrator ⑦⑧ 구현 — 14/14
- DAY 25: learner RAG (embedder 128차원 TF-IDF, vector_store, ingest, retriever) — 21/21
- DAY 26: company_analyzer (RAG 평판 조회 + 자동 패스) — 9/9
- DAY 27: interview prep_generator (RAG+LLM) + debrief (B/C/E층+RAG #36) — 11/11
- DAY 28: auto_promotion (N회 연속 OK → 자동화 단계 상승, #30·#37·M4) — 11/11
- DAY 29: FastAPI 대시보드 (비용·HITL·검증통과율·자동화·지원현황) — 7/7
- DAY 30: E2E 통합 테스트 15/15 + README 최종본 + MVP_v1.0.md + git tag v1.0.0
- 전체 287/287 테스트 통과, 메타원칙 7개 위반 0건

---

## [2026-05-31] dev | Phase 2 진행중 (DAY 17~22) — 191/191 테스트 통과

- DAY 17: SaraminSource(urllib+backoff), normalizer, deduplicate — 19/19 통과
- DAY 18: WorknetSource, JoballioSource, GeminiWebSource, aggregator(4소스→중복제거) — 12/12 통과
- DAY 19: filter.py(페르소나 제약), pass_handler.py(M11: company+job_role), 0002 마이그레이션 — 13/13 통과
- DAY 20: rule_engine.py(YAML 룰), style_marker.py, anti_pattern.py — 14/14 통과
- DAY 21: llm_judge.py(지연초기화), retry_loop.py(Q3: 3회→HITL), storage.py — 12/12 통과
- DAY 22: pool_loader.py(3-풀 로드), synthesizer.py(SHA256 draft_id), generate_cover_letter.md — 8/8 통과
- 기술 결정: urllib.request(의존성 최소화), _get_router() 패턴(import시 API키 불필요), patch.dict 패턴

---

## [2026-05-31] dev | Phase 1 완료 (DAY 10~16) — v0.2.0-phase1 태그

- DAY 10: persona extractor (txt/docx/pdf → LLM → 11섹션) — 9/9 통과
- DAY 11: persona storage + changelog (DB 저장, 변경이력 #37) — 5/5 통과
- DAY 12: 텔레그램 단방향 알림 + 3종 템플릿 — 7/7 통과
- DAY 13: core orchestrator 셋업 흐름 ①~⑤ 구현 — 3/3 통과
- DAY 14: HITL CLI + hitl_bus (DB 기반 요청·응답 큐) — 3/3 통과
- DAY 15: learner 신호 5층 + 동적 기준값 (#37) — 9/9 통과
- DAY 16: 전체 113/113 통과, lint clean, v0.2.0-phase1 태그

---

## [2026-05-31] dev | 단계2 완료 (DAY 01~09) — v0.1.0-spec-frozen 태그

- DAY 05: interface.py 8개 v1.0 확정 (16/16 통과)
- DAY 06: core/orchestrator.py 11단계 stub + router (13/13 통과)
- DAY 07: 검증AI 룰셋 YAML 4종 + LLM 심사 프롬프트 (12/12 통과)
- DAY 08: 미결 M1·M4~M10 8건 결정 → decisions/OPEN_ITEMS_RESOLVED.md
- DAY 09: lint_imports.py(25파일 clean) + README + STAGE_2_SUMMARY + git tag v0.1.0-spec-frozen
- 전체 테스트 65/65 통과

---

## [2026-05-31] dev | DAY 04 — LLM 호출 추상화 완료

- shared/llm/ Claude·Gemini 클라이언트, LLMRouter, cost_tracker
- google-generativeai deprecated → google-genai 2.7.0 교체
- 9/9 통과

---

## [2026-05-31] dev | DAY 03 — DB 스키마 + SQLite 추상화 계층 완료

- shared/db/migrations/0001_initial.sql — 17개 테이블 + 인덱스 (idempotent)
- shared/db/connection.py — WAL 모드, DB_PATH 환경변수, --init CLI
- shared/db/repositories/persona_repo.py — get_persona, upsert_persona
- tests/test_db_roundtrip.py — 4/4 통과
- DB 위치: D:\IT\Agentic_AI\data\agent.db

---

## [2026-05-31] dev | DAY 02 — JSON 표준 포맷 정의 완료 (M13 확정)

- shared/schemas/ 4개 Pydantic 모델 작성 (JobPosting, Persona 11섹션, LearningSignal, EventLog)
- M13 확정: nested Pydantic / str ISO8601 / list[str] / Optional=None
- tests/test_schemas.py — 11/11 통과

---

## [2026-05-31] dev | DAY 01 — 레포 골격 생성 완료

- job_agent/ 폴더 트리 전체 생성 (core, shared, features 8개, protected)
- 각 features에 interface.py(v1.0 플레이스홀더) + SKILL.md
- requirements.txt 갱신, venv 환경 설정, PYTHONUTF8=1 자동 설정

---

## [2026-05-31] setup | 개발환경 설정

- venv/ 생성 (D:\IT\Agentic_AI\venv)
- .vscode/settings.json — 터미널 자동 venv 활성화
- PowerShell 프로파일 — 폴더 진입 시 자동 venv 활성화

---

## [2026-05-25] init | 위키 초기 구조 설정

- SCHEMA.md 작성 (거버넌스 문서)
- wiki/ 디렉토리 구조 생성 (entities/, concepts/, scenarios/)
- raw/ 디렉토리 생성 (불변 소스 보관용)
- index.md, log.md, overview.md 초기화
- LLM Wiki 패턴 기반으로 하네스 엔지니어링 프로젝트에 맞춤 적용
