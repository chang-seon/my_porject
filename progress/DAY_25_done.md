# DAY 25 완료

> 완료일: 2026-05-31
> 단계: Phase 3

## 산출물

- `job_agent/features/learner/internal/rag/__init__.py`
- `job_agent/features/learner/internal/rag/embedder.py` — 한국어 n-gram 해시 임베딩 (128차원, 로컬 비용 0, sentence-transformers 교체 가능)
- `job_agent/features/learner/internal/rag/vector_store.py` — rag_knowledge CRUD + 코사인 유사도 검색
- `job_agent/features/learner/internal/rag/ingest.py` — 단건/일괄 적재, 회사 평판, 면접 기출
- `job_agent/features/learner/internal/rag/retriever.py` — 쿼리 검색, 회사 정보, 면접 기출 검색
- `tests/learner/test_rag.py` — 21/21 통과

## 기술 결정

- 임베딩: TF-IDF 해시 방식 (128차원, 로컬, 비용 0)
- 유사도: 코사인 유사도
- BLOB 저장: struct.pack/unpack (float32)
- 원칙 #39(데이터 주권) 준수: 로컬 전용, 외부 API 없음

## 테스트 결과

```
21 passed in 0.99s
```

## 다음 DAY 시작 시 읽을 파일

- `progress/DAY_25_done.md`
- `job_agent/features/job_search/internal/pass_handler.py`
- `job_agent/features/learner/internal/rag/retriever.py`
