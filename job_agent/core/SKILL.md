# core/ SKILL

> 이 파일을 먼저 읽을 것 (CLAUDE.md 규칙).

## 역할

모듈간 유일한 중재자(오케스트레이터). features/ 모듈끼리 직접 호출 금지 — 반드시 core를 거친다.

## 포함 예정 파일 (DAY 06)

- `orchestrator.py` — 11단계 파이프라인 함수 모음
- `router.py` — 모듈간 호출 중재
- `hitl_bus.py` — HITL 요청·응답 큐 (DAY 14)

## 수정 규칙

- core/ 전체가 보호 컴포넌트. **사용자 승인 없이 수정 금지** (CLAUDE.md 보호 컴포넌트 수정 절차 참조).
- features/끼리 직접 import 금지 → lint 룰로 강제 (DAY 09).
