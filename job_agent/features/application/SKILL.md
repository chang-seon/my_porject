# features/application SKILL

> 이 파일을 먼저 읽을 것 (CLAUDE.md 규칙).

## 역할

지원 현황을 기록하고 추적한다. v1은 링크 전달 방식.

## 외부 인터페이스

`interface.py` (보호 컴포넌트 — 버전 태그 확인 필수, DAY 05에서 함수 시그니처 확정)

## 구현 예정 (DAY 24)

- `internal/recorder.py` — 지원·결과(합격/탈락/미응답) 추적
- `internal/link_handler.py` — v1: 지원 링크 전달

## 수정 범위

- `internal/` 자유 수정 가능.
- `interface.py` 수정 → 사용자 승인 + 버전 bump 필수.
