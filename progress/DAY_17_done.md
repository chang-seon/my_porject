# DAY 17 완료

> 완료일: 2026-05-31
> 단계: Phase 2

## 산출물

- `job_agent/features/job_search/internal/sources/base.py` — JobSource 추상 기반 클래스
- `job_agent/features/job_search/internal/sources/__init__.py`
- `job_agent/features/job_search/internal/sources/saramin.py` — 사람인 Open API 클라이언트 (지수 backoff, 3회 재시도)
- `job_agent/features/job_search/internal/normalizer.py` — 4개 소스(사람인/워크넷/잡알리오/Gemini) → JobPosting 표준 dict 변환 + deduplicate
- `tests/job_search/__init__.py`
- `tests/job_search/test_saramin.py` — 19/19 통과

## 테스트 결과

```
19 passed in 0.12s
```

## 다음 DAY 시작 시 읽을 파일

- `progress/DAY_17_done.md`
- `job_agent/features/job_search/internal/sources/saramin.py`
- `job_agent/features/job_search/internal/normalizer.py`
