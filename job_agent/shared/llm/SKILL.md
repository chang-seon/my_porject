# shared/llm/ SKILL

> 이 파일을 먼저 읽을 것 (CLAUDE.md 규칙).

## 역할

모든 LLM 호출의 단일 진입점. 모든 features/는 반드시 `LLMRouter`를 통해 호출한다.

## 사용법

```python
from job_agent.shared.llm import LLMRouter

router = LLMRouter()
result = router.generate(
    prompt="...",
    task_type="implementation",   # 아래 작업 유형 참조
    system="...",                 # 선택
    source_module="validator",    # 비용 추적용
)
```

## 작업 유형별 모델 라우팅

| task_type | 모델 | 용도 |
|-----------|------|------|
| `architecture_review` | Opus | 설계·정합성 검토 |
| `interface_design` | Opus | interface.py 설계 |
| `decision` | Opus | 미결 항목 결정 보조 |
| `implementation` | Sonnet | 구현 코드 생성 |
| `test` | Sonnet | 테스트 코드 |
| `document` | Sonnet | 문서화 |
| `web_search` | Gemini | 웹 검색·공고 수집 |
| `fallback` | Sonnet | 기본값 |

## 비용 추적

- 모든 호출 자동으로 `cost_log` 테이블에 적재
- `get_daily_summary(year, month, day)` 로 일별 조회
- DAY 29 대시보드에서 시각화 예정 (#54)

## 수정 규칙

- shared/llm/ 는 보호 컴포넌트 외부 — 사용자 승인 불필요
- 새 모델 추가 시: `_ROUTING`, `_COST_PER_1K` 두 곳 동시 업데이트
- API 키는 반드시 `.env`에서만 로드
