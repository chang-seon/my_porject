# interface version: 1.0
from __future__ import annotations


def generate_cover_letter(job_id: str, user_id: str, job_posting: dict | None = None, skip_llm: bool = False) -> dict:
    """공고 + 페르소나 3-풀 기반으로 자소서 초안을 생성하고 검증한다.

    반환: {"결과": "성공", "draft_id": str, "content": str,
           "validation": dict, "token_used": int}
    """
    try:
        from job_agent.features.document.internal.pipeline import generate_and_validate
        _posting = job_posting or {"job_id": job_id}
        return generate_and_validate(_posting, user_id, skip_llm=skip_llm)
    except Exception as e:
        return {"결과": "실패", "이유": str(e)}


def get_draft(draft_id: str) -> dict:
    """생성된 자소서 초안을 조회한다."""
    try:
        from job_agent.features.document.internal.pipeline import get_draft as _get
        return _get(draft_id)
    except Exception as e:
        return {"결과": "실패", "이유": str(e)}


def update_draft(draft_id: str, content: str, reason: str, user_id: str = "") -> dict:
    """사용자가 수정한 자소서를 저장하고 학습신호 C층에 기록한다."""
    try:
        from job_agent.features.document.internal.pipeline import update_draft as _update
        return _update(draft_id, content, reason, user_id)
    except Exception as e:
        return {"결과": "실패", "이유": str(e)}
