# features/job_search SKILL

> 이 파일을 먼저 읽을 것 (CLAUDE.md 규칙).

## 역할

채용공고를 API·웹탐색으로 수집하고, 페르소나 제약조건으로 필터링·매칭한다.

## 외부 인터페이스

`interface.py` (보호 컴포넌트 — 버전 태그 확인 필수, DAY 05에서 함수 시그니처 확정)

## 구현 예정 (DAY 17~19)

- `internal/sources/saramin.py` — 사람인 API
- `internal/sources/worknet.py` — 워크넷 OpenAPI
- `internal/sources/joballio.py` — 잡알리오
- `internal/sources/gemini_web.py` — API 없는 사이트 Gemini 탐색
- `internal/normalizer.py` — 소스별 공고 → JobPosting 표준 JSON
- `internal/filter.py` — 페르소나 제약조건 대조
- `internal/pass_handler.py` — 패스·배제 처리

## 수정 범위

- `internal/` 자유 수정 가능.
- `interface.py` 수정 → 사용자 승인 + 버전 bump 필수.
