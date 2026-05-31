# interface version: 1.0
from __future__ import annotations


def validate(target: str, content: str, context: dict | None = None) -> dict:
    """1차 룰 엔진 + 2차 LLM으로 콘텐츠를 검증한다.

    target: "cover_letter" | "code" | "job_posting" | "interview"
    반환: {"결과": "성공", "passed": bool, "score": float,
           "issues": list[dict], "retry_count": int}
    """
    try:
        raise NotImplementedError
    except NotImplementedError:
        raise
    except Exception as e:
        return {"결과": "실패", "이유": str(e)}


def get_validation_history(reference_id: str) -> dict:
    """특정 대상의 검증 이력을 조회한다."""
    try:
        raise NotImplementedError
    except NotImplementedError:
        raise
    except Exception as e:
        return {"결과": "실패", "이유": str(e)}
