# features/learner SKILL

> 이 파일을 먼저 읽을 것 (CLAUDE.md 규칙).

## 역할

학습 신호 5층을 수집하고, 동적기준값을 관리하며, RAG 메타학습과 자동화 전환 로직을 담당한다.

## 외부 인터페이스

`interface.py` (보호 컴포넌트 — 버전 태그 확인 필수, DAY 05에서 함수 시그니처 확정)

## 구현 예정

- `internal/signal_collector.py` — A~E 5층 신호 수집 (DAY 15)
- `internal/dynamic_threshold.py` — DB 기반 동적기준값 read/write (DAY 15)
- `internal/rag/` — 벡터스토어·인제스트·리트리버 (DAY 25)
- `internal/auto_promotion.py` — 검증AI N회 OK → 자동화 전환 (DAY 28)

## 핵심 원칙

- 동적기준값은 DB에서만 읽음. 코드 하드코딩 금지 (#37).
- 학습 데이터: 라벨여부·타임스탬프·컨텍스트·수정이력 반드시 보존 (#50).

## 수정 범위

- `internal/` 자유 수정 가능.
- `interface.py` 수정 → 사용자 승인 + 버전 bump 필수.
