# features/notification SKILL

> 이 파일을 먼저 읽을 것 (CLAUDE.md 규칙).

## 역할

텔레그램을 통해 공고 알림·자소서 검토 요청·HITL 요청을 전송한다.

## 외부 인터페이스

`interface.py` (보호 컴포넌트 — 버전 태그 확인 필수, DAY 05에서 함수 시그니처 확정)

## 구현 예정 (DAY 12)

- `internal/telegram_sender.py` — Bot API 래퍼
- `internal/templates/` — 메시지 템플릿 (자소서검토·공고알림·HITL요청)

## 미결 의존

- M9 (단방향 vs 양방향) — DAY 08에서 결정. 양방향 시 webhook + FastAPI 추가 검토.

## 수정 범위

- `internal/` 자유 수정 가능.
- `interface.py` 수정 → 사용자 승인 + 버전 bump 필수.
