# shared/ SKILL

> 이 파일을 먼저 읽을 것 (CLAUDE.md 규칙).

## 역할

모든 features/가 공통으로 사용하는 유틸리티 계층.

## 포함 하위 폴더

| 폴더 | 내용 | 작성 DAY |
|------|------|---------|
| `schemas/` | Pydantic 모델 (JobPosting, Persona, LearningSignal 등) | DAY 02 ✅ |
| `db/` | SQLite 추상화 계층, repositories | DAY 03 |
| `llm/` | Claude/Gemini 클라이언트, 라우터, 비용 추적 | DAY 04 |

## schemas/ 사용법 (DAY 02 완료)

```python
from job_agent.shared.schemas import Persona, JobPosting, LearningSignal, EventLog
```

### 공통 규칙 (M13 확정)
- 복합 필드: nested Pydantic 모델
- 날짜: `str` ISO8601 (`"2026-05-30"`) + `year/month/day` int 계층 인덱스 동시 보관 (#37)
- 리스트: `list[str]` 또는 `list[모델]`
- 미입력 필드: `Optional[X] = None`
- 모든 모델: `model_config = ConfigDict(extra="forbid")` (오타 차단)
- 개인 데이터 모델: `user_id: str` 필수 (#38)

## 수정 규칙

- shared/는 보호 컴포넌트 외부 — interface.py 없음, 사용자 승인 불필요.
- 단, schemas/ 변경 시 연관 interface.py 버전에 영향 없는지 확인할 것.
