# 초개인화 구직 에이전트 v1.0.0

어창선 본인만을 위한 자소서 생성·검증·지원 자동화 시스템.

## 현재 상태

**MVP 완성 (v1.0.0)**

| 단계 | 범위 | 상태 |
|------|------|------|
| 단계2 DAY 01~09 | 사양 구체화 | ✅ 완료 (v0.1.0-spec-frozen) |
| Phase 1 DAY 10~16 | persona·notification·learner 기반 | ✅ 완료 (v0.2.0-phase1) |
| Phase 2 DAY 17~24 | job_search·validator·document 핵심 | ✅ 완료 (v0.3.0-phase2) |
| Phase 3 DAY 25~30 | RAG·interview·대시보드·E2E | ✅ 완료 (v1.0.0) |

## 11단계 파이프라인

```
① 셋업        — 이력서 파싱 → Claude 11섹션 추출 → DB 저장
② 공고 수집   — 사람인·워크넷·잡알리오·Gemini 4소스 → 중복 제거
③ 필터링      — 페르소나 제약(지역·고용형태·블랙리스트) + 패스 기록
④ 자소서 생성 — 3-풀(콘텐츠·구조·문체) → Claude 합성
⑤ 검증AI      — 1차 YAML 룰(무비용) + 2차 LLM 심사 → Q3 재시도
⑥ HITL 1      — 자소서 검토 요청 (승인/수정/폐기)
⑦ 지원 실행   — 지원 기록 DB 저장 + 링크 알림
⑧ 결과 추적   — 서류·면접·합격/불합격 상태 갱신
⑨ 패스 처리   — 동일조건 반복 차단 + RAG 평판 자동 패스
⑩ 면접 준비   — RAG 기출 + Claude 모의 질문
⑪ 면접 회고   — B/C/E층 학습신호 + RAG 자동 누적
```

## 설치 및 실행

```bash
# 1. 가상환경 생성 및 활성화
python -m venv .venv
.venv\Scripts\Activate.ps1

# 2. 패키지 설치
pip install -r requirements.txt

# 3. 환경 변수 설정 (.env 파일 생성)
ANTHROPIC_API_KEY=<키>
GOOGLE_AI_API_KEY=<키>
SARAMIN_API_KEY=<키>
TELEGRAM_BOT_TOKEN=<토큰>
TELEGRAM_CHAT_ID=<chat_id>
DB_PATH=D:\IT\Agentic_AI\data\agent.db

# 4. DB 초기화
python -m job_agent.shared.db.connection --init

# 5. 테스트 실행
python -m pytest tests/ -q
```

## 대시보드

```bash
python -m tools.dashboard.server
# 브라우저에서 http://localhost:8080 접속
```

표시 항목: LLM 비용 | HITL 대기 | 검증 통과율 | 자동화 수준 | 지원 현황

## 프로젝트 구조

```
job_agent/
├── core/           # orchestrator (11단계), router, hitl_bus
├── shared/
│   ├── db/         # SQLite WAL, 마이그레이션, persona_repo
│   ├── llm/        # Claude·Gemini 클라이언트, LLMRouter, cost_tracker
│   └── schemas/    # Pydantic 모델 (JobPosting, Persona, LearningSignal, EventLog)
└── features/
    ├── persona/    # 이력서 파싱, LLM 추출, DB 저장, changelog
    ├── job_search/ # 4소스 수집, 정규화, 필터링, 패스, 회사분석
    ├── document/   # 3-풀 로드, Claude 합성, pipeline
    ├── validator/  # YAML 룰엔진, LLM 심사, Q3 재시도
    ├── notification/ # 텔레그램 단방향
    ├── application/  # 지원 기록, 링크 핸들러
    ├── interview/    # 면접 준비, 회고
    └── learner/      # 학습신호 5층, RAG, auto_promotion
tools/
├── dashboard/      # FastAPI 대시보드
├── hitl_cli.py     # HITL 응답 CLI
└── lint_imports.py # features/ 직접 import 금지 lint
```

## 메타원칙

| 원칙 | 구현 |
|------|------|
| #20 자동화 | 일일 사이클 자동 실행 |
| #30 초기→자동화 | auto_promotion: N회 통과 → 자동화 단계 상승 |
| #36 RAG 메타학습 | 면접 경험 → RAG 자동 누적 |
| #37 동적 기준값 | dynamic_thresholds (N=5 등 DB에서 관리) |
| #38 격리+공유 | user_id 모든 개인 테이블 |
| #39 데이터 주권 | 로컬 임베딩, 외부 API 최소화 |
| #50 Learning to Learn | 학습신호 A~E층 전 과정 저장 |

## 테스트

```
총 262개 테스트 (전부 통과)
```

## 기술 스택

- Python 3.10, SQLite WAL, Pydantic v2
- anthropic SDK (Claude Sonnet/Opus), google-genai (Gemini)
- FastAPI (대시보드), python-telegram-bot (알림)
- pytest (테스트)
