# 초개인화 구직 에이전트 — DAY별 구현 계획서

> 작성일: 2026-05-30
> 기준 문서: `document_A_전과정정리.md`, `document_B_Opus_인수인계.md`, `PLAN_HANDOFF_2026-05-25.md`, `CLAUDE.md`
> 범위: **단계2 사양 구체화 + 단계3 Phase 1~3 전체** (MVP 완성까지 DAY별 풀 로드맵)
> 토큰 기준: **Claude Pro $22 / Opus 위주 / 5h 윈도우 + 7일 한도**
> 작업 원칙: 무조건 하나씩, 충돌·꼬임 0건

---

## 0. 사용 설명서 (반드시 먼저 읽을 것)

1. 매 세션 시작 시 **이 문서 → 직전 `progress/DAY_N_done.md` → `document_B_Opus_인수인계.md` 순서**로 읽는다.
2. **1 DAY = 1 의사결정 묶음**. 한 DAY를 5h 윈도우 1~2개 안에 끝낼 수 있게 쪼개 놓았다.
3. 한 DAY가 5h 윈도우를 넘기면 **DAY를 쪼개지 말고, 윈도우만 대기**한다 (DAY 경계가 컨텍스트 단절 지점이기 때문).
4. DAY 종료 시 반드시 `progress/DAY_N_done.md`를 채워라 → 다음 세션 컨텍스트 복원의 단일 진실 공급원.
5. **보호 컴포넌트(interface.py·core/) 수정 절차**는 CLAUDE.md 4번 섹션을 그대로 따른다.
6. 미결 항목은 임의 결정 금지. DAY 카드에 표시된 "🔴 사용자 결정 필요" 마커를 만나면 즉시 사용자에게 묻는다.

---

## 1. Claude Pro $22 토큰 예산표

### 1-1. 플랜 한도 (실측 기준)

| 항목 | Opus 4.x | Sonnet 4.x |
|------|---------|-----------|
| 5h 윈도우 메시지 | **약 5~15개** (대화 길이·첨부에 따라 변동) | 약 40~50개 |
| 7일 한도 (Pro) | **약 40~80 Opus 메시지/주** | 충분 |
| 1 메시지 평균 컨텍스트 | 입력 5k~30k token + 출력 1k~5k token | 동일 |

> Pro $22는 Opus를 매우 보수적으로 풀어준다. **Opus는 결정·검토 전용으로만 쓰고, 생성·구현은 Sonnet에 위임**하는 게 유일한 안전 운영법.

### 1-2. 모델 사용 분배 원칙 (DAY 카드에서 그대로 따를 것)

| 작업 유형 | 사용 모델 | 이유 |
|----------|---------|------|
| 아키텍처 정합성 검토 / 충돌 해소 | **Opus** | 결정 품질이 비용보다 비쌈 |
| interface.py 설계 (보호 컴포넌트) | **Opus** | 한 번 결정하면 되돌리기 어려움 |
| 미결 항목(M·Q) 의사결정 보조 | **Opus** | 잘못된 결정의 누적 비용이 큼 |
| internal/ 구현 코드 | Sonnet | 반복적·교체 가능 |
| 단위 테스트 · 픽스처 | Sonnet | 양치기 작업 |
| 문서화 · SKILL.md 작성 | Sonnet | 양치기 작업 |
| Git 커밋 메시지 · 로그 분석 | Sonnet | 짧고 정형적 |

### 1-3. 1 DAY 권장 예산

| 구분 | Opus 메시지 | Sonnet 메시지 | 5h 윈도우 |
|------|-----------|-------------|---------|
| 가벼운 DAY (문서·결정) | 3~5 | 5~10 | 1개 안에 종료 |
| 표준 DAY (모듈 1개 구현) | 5~8 | 15~25 | 1~2개 |
| 무거운 DAY (스키마·검증AI) | 8~12 | 20~35 | 2개 (윈도우 사이 대기) |

> **경고선**: Opus가 5h 윈도우에서 12개를 넘으면 그 DAY는 무조건 중단 → progress 갱신 → 다음 윈도우/세션으로 이월.

### 1-4. 7일 한도 관리

- **주간 Opus 상한 70개**를 가정하고 짠다. DAY를 30일에 걸쳐 분산했으니 평균 주 8~10개로 수렴 (안전 마진 충분).
- 매주 일요일 밤 `progress/WEEK_N_summary.md` 작성 (Sonnet으로 충분).

---

## 2. DAY 분배 원칙 (충돌·꼬임 방지)

| 원칙 | 의미 |
|------|------|
| **단방향 의존** | DAY N은 DAY 1~N-1 산출물만 참조. 역방향 수정 금지. 필요하면 새 DAY 신설 |
| **인터페이스 우선** | 모든 features/ DAY는 interface.py 먼저 → core 등록 → internal 구현 (CLAUDE.md 5단계) |
| **보호 컴포넌트 잠금** | interface.py 버전 태그(`# interface version: X.Y`)가 올라가는 DAY는 별도 표시. 사용자 승인 게이트 |
| **미결 동결** | 🔴 미결 항목은 해당 DAY 첫 작업으로 결정 → 결정 안 되면 DAY 보류, 다음 DAY 못 시작 |
| **테스트 동봉** | 모든 구현 DAY는 `tests/test_<module>.py` 동시 작성 (산출물 정의에 포함) |
| **롤백 가능** | DAY 종료 = git commit 1회 (커밋 메시지에 "DAY N: ..." 접두) |

---

## 3. 전체 로드맵 한눈에

```
[단계2 · 사양 구체화]   DAY 01 ~ DAY 09   (9일)
  └─ L섹션 6항목 + 개발 직전 결정 M1·Q4 + 중간 미결 M4~M10

[단계3 · Phase 1 기반]  DAY 10 ~ DAY 16   (7일)
  └─ shared/db · core 골격 · features/persona · features/notification

[단계3 · Phase 2 핵심]  DAY 17 ~ DAY 24   (8일)
  └─ features/job_search · document · validator

[단계3 · Phase 3 확장]  DAY 25 ~ DAY 30   (6일)
  └─ features/learner · interview · RAG · 통합 E2E · MVP 릴리스
```

**총 30 DAY** (= 4~5주, 주 5~6 DAY 페이스). Opus 주 한도 70개 안에서 안전하게 수렴.

---

## 4. DAY 카드 양식 (모든 DAY 공통)

```
## DAY N — <주제>
- 단계: 단계2 / Phase1 / Phase2 / Phase3
- 산출물 (파일 경로): <리스트>
- 선행 DAY: DAY M (어떤 산출물에 의존)
- 예상 Opus 사용: N개 메시지 (가벼움 / 표준 / 무거움)
- 예상 Sonnet 사용: N개 메시지
- 핵심 결정 포인트: <리스트>
- 미결 처리: 🔴/🟡/🟢 + 처리 방법
- 보호 컴포넌트 변경: 있음/없음 (있으면 승인 게이트)
- 종료 조건 (Definition of Done): <체크리스트>
- 종료 시 갱신: progress/DAY_N_done.md
- 다음 DAY 시작 시 읽을 파일: <리스트>
```

---

# 단계2 · 사양 구체화 (DAY 01 ~ DAY 09)

## DAY 01 — 모듈 폴더 구조 최종 확정 + 레포 골격 생성

- 단계: 단계2
- 산출물:
  - `D:\IT\Agentic_AI\job_agent\` 빈 폴더 트리 (core/ shared/ features/{persona,job_search,document,validator,notification,application,interview,learner}/ protected/)
  - 각 폴더에 `__init__.py`, 빈 `interface.py`, 빈 `SKILL.md` 플레이스홀더
  - `D:\IT\Agentic_AI\.claudeignore` (protected/, .env, *.db)
  - `D:\IT\Agentic_AI\.gitignore` (.env, *.db, __pycache__/, venv/, .mypy_cache/)
  - `D:\IT\Agentic_AI\requirements.txt` (anthropic, google-generativeai, python-dotenv, pydantic, sqlmodel, python-telegram-bot, pytest)
- 선행 DAY: 없음
- 예상 Opus 사용: 3개 (구조 확정 검토)
- 예상 Sonnet 사용: 5개 (파일 생성)
- 핵심 결정:
  - 폴더 트리 = document_B H섹션 구조 그대로
  - 외부 노출 = `interface.py` 단일 파일, 상단에 `# interface version: 1.0` 필수
- 미결 처리: 없음 (이미 확정)
- 보호 컴포넌트 변경: 없음 (껍데기만)
- 종료 조건:
  - [ ] `tree job_agent/` 출력 시 8개 features + core + shared + protected 확인
  - [ ] `pip install -r requirements.txt` 성공
  - [ ] `pytest` 실행 시 "no tests collected"로 정상 종료
- 종료 시 갱신: `progress/DAY_01_done.md`
- 다음 DAY 시작 시 읽을 파일: PLAN_DAYS.md, progress/DAY_01_done.md

---

## DAY 02 — JSON 표준 포맷 정의 (공고·페르소나·학습신호·이벤트 로그)

- 단계: 단계2
- 산출물:
  - `job_agent/shared/schemas/job_posting.py` (Pydantic 모델, source/title/company/url/raw_text 등)
  - `job_agent/shared/schemas/persona.py` (11섹션 Pydantic 모델 골격 — 타입만 잠정)
  - `job_agent/shared/schemas/learning_signal.py` (A~E 5층 enum + payload)
  - `job_agent/shared/schemas/event_log.py` (event_type/event_data/year/month/day)
  - `job_agent/shared/schemas/__init__.py` (export)
  - `job_agent/shared/SKILL.md` (스키마 사용법)
- 선행 DAY: DAY 01
- 예상 Opus 사용: 5개 (스키마 충돌 검토)
- 예상 Sonnet 사용: 10개 (Pydantic 코드 작성)
- 핵심 결정:
  - 필드명 = 영어 snake_case (CLAUDE.md 규칙)
  - 모든 모델 `model_config = ConfigDict(extra="forbid")` (오타 차단)
  - 타임스탬프 = ISO8601 문자열 + year/month/day 계층 인덱스 동시 보관 (#37)
- 미결 처리: M13(데이터 타입) — **이 DAY에서 일괄 결정**. 🔴 사용자 결정 필요
- 보호 컴포넌트 변경: 없음 (shared/는 보호 외부)
- 종료 조건:
  - [ ] `pytest tests/test_schemas.py` 모든 모델 round-trip 통과
  - [ ] M13 결정 사항이 PLAN_DAYS.md 부록 A에 기록됨
- 종료 시 갱신: progress/DAY_02_done.md
- 다음 DAY 시작 시 읽을 파일: progress/DAY_02_done.md, schemas/*.py

---

## DAY 03 — DB 스키마 설계 + SQLite 추상화 계층

- 단계: 단계2 + Phase1 경계
- 산출물:
  - `job_agent/shared/db/schema.sql` (11 페르소나 테이블 + 패스/배제 + 학습신호 + 동적기준값 + RAG)
  - `job_agent/shared/db/connection.py` (sqlite3 wrapper, WAL 모드, 외장 SSD 경로 지원)
  - `job_agent/shared/db/repositories/persona_repo.py` (get_persona, upsert_persona)
  - `job_agent/shared/db/migrations/0001_initial.sql`
  - `tests/test_db_roundtrip.py` (insert→select 검증)
- 선행 DAY: DAY 02 (Pydantic 스키마 → SQL 컬럼 매핑)
- 예상 Opus 사용: 8개 (스키마 정합성·인덱싱 전략 검토)
- 예상 Sonnet 사용: 20개 (SQL · 래퍼 코드 · 테스트)
- 핵심 결정:
  - DB 위치: **D 드라이브** (`D:\IT\Agentic_AI\data\agent.db`) — C 드라이브 용량 보호 (document_B G섹션)
  - LLM 호출부도 추상화 (DAY 04에서 처리) → 여기는 DB만
  - user_id 격리 컬럼 모든 개인 테이블에 필수 (#38)
- 미결 처리: 없음 (DAY 02 결정으로 자동 해결)
- 보호 컴포넌트 변경: 없음
- 종료 조건:
  - [ ] `python -m job_agent.shared.db.connection --init` 실행 시 DB 생성
  - [ ] 모든 페르소나 11섹션 round-trip 테스트 통과
  - [ ] 마이그레이션 스크립트 idempotent (두 번 실행해도 OK)
- 종료 시 갱신: progress/DAY_03_done.md
- 다음 DAY 시작 시 읽을 파일: schema.sql, persona_repo.py

---

## DAY 04 — LLM 호출 추상화 계층 (Claude·Gemini 인터페이스)

- 단계: 단계2
- 산출물:
  - `job_agent/shared/llm/base.py` (`LLMClient` 추상 클래스 — generate/stream/count_tokens)
  - `job_agent/shared/llm/claude_client.py` (anthropic SDK 래퍼, 모델 토글)
  - `job_agent/shared/llm/gemini_client.py` (google-generativeai 래퍼)
  - `job_agent/shared/llm/router.py` (작업유형 → 모델 라우팅, 토큰 카운터 누적)
  - `job_agent/shared/llm/cost_tracker.py` (호출별 비용 SQLite 적재 — #54 대시보드 대비)
  - `tests/test_llm_router.py` (모의 응답 fixture)
- 선행 DAY: DAY 03 (cost 로그용 DB)
- 예상 Opus 사용: 6개 (추상화 경계 결정)
- 예상 Sonnet 사용: 15개
- 핵심 결정:
  - 추상화 목적: **v3+ 자체 AI 교체 가능성** (#39, #50). 모든 호출은 router 거침
  - API 키 = `.env` 에서만 로드. `protected/.env.example` 작성 (실제 .env는 git에서 제외)
  - 호출당 cost 자동 적재 → #54 대시보드의 기반
- 미결 처리: 없음
- 보호 컴포넌트 변경: 없음 (shared)
- 종료 조건:
  - [ ] `LLMClient(provider="claude").generate("ping")` 통과
  - [ ] router 호출 시 cost_log 테이블에 row 적재
- 종료 시 갱신: progress/DAY_04_done.md
- 다음 DAY 시작 시 읽을 파일: llm/router.py, llm/base.py

---

## DAY 05 — 7개 모듈 interface.py 시그니처 초안 (보호 컴포넌트 1.0)

- 단계: 단계2
- 산출물:
  - `job_agent/features/persona/interface.py` (`extract_persona(files: list[Path]) -> Persona`, `update_persona(diff: dict) -> Persona`)
  - `job_agent/features/job_search/interface.py` (`fetch_postings(query: JobQuery) -> list[JobPosting]`, `filter_postings(...) -> list[JobPosting]`)
  - `job_agent/features/document/interface.py` (`generate_cover_letter(...) -> Draft`)
  - `job_agent/features/validator/interface.py` (`validate(target: ValidationTarget, content: str) -> ValidationResult`)
  - `job_agent/features/notification/interface.py` (`notify(message: Notification) -> NotifyAck`)
  - `job_agent/features/application/interface.py` (`record_application(...) -> ApplicationRecord`)
  - `job_agent/features/interview/interface.py` (`prepare(...) / debrief(...)`)
  - `job_agent/features/learner/interface.py` (`record_signal(signal: LearningSignal) -> None`, `get_dynamic_threshold(domain: str) -> Any`)
  - 각 파일 상단: `# interface version: 1.0`
- 선행 DAY: DAY 02 (스키마), DAY 03 (DB), DAY 04 (LLM)
- 예상 Opus 사용: **10개** (이 DAY는 무거움 — 보호 컴포넌트 첫 확정)
- 예상 Sonnet 사용: 10개
- 핵심 결정:
  - 모든 함수 반환 = **dict 또는 Pydantic 모델** (CLAUDE.md 규칙: dict 반환)
  - 에러는 함수 밖으로 전파 금지 → `{"결과": "실패", "이유": str}` 형태
  - 인터페이스 변경 시 버전 태그 bump 의무
- 미결 처리: 없음 (시그니처만, 구현은 Phase별로)
- 보호 컴포넌트 변경: **있음 — interface.py 8개 생성** → 사용자 승인 게이트 필수
- 종료 조건:
  - [ ] `mypy job_agent/features/*/interface.py` 통과
  - [ ] 사용자가 8개 interface 모두 승인
  - [ ] 각 모듈에 `internal/` 빈 폴더 생성됨
- 종료 시 갱신: progress/DAY_05_done.md + `progress/INTERFACE_VERSIONS.md` 신규
- 다음 DAY 시작 시 읽을 파일: 모든 interface.py, INTERFACE_VERSIONS.md

---

## DAY 06 — core/ 오케스트레이터 골격

- 단계: 단계2
- 산출물:
  - `job_agent/core/orchestrator.py` (8개 features import, 파이프라인 11단계 함수 stub)
  - `job_agent/core/router.py` (모듈간 호출은 여기만 거침 = 침범 최소화 원칙)
  - `job_agent/core/SKILL.md` (core 수정 규칙)
  - `tests/test_orchestrator_smoke.py` (모든 stub 호출이 NotImplementedError 던지는지)
- 선행 DAY: DAY 05
- 예상 Opus 사용: 6개
- 예상 Sonnet 사용: 10개
- 핵심 결정:
  - core는 **모듈간 유일한 중재자**. features끼리 직접 import 금지 (lint 규칙으로 강제 — DAY 09)
- 미결 처리: 없음
- 보호 컴포넌트 변경: **있음 — core/** → 사용자 승인 게이트
- 종료 조건:
  - [ ] 11단계 함수 stub 존재
  - [ ] 사용자 승인
- 종료 시 갱신: progress/DAY_06_done.md
- 다음 DAY 시작 시 읽을 파일: orchestrator.py

---

## DAY 07 — 검증AI 룰셋 초안 (Q4 결정 + 룰셋 문서화)

- 단계: 단계2
- 산출물:
  - `job_agent/features/validator/internal/rules/cover_letter_rules.yaml` (문체 마커 6 + 안티패턴 4)
  - `job_agent/features/validator/internal/rules/code_rules.yaml`
  - `job_agent/features/validator/internal/rules/job_posting_rules.yaml`
  - `job_agent/features/validator/internal/rules/interview_rules.yaml`
  - `job_agent/features/validator/internal/prompts/cover_letter_judge.md` (2차 LLM 검증 프롬프트)
  - `job_agent/features/validator/SKILL.md`
- 선행 DAY: DAY 02, DAY 05
- 예상 Opus 사용: **10개** (룰셋 품질이 시스템 전체 품질 결정)
- 예상 Sonnet 사용: 15개
- 핵심 결정:
  - 🔴 **Q4 작성 주체**: [본인 직접 / Claude 초안 / RAG 자동] — **DAY 첫 작업으로 사용자에게 확정 받기**
  - 1차 룰 = LLM 없음·비용 0 (D 하이브리드 구조)
  - 2차 LLM 프롬프트는 Claude 기준으로 작성. Gemini용은 v2 이후
- 미결 처리: **Q4 확정** (이 DAY에서 종결). 🔴
- 보호 컴포넌트 변경: 없음 (internal)
- 종료 조건:
  - [ ] Q4 결정 사항 progress + PLAN_DAYS 부록 A 기록
  - [ ] 룰 4개 YAML 파싱 테스트 통과
- 종료 시 갱신: progress/DAY_07_done.md
- 다음 DAY 시작 시 읽을 파일: validator/internal/rules/

---

## DAY 08 — 개발 직전 결정 M1 이메일 처리 + 중간 미결 M4~M10 일괄 정리

- 단계: 단계2
- 산출물:
  - `D:\IT\Agentic_AI\decisions\OPEN_ITEMS_RESOLVED.md` (M1·M4·M5·M6·M7·M8·M9·M10 결정 기록)
  - 필요 시 schemas/persona.py, schemas/job_posting.py 수정 (M7 라벨, M8 잡코리아 플래그 등)
- 선행 DAY: DAY 02·03·07
- 예상 Opus 사용: **10개** (8건 결정 — 무거운 DAY)
- 예상 Sonnet 사용: 5개
- 핵심 결정 (각 항목 🔴 사용자 결정 필요):
  - M1: 이메일 자동 확인 방식 [OAuth / 본인 입력 / 제외]
  - M4: 자동화 전환 임계값 N
  - M5: 보강 질문 5~7개 리스트
  - M6: 추가 정보 부족 시 판단 로직
  - M7: 콘텐츠 풀 직무별 라벨링 체계
  - M8: 잡코리아 포함 여부 (#39 충돌 재확인)
  - M9: 텔레그램 단/양방향
  - M10: 공고 갱신 트리거
- 미결 처리: **8건 종결**. 한 건이라도 미결이면 DAY 미완료 처리
- 보호 컴포넌트 변경: schema 변경 시 interface.py 영향 검토 → 영향 있으면 버전 bump
- 종료 조건:
  - [ ] 8건 모두 OPEN_ITEMS_RESOLVED.md 기록
  - [ ] 영향 받은 schema 테스트 재통과
- 종료 시 갱신: progress/DAY_08_done.md
- 다음 DAY 시작 시 읽을 파일: OPEN_ITEMS_RESOLVED.md

---

## DAY 09 — 모듈간 침범 방지 lint 룰 + 단계2 종료 검수

- 단계: 단계2 마감
- 산출물:
  - `D:\IT\Agentic_AI\tools\lint_imports.py` (features/X가 features/Y를 직접 import하면 fail)
  - `D:\IT\Agentic_AI\.pre-commit-config.yaml` (lint_imports + black + mypy)
  - `D:\IT\Agentic_AI\README.md` 단계2 종료 시점 최신화
  - `D:\IT\Agentic_AI\decisions\STAGE_2_SUMMARY.md`
- 선행 DAY: DAY 01~08 전부
- 예상 Opus 사용: 4개 (전체 정합성 최종 검토)
- 예상 Sonnet 사용: 10개
- 핵심 결정: 없음 (마감 검수)
- 미결 처리: 모든 단계2 미결 완료 확인
- 보호 컴포넌트 변경: 없음
- 종료 조건:
  - [ ] `python tools/lint_imports.py` clean
  - [ ] `pre-commit run --all-files` 통과
  - [ ] git tag `v0.1.0-spec-frozen`
- 종료 시 갱신: progress/DAY_09_done.md + progress/WEEK_2_summary.md
- 다음 DAY 시작 시 읽을 파일: STAGE_2_SUMMARY.md

---

# 단계3 · Phase 1 — 기반 (DAY 10 ~ DAY 16)

## DAY 10 — features/persona internal 구현 1/2 (파일 파싱·페르소나 추출)

- 단계: Phase1
- 산출물:
  - `features/persona/internal/extractor.py` (docx/pdf/txt → 텍스트)
  - `features/persona/internal/llm_extract.py` (Claude로 11섹션 추출)
  - `features/persona/internal/prompts/extract_persona.md`
  - `tests/persona/test_extractor.py`
- 선행 DAY: DAY 02·03·04·05
- 예상 Opus 사용: 5개 (프롬프트 설계)
- 예상 Sonnet 사용: 25개 (파싱 코드 · 테스트)
- 핵심 결정: 파일 파싱 라이브러리 = python-docx + pypdf (PDF 스킬과 별개, 단순 텍스트 추출 목적)
- 미결 처리: 없음
- 보호 컴포넌트 변경: 없음
- 종료 조건:
  - [ ] 어창선 본인 자소서 1편 입력 → 11섹션 dict 반환
  - [ ] 빈 파일·깨진 파일 graceful 실패
- 종료 시 갱신: progress/DAY_10_done.md

---

## DAY 11 — features/persona internal 2/2 (DB 저장·갱신·시계열)

- 단계: Phase1
- 산출물:
  - `features/persona/internal/storage.py` (Repository 사용, 11섹션 분해 저장)
  - `features/persona/internal/changelog.py` (변경 전/후/사유/타임스탬프 #37)
  - `tests/persona/test_storage_changelog.py`
- 선행 DAY: DAY 10
- 예상 Opus 사용: 4개
- 예상 Sonnet 사용: 20개
- 핵심 결정: 변경 이력은 별도 테이블 `persona_changelog` (year/month/day 인덱스)
- 종료 조건:
  - [ ] 페르소나 update → changelog row 추가 검증
  - [ ] 어창선 시드값 시드 스크립트 동작
- 종료 시 갱신: progress/DAY_11_done.md

---

## DAY 12 — features/notification (텔레그램 단방향)

- 단계: Phase1
- 산출물:
  - `features/notification/internal/telegram_sender.py`
  - `features/notification/internal/templates/` (자소서검토·공고알림·HITL요청)
  - `features/notification/SKILL.md`
  - `tests/notification/test_send.py` (실제 토큰은 .env)
- 선행 DAY: DAY 05·08 (M9 단/양방향 결정)
- 예상 Opus 사용: 3개
- 예상 Sonnet 사용: 15개
- 핵심 결정: M9 결정 반영. 양방향이면 webhook + FastAPI 미니서버 추가 검토 (스코프 초과 시 v1.1로 이월)
- 종료 조건:
  - [ ] 본인 텔레그램 chat_id로 테스트 메시지 발송 성공
- 종료 시 갱신: progress/DAY_12_done.md

---

## DAY 13 — core/ orchestrator 1차 통합 (persona + notification)

- 단계: Phase1
- 산출물:
  - `core/orchestrator.py` 구현 (1단계: 최초 셋업 흐름 ①~⑤)
  - `tests/integration/test_setup_flow.py`
- 선행 DAY: DAY 06·11·12
- 예상 Opus 사용: 6개 (통합 시점 정합성)
- 예상 Sonnet 사용: 15개
- 보호 컴포넌트 변경: core/orchestrator.py 본문 추가 → 승인 게이트
- 종료 조건: 셋업 E2E 통과 (파일 → 페르소나 DB 저장 → 텔레그램 알림)
- 종료 시 갱신: progress/DAY_13_done.md

---

## DAY 14 — HITL CLI 미니 인터페이스 (사용자 결정 수신)

- 단계: Phase1
- 산출물:
  - `tools/hitl_cli.py` (지원/패스/보류 입력)
  - `core/hitl_bus.py` (HITL 요청·응답 큐 — DB 기반)
- 선행 DAY: DAY 13
- 예상 Opus 사용: 4개
- 예상 Sonnet 사용: 15개
- 핵심 결정: v1은 CLI로 충분. 텔레그램 양방향은 M9 결정에 따름
- 종료 조건: CLI에서 보류 응답 → DB 상태 변경 확인
- 종료 시 갱신: progress/DAY_14_done.md

---

## DAY 15 — features/learner internal 1차 (학습신호 5층 수집)

- 단계: Phase1
- 산출물:
  - `features/learner/internal/signal_collector.py` (A~E 5층 분기)
  - `features/learner/internal/dynamic_threshold.py` (#37 동적기준값 read/write)
  - `tests/learner/test_signals.py`
- 선행 DAY: DAY 03·05
- 예상 Opus 사용: 5개
- 예상 Sonnet 사용: 20개
- 핵심 결정: 동적기준값은 DB만 읽고 하드코딩 금지 (#37)
- 종료 시 갱신: progress/DAY_15_done.md

---

## DAY 16 — Phase 1 통합 검수 + WEEK 정리

- 단계: Phase1 마감
- 산출물:
  - `decisions/PHASE_1_DONE.md` (체크리스트)
  - git tag `v0.2.0-phase1`
- 선행 DAY: DAY 10~15
- 예상 Opus 사용: 3개
- 예상 Sonnet 사용: 10개
- 종료 조건: 셋업 흐름 + 학습신호 수집 E2E 안정 동작
- 종료 시 갱신: progress/DAY_16_done.md + progress/WEEK_3_summary.md

---

# 단계3 · Phase 2 — 핵심 (DAY 17 ~ DAY 24)

## DAY 17 — features/job_search internal 1/3 (사람인 API)

- 단계: Phase2
- 산출물:
  - `features/job_search/internal/sources/saramin.py` (공식 API 클라이언트)
  - `features/job_search/internal/sources/base.py` (Source 추상)
  - `features/job_search/internal/normalizer.py` (→ JobPosting 표준 JSON)
  - `tests/job_search/test_saramin.py` (VCR cassette)
- 선행 DAY: DAY 02·04·05
- 예상 Opus 사용: 4개
- 예상 Sonnet 사용: 25개
- 핵심 결정: API 키 .env에서만. rate limit 핸들링 (지수 backoff)
- 종료 조건: 본인 조건(마곡·신입·AI)으로 검색 → 정규화된 JSON 리스트 반환
- 종료 시 갱신: progress/DAY_17_done.md

---

## DAY 18 — features/job_search 2/3 (워크넷·잡알리오 + Gemini 폴백)

- 단계: Phase2
- 산출물:
  - `features/job_search/internal/sources/worknet.py`
  - `features/job_search/internal/sources/joballio.py`
  - `features/job_search/internal/sources/gemini_web.py` (API 없는 곳 — JSON 표준 변환)
- 선행 DAY: DAY 17
- 예상 Opus 사용: 4개
- 예상 Sonnet 사용: 25개
- 종료 조건: 4개 소스 통합 호출 → 중복 제거 → 단일 리스트
- 종료 시 갱신: progress/DAY_18_done.md

---

## DAY 19 — features/job_search 3/3 (필터링·매칭 + 패스 처리)

- 단계: Phase2
- 산출물:
  - `features/job_search/internal/filter.py` (페르소나 제약 대조)
  - `features/job_search/internal/pass_handler.py` (회사 평판·동일조건 반복·이직 시 초기화)
- 선행 DAY: DAY 11·18
- 예상 Opus 사용: 6개 (패스 처리 로직 정합성)
- 예상 Sonnet 사용: 20개
- 핵심 결정: M11(동일조건 정의) — 이 DAY에서 운영 시작 위해 잠정값 확정 필요. 🔴
- 종료 조건: 패스 → 동일조건 반복 시 차단 검증
- 종료 시 갱신: progress/DAY_19_done.md

---

## DAY 20 — features/validator internal 1/2 (1차 룰 엔진)

- 단계: Phase2
- 산출물:
  - `features/validator/internal/rule_engine.py` (YAML 룰 → 판정 함수)
  - `features/validator/internal/checks/style_marker.py`
  - `features/validator/internal/checks/anti_pattern.py`
  - `tests/validator/test_rules.py`
- 선행 DAY: DAY 07
- 예상 Opus 사용: 5개
- 예상 Sonnet 사용: 25개
- 종료 조건: 본인 자소서 6개 마커 검출, GPT 안티패턴 자소서 4개 검출
- 종료 시 갱신: progress/DAY_20_done.md

---

## DAY 21 — features/validator 2/2 (2차 LLM + Q3 재시도 루프)

- 단계: Phase2
- 산출물:
  - `features/validator/internal/llm_judge.py` (Claude judge)
  - `features/validator/internal/retry_loop.py` (Q3: 3회 → 본인 전달)
  - `features/validator/internal/storage.py` (Q5: 전 과정 저장)
  - `tests/validator/test_retry_loop.py`
- 선행 DAY: DAY 04·20
- 예상 Opus 사용: **10개** (검증AI는 시스템 핵심)
- 예상 Sonnet 사용: 25개
- 핵심 결정: Q3·Q5·Q7 확정사항 그대로 구현. Q6 메타검증은 v1=본인 HITL이므로 별도 구현 없음 (학습신호 B층에 자동 누적되도록만)
- 종료 조건: 실패 케이스 3회 재시도 후 본인 알림 → 본인 [그대로/수정/폐기] 응답 → DB 기록
- 종료 시 갱신: progress/DAY_21_done.md

---

## DAY 22 — features/document internal 1/2 (3-소스 합성)

- 단계: Phase2
- 산출물:
  - `features/document/internal/pool_loader.py` (콘텐츠·구조·문체 3-풀 로드)
  - `features/document/internal/synthesizer.py` (Claude 호출 + 본인 문체 마커 주입)
  - `features/document/internal/prompts/generate_cover_letter.md`
- 선행 DAY: DAY 11·20
- 예상 Opus 사용: 8개 (자소서 생성 = 핵심 가치)
- 예상 Sonnet 사용: 20개
- 핵심 결정: "있는 사실 안에서 거짓말" 정책 = 프롬프트에 명시 + 풀에 없는 사실 차단 후처리
- 종료 조건: 어창선 페르소나 + 가짜 공고 → 자소서 초안 생성 + 6개 마커 자가검증 통과율 ≥ 80%
- 종료 시 갱신: progress/DAY_22_done.md

---

## DAY 23 — features/document 2/2 (검증 통합 + HITL2 흐름)

- 단계: Phase2
- 산출물:
  - `features/document/internal/pipeline.py` (생성 → validator 호출 → 재시도 → HITL2)
  - `core/orchestrator.py` 갱신 (2단계 사이클 ④~⑥ 연결)
- 선행 DAY: DAY 21·22
- 예상 Opus 사용: 6개
- 예상 Sonnet 사용: 20개
- 보호 컴포넌트 변경: core/orchestrator 갱신 → 승인 게이트
- 종료 조건: 공고 1건 → 자소서 생성 → 검증 → HITL2 응답 → 상태 DB 기록
- 종료 시 갱신: progress/DAY_23_done.md

---

## DAY 24 — features/application + Phase 2 통합 검수

- 단계: Phase2 마감
- 산출물:
  - `features/application/internal/recorder.py` (지원·결과 추적)
  - `features/application/internal/link_handler.py` (v1: 링크 전달)
  - git tag `v0.3.0-phase2`
- 선행 DAY: DAY 23
- 예상 Opus 사용: 4개
- 예상 Sonnet 사용: 15개
- 종료 조건: 11단계 중 ①~⑨ E2E 동작
- 종료 시 갱신: progress/DAY_24_done.md + progress/WEEK_4_summary.md

---

# 단계3 · Phase 3 — 확장 (DAY 25 ~ DAY 30)

## DAY 25 — features/learner 2차 (RAG 메타학습 골격)

- 단계: Phase3
- 산출물:
  - `features/learner/internal/rag/vector_store.py` (sqlite + sentence-transformers or 외부 임베딩 API)
  - `features/learner/internal/rag/ingest.py` (회사 평점컷·면접 기출 적재)
  - `features/learner/internal/rag/retriever.py`
- 선행 DAY: DAY 15
- 예상 Opus 사용: 6개
- 예상 Sonnet 사용: 25개
- 핵심 결정: 임베딩 = 로컬 우선(#39). 모델 선택은 sentence-transformers/paraphrase-multilingual
- 종료 시 갱신: progress/DAY_25_done.md

---

## DAY 26 — 회사 분석 + 패스 처리 RAG 통합

- 단계: Phase3
- 산출물:
  - `features/job_search/internal/company_analyzer.py` (RAG 호출 → 평점컷·평판)
  - 패스 핸들러 강화 (DAY 19 모듈 연결)
- 선행 DAY: DAY 19·25
- 예상 Opus 사용: 5개
- 예상 Sonnet 사용: 20개
- 종료 시 갱신: progress/DAY_26_done.md

---

## DAY 27 — features/interview (준비 + 회고)

- 단계: Phase3
- 산출물:
  - `features/interview/internal/prep_generator.py` (RAG로 기출 → Claude로 모의 질문)
  - `features/interview/internal/debrief.py` (회고 입력 → 학습신호 적재)
- 선행 DAY: DAY 15·25
- 예상 Opus 사용: 5개
- 예상 Sonnet 사용: 20개
- 종료 시 갱신: progress/DAY_27_done.md

---

## DAY 28 — 동적기준값 자동화 전환 로직 (#30·#37)

- 단계: Phase3
- 산출물:
  - `features/learner/internal/auto_promotion.py` (검증AI N회 연속 OK → 자동화 단계 상승)
  - `tests/learner/test_auto_promotion.py`
- 선행 DAY: DAY 08·15·21
- 예상 Opus 사용: 5개
- 예상 Sonnet 사용: 15개
- 핵심 결정: M4(임계값 N) 적용
- 종료 시 갱신: progress/DAY_28_done.md

---

## DAY 29 — 운영 모니터링 대시보드 #54 (최소 버전)

- 단계: Phase3
- 산출물:
  - `tools/dashboard/server.py` (FastAPI + 정적 HTML)
  - 표시 항목: 일·주 Opus/Sonnet 토큰 사용·비용·HITL 대기·검증 통과율·자체AI 자립도
- 선행 DAY: DAY 04 cost_tracker
- 예상 Opus 사용: 4개
- 예상 Sonnet 사용: 25개
- 종료 시 갱신: progress/DAY_29_done.md

---

## DAY 30 — MVP E2E 테스트 + v1.0 릴리스

- 단계: Phase3 마감
- 산출물:
  - `tests/integration/test_full_pipeline.py` (11단계 ①~⑪ 전부 mock 데이터로 통과)
  - `README.md` 최종본 (설치·실행·운영 가이드)
  - `decisions/MVP_v1.0.md`
  - git tag `v1.0.0`
- 선행 DAY: DAY 10~29 전체
- 예상 Opus 사용: 5개 (최종 정합성 검토)
- 예상 Sonnet 사용: 20개
- 종료 조건:
  - [ ] 셋업 → 공고 수집 → 필터 → 자소서 → 검증 → HITL → 지원 → 추적 → 면접 → 회고 E2E
  - [ ] 메타원칙 7개 위반 0건 (lint + 수동 체크리스트)
- 종료 시 갱신: progress/DAY_30_done.md + progress/WEEK_5_summary.md + progress/MVP_DONE.md

---

# 부록 A — 미결 결정 추적 (DAY별 결정 사항 기록부)

| ID | 결정 DAY | 결정 내용 | 비고 |
|----|---------|---------|------|
| M13 (데이터 타입) | DAY 02 | nested Pydantic / str ISO8601 / list[str] / Optional=None | ✅ 확정 |
| Q4 (룰셋 작성 주체) | DAY 07 | Claude 초안 (잠정) — 운영 후 본인 피드백으로 보강 | ✅ 잠정 확정 |
| M1 (이메일) | DAY 08 | 본인 직접 입력 (v1.1에서 OAuth 검토) | ✅ |
| M4 (자동화 임계값 N) | DAY 08 | N=5 (dynamic_thresholds로 운영 중 조정) | ✅ |
| M5 (보강 질문) | DAY 08 | 5개 질문 확정 (OPEN_ITEMS_RESOLVED.md 참조) | ✅ |
| M6 (정보 부족 시) | DAY 08 | HITL 요청 후 대기, 24h 무응답 시 보류 | ✅ |
| M7 (직무별 라벨) | DAY 08 | 5분류: ai_ml/data_eng/backend/frontend/general | ✅ |
| M8 (잡코리아) | DAY 08 | 제외 (#39 원칙, 공식 API 없음) | ✅ |
| M9 (텔레그램 단/양방향) | DAY 08 | 단방향 v1, 양방향 v1.1 이월 | ✅ |
| M10 (공고 갱신 트리거) | DAY 08 | 매일 오전 9시 자동 갱신 (크론 0 9 * * *) | ✅ |
| M11 (동일조건 정의) | DAY 19 | _DAY 19 종료 후 기입_ | |
| M12 (모듈 안정성 등급) | DAY 09 | features/ 수직분리로 자동 해소 가능 — DAY 09에서 최종 확인 | |
| M14 (초창기 종료 시점) | DAY 28 | 자동화 전환 시점과 함께 결정 | |
| M15 (지식 유효 기간) | DAY 25 | RAG 적재 시점에 결정 | |

---

# 부록 B — 보호 컴포넌트 변경 게이트 DAY

| DAY | 대상 | 변경 유형 |
|-----|------|---------|
| DAY 05 | 8개 interface.py 신규 | v1.0 생성 |
| DAY 06 | core/orchestrator.py 골격 | 신규 |
| DAY 13 | core/orchestrator.py 본문 | 1차 통합 |
| DAY 23 | core/orchestrator.py 갱신 | 2단계 사이클 연결 |
| (조건부) | interface 시그니처 변경 시 | 버전 bump + 승인 |

---

# 부록 C — 매 DAY 시작 체크리스트

```
[ ] 1. PLAN_DAYS.md 해당 DAY 카드 다시 읽기
[ ] 2. 직전 DAY의 progress/DAY_N-1_done.md 읽기
[ ] 3. INTERFACE_VERSIONS.md 확인 (변경 있었나?)
[ ] 4. 미결 마커(🔴) 있으면 사용자에게 먼저 묻기
[ ] 5. 작업 전 해당 features 폴더의 SKILL.md 읽기 (CLAUDE.md 규칙)
[ ] 6. 보호 컴포넌트 변경 예정이면 승인 요청 먼저
[ ] 7. 시작 시 git checkout dev (main 보호)
```

---

# 부록 D — 매 DAY 종료 체크리스트

```
[ ] 1. 산출물 모두 생성·테스트 통과
[ ] 2. progress/DAY_N_done.md 작성 (템플릿 사용)
[ ] 3. 결정 사항 있으면 부록 A 표 갱신 + decisions/ 폴더 기록
[ ] 4. interface.py 버전 변경 있었으면 INTERFACE_VERSIONS.md 갱신
[ ] 5. requirements.txt 신규 라이브러리 추가 (CLAUDE.md 규칙: 삭제 금지)
[ ] 6. git add (파일명 지정) → commit "DAY N: <한 줄 요약>" → push
[ ] 7. 토큰 사용량 보고 (Opus/Sonnet 개수)
[ ] 8. 다음 DAY 시작 시 읽을 파일 명시
```

---

# 부록 E — 토큰 부족·중단 시 복구 절차

상황: 5h 윈도우 또는 7일 한도 소진 → 작업 중단 필요.

```
1. 진행 중 작업 즉시 멈춤 (반쯤 작성된 파일은 .draft 확장자로 저장)
2. progress/DAY_N_done.md 에 "상태: 중단 / 진행률: XX% / 남은 작업: ..." 기록
3. git add (현재 상태) → commit "DAY N WIP: <상태>" → push (CLAUDE.md 자동 push 규칙)
4. 다음 세션 시작:
   - PLAN_HANDOFF 형식의 인수인계 파일 생성 (자동)
   - 다음 윈도우 열리면 progress/DAY_N_done.md 부터 읽고 이어서 진행
5. DAY 중간 중단도 안전 (DAY 경계가 강한 컨텍스트 분리점이지만 WIP 커밋으로 보완)
```

---

# 부록 F — 메타원칙 7개 위반 체크리스트 (매 DAY 종료 시 자동 점검)

| 원칙 | 위반 조건 |
|------|---------|
| #20 게으름→자동화 | 사용자가 반복 입력해야 하는 흐름이 추가됐는가? |
| #30 초기학습→자동화 | 자동화 전환 경로 없이 영구 HITL인 흐름이 있는가? |
| #36 RAG 메타학습 | 도메인 지식이 코드에 하드코딩됐는가? |
| #37 동적 기준값 | 임계값·기준값이 코드에 박혔는가? (DB·동적기준값 미사용) |
| #38 격리+공유 | 개인 데이터에 user_id 컬럼 누락? 공유 지식에 user_id 잘못 들어감? |
| #39 데이터 주권 | 불필요한 외부 호출이 추가됐는가? (캐시·로컬 우선?) |
| #50 Learning to Learn | 외부 LLM 결과가 학습 데이터로 저장되지 않는 경로가 있는가? |

---

> 본 PLAN_DAYS.md는 단계2~3 전 구현 기간의 단일 진실 공급원이다.
> 변경 시 git diff 명확히 남기고 사용자 승인 받을 것.
