# features/document SKILL

> 이 파일을 먼저 읽을 것 (CLAUDE.md 규칙).

## 역할

페르소나 + 공고를 입력받아 본인 문체로 자소서·이력서 초안을 자동 생성한다.

## 외부 인터페이스

`interface.py` (보호 컴포넌트 — 버전 태그 확인 필수, DAY 05에서 함수 시그니처 확정)

## 구현 예정 (DAY 22~23)

- `internal/pool_loader.py` — 콘텐츠·구조·문체 3-풀 로드
- `internal/synthesizer.py` — Claude 호출 + 본인 문체 마커 주입
- `internal/pipeline.py` — 생성 → 검증AI → 재시도 → HITL2

## 핵심 정책

- "있는 사실 안에서 거짓말" — 콘텐츠 풀에 없는 사실 창작 금지.
- 문체 마커 6종 반드시 반영, GPT 안티패턴 4종 회피.

## 수정 범위

- `internal/` 자유 수정 가능.
- `interface.py` 수정 → 사용자 승인 + 버전 bump 필수.
