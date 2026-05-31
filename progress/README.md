# progress/ 폴더 사용 규칙

이 폴더는 **DAY별 진행 상태**의 단일 진실 공급원이다.
새 세션에서 컨텍스트를 복원할 때 가장 먼저 읽는 곳.

## 파일 규칙

- `DAY_NN_done.md` — 각 DAY 종료 시 1개 생성 (`_TEMPLATE.md` 복사해서 채움)
- `WEEK_N_summary.md` — 매주 일요일 1개 (Sonnet으로 작성 충분)
- `INTERFACE_VERSIONS.md` — 보호 컴포넌트 버전 단일 기록부
- `MVP_DONE.md` — DAY 30 종료 시 1개

## 새 세션 시작 시 읽기 순서

1. `PLAN_DAYS.md` (해당 DAY 카드)
2. `progress/DAY_<직전>_done.md`
3. `progress/INTERFACE_VERSIONS.md`
4. 필요 시 `decisions/OPEN_ITEMS_RESOLVED.md`

## 중단(WIP) 시 작성 규칙

- `DAY_NN_done.md`에 "상태: ⏸️ 중단(WIP)" + 진행률 + 남은 작업 명시
- `.draft` 확장자 파일들 목록도 함께 기록
- git WIP 커밋 메시지: `DAY N WIP: <남은 작업>`
