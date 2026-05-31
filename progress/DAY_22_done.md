# DAY 22 완료

> 완료일: 2026-05-31
> 단계: Phase 2

## 산출물

- `job_agent/features/document/internal/prompts/generate_cover_letter.md` — LLM 자소서 생성 프롬프트 (사실 일치 원칙, 6종 문체 마커, 4종 안티패턴)
- `job_agent/features/document/internal/pool_loader.py` — 페르소나 DB에서 3-풀(콘텐츠/문체/안티) 로드
- `job_agent/features/document/internal/synthesizer.py` — Claude 호출, SHA256[:16] draft_id, 지연 초기화
- `tests/document/__init__.py`
- `tests/document/test_synthesizer.py` — 8/8 통과

## 기술 결정

- draft_id = SHA256[:16] (결정론적, 같은 내용 → 같은 ID)
- `_get_router()` 지연 초기화 패턴 유지 (API 키 없는 환경에서 import 실패 방지)
- 프롬프트 플레이스홀더: `{{job_posting}}` `{{content_pool}}` `{{style_markers}}` `{{anti_patterns}}`

## 테스트 결과

```
8 passed in 2.82s
```

## 다음 DAY 시작 시 읽을 파일

- `progress/DAY_22_done.md`
- `job_agent/features/document/internal/synthesizer.py`
- `job_agent/features/validator/internal/retry_loop.py`
