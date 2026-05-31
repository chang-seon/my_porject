# 미결 사항 일괄 결정 기록 (DAY 08)

> 작성일: 2026-05-31
> 결정 방식: 합리적 기본값 적용 (운영 시 데이터 기반으로 갱신 예정)

---

## M1 — 이메일 자동 확인 방식

**결정: 본인 직접 입력**

- OAuth 연동은 보안 복잡도가 높고 v1 범위 초과
- 합격/불합격 결과는 사용자가 CLI 또는 텔레그램으로 직접 입력
- v1.1에서 Gmail OAuth 연동 검토
- 적용 위치: `features/application/internal/` 결과 수동 입력 흐름

---

## M4 — 자동화 전환 임계값 N

**결정: N = 5**

- 검증AI가 5회 연속 OK 판정 시 해당 단계 자동화 전환
- 초기값 5는 보수적 기준 — 운영 후 dynamic_thresholds 테이블에서 조정 가능
- 적용 위치: `features/learner/internal/auto_promotion.py` (DAY 28)

---

## M5 — 페르소나 보강 질문 목록 (5개)

**결정: 아래 5개 질문으로 확정**

1. 현재 가장 자신 있는 기술 스택과 최근 사용한 프로젝트를 알려주세요.
2. 지원을 절대 피하고 싶은 회사 유형 또는 조건이 있나요? (예: 대기업 제외, 마곡 외 지역 제외)
3. 자소서에서 가장 강조하고 싶은 경험이나 에피소드 3가지를 말씀해 주세요.
4. 합격 가능성보다 성장 가능성을 우선하시나요, 아니면 안정성을 우선하시나요?
5. 현재 취업 준비에서 가장 불안한 부분이 무엇인가요?

- 적용 위치: `features/persona/internal/supplement_questions.py` (DAY 10)

---

## M6 — 추가 정보 부족 시 판단 로직

**결정: HITL 요청 후 대기**

- 페르소나 필수 섹션(신원·목표직무·스킬)이 비어 있으면 자동 진행 중단
- 텔레그램으로 보강 질문(M5) 발송 → 사용자 응답 대기
- 응답 없이 24시간 경과 시 해당 공고 보류(pending) 처리
- 적용 위치: `core/orchestrator.py` run_setup 단계

---

## M7 — 콘텐츠 풀 직무별 라벨링 체계

**결정: 5분류 라벨**

| 라벨 | 설명 | 예시 |
|------|------|------|
| `ai_ml` | AI·머신러닝·데이터사이언스 | RAG, LLM, PyTorch |
| `data_eng` | 데이터 엔지니어링·파이프라인 | ETL, Spark, Airflow |
| `backend` | 백엔드·서버 개발 | FastAPI, DB, API |
| `frontend` | 프론트엔드·UI | React, Vue |
| `general` | 공통 (직무 무관) | 커뮤니케이션, 협업 |

- 콘텐츠 자산 `tags` 필드에 라벨 포함 방식으로 적용
- 자소서 생성 시 지원 직무와 라벨이 일치하는 자산 우선 사용
- 적용 위치: `shared/schemas/persona.py` ContentAsset.tags (기존 list[str] 그대로 사용)

---

## M8 — 잡코리아 포함 여부

**결정: 제외**

- 잡코리아는 크롤링 방지 정책이 강하고 공식 API 없음 (#39 데이터 주권 원칙 충돌)
- 사람인(공식 API) + 워크넷(공공데이터) + 잡알리오(공공데이터)로 충분
- v2에서 재검토 가능
- 적용 위치: `features/job_search/internal/sources/` 소스 목록

---

## M9 — 텔레그램 단방향 vs 양방향

**결정: 단방향 (v1)**

- v1: 텔레그램 알림 발송만 (bot → 사용자)
- 사용자 응답은 CLI(`tools/hitl_cli.py`)로 수신
- 양방향(webhook + FastAPI)은 v1.1로 이월
- 적용 위치: `features/notification/internal/telegram_sender.py` (DAY 12)

---

## M10 — 공고 갱신 트리거

**결정: 매일 오전 9시 자동 갱신**

- 크론 스케줄: `0 9 * * *`
- 갱신 범위: 전체 소스 (사람인·워크넷·잡알리오)
- 중복 공고는 URL 기준으로 스킵
- 만료 공고(deadline < today)는 자동 비활성화
- 적용 위치: `tools/scheduler.py` (Phase 3에서 구현, v1은 수동 실행)
