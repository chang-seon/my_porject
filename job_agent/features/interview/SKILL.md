# features/interview SKILL

> 이 파일을 먼저 읽을 것 (CLAUDE.md 규칙).

## 역할

면접 준비 자료 생성(RAG 기출 기반)과 면접 후 회고를 지원한다.

## 외부 인터페이스

`interface.py` (보호 컴포넌트 — 버전 태그 확인 필수, DAY 05에서 함수 시그니처 확정)

## 구현 예정 (DAY 27)

- `internal/prep_generator.py` — RAG 기출 → Claude 모의 질문 생성
- `internal/debrief.py` — 회고 입력 → 학습신호 E층 적재

## 수정 범위

- `internal/` 자유 수정 가능.
- `interface.py` 수정 → 사용자 승인 + 버전 bump 필수.
