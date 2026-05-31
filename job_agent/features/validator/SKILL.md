# features/validator SKILL

> 이 파일을 먼저 읽을 것 (CLAUDE.md 규칙).

## 역할

D 하이브리드 구조로 생성물을 검증한다: 1차 룰 엔진(비용 0) → 2차 LLM 검증 → Q3 재시도 루프.

## 외부 인터페이스

`interface.py` (보호 컴포넌트 — 버전 태그 확인 필수, DAY 05에서 함수 시그니처 확정)

## 구현 예정 (DAY 07, 20~21)

- `internal/rules/` — YAML 룰셋 4종 (자소서·코드·공고·면접)
- `internal/rule_engine.py` — YAML 룰 → 판정 함수
- `internal/llm_judge.py` — Claude 2차 검증
- `internal/retry_loop.py` — 실패 시 최대 3회 재시도, 초과 시 HITL 전달
- `internal/storage.py` — 전 과정 저장 (Q5)

## 검증 타이밍

- 자소서·면접·코드: 실시간 / 공고: 배치 (비용 절감)

## 수정 범위

- `internal/` 자유 수정 가능 (룰셋 YAML 포함).
- `interface.py` 수정 → 사용자 승인 + 버전 bump 필수.
