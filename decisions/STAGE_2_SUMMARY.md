# 단계2 사양 구체화 완료 요약

> 완료일: 2026-05-31
> 커버 범위: DAY 01 ~ DAY 09

---

## 완료된 DAY 목록

| DAY | 주제 | 핵심 산출물 | 테스트 |
|-----|------|-----------|--------|
| DAY 01 | 레포 골격 | job_agent/ 폴더 트리, 8개 플레이스홀더 | 0 items ✅ |
| DAY 02 | JSON 표준 포맷 (M13 확정) | Pydantic 모델 4종 | 11/11 ✅ |
| DAY 03 | DB 스키마 + SQLite 추상화 | 17개 테이블, persona_repo | 4/4 ✅ |
| DAY 04 | LLM 호출 추상화 | Claude·Gemini 클라이언트, 라우터, 비용추적 | 9/9 ✅ |
| DAY 05 | interface.py 시그니처 확정 | 8개 모듈 interface v1.0 | 16/16 ✅ |
| DAY 06 | core 오케스트레이터 골격 | orchestrator(11단계 stub), router | 13/13 ✅ |
| DAY 07 | 검증AI 룰셋 초안 (Q4 잠정) | YAML 4종, LLM 심사 프롬프트 | 12/12 ✅ |
| DAY 08 | 미결 8건 결정 | OPEN_ITEMS_RESOLVED.md | 문서 ✅ |
| DAY 09 | lint 룰 + 마감 검수 | lint_imports.py, .pre-commit, README | 65/65 ✅ |

---

## 확정된 기술 결정 (전체)

| 항목 | 결정 |
|------|------|
| M13 데이터 타입 | nested Pydantic / str ISO8601 / list[str] / Optional=None |
| Q4 룰셋 작성 주체 | Claude 초안 (잠정, 운영 후 보강) |
| M1 이메일 처리 | 본인 직접 입력 (v1.1 OAuth) |
| M4 자동화 임계값 | N=5 |
| M5 보강 질문 | 5개 확정 |
| M6 정보 부족 시 | HITL → 24h 무응답 시 보류 |
| M7 직무 라벨 | ai_ml / data_eng / backend / frontend / general |
| M8 잡코리아 | 제외 (#39) |
| M9 텔레그램 | 단방향 v1 |
| M10 공고 갱신 | 매일 오전 9시 크론 |

---

## 단계3 진입 조건 체크

- [x] 폴더 구조 확정
- [x] Pydantic 스키마 round-trip 통과
- [x] DB 17개 테이블 생성, idempotent 마이그레이션
- [x] LLM 라우터 mock 테스트 통과
- [x] interface.py 8개 v1.0 확정
- [x] core/ 11단계 파이프라인 stub
- [x] 검증AI 룰셋 YAML 4종
- [x] 미결 M1·M4~M10 전부 결정
- [x] lint_imports.py clean
- [x] 전체 테스트 65/65 통과

**→ 단계3 Phase 1 진입 가능**
