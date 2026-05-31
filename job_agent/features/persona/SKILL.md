# features/persona SKILL

> 이 파일을 먼저 읽을 것 (CLAUDE.md 규칙).

## 역할

자소서·이력서 파일을 받아 페르소나 11섹션을 자동 추출·저장·관리한다.

## 외부 인터페이스

`interface.py` (보호 컴포넌트 — 버전 태그 확인 필수, DAY 05에서 함수 시그니처 확정)

## 구현 예정 (DAY 10~11)

- `internal/extractor.py` — docx/pdf/txt → 텍스트 파싱
- `internal/llm_extract.py` — Claude로 11섹션 추출
- `internal/storage.py` — DB 저장·갱신
- `internal/changelog.py` — 변경 이력 시계열 기록

## 수정 범위

- `internal/` 자유 수정 가능.
- `interface.py` 수정 → 사용자 승인 + 버전 bump 필수.
