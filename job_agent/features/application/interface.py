# interface version: 1.0
from __future__ import annotations


def record_application(job_id: str, user_id: str, draft_id: str, job_posting: dict | None = None) -> dict:
    """지원 기록을 생성하고 지원 링크를 반환한다.

    반환: {"결과": "성공", "application_id": str, "apply_url": str}
    """
    try:
        from job_agent.features.application.internal.recorder import record_application as _record
        return _record(job_id, user_id, draft_id, job_posting)
    except Exception as e:
        return {"결과": "실패", "이유": str(e)}


def update_application_status(application_id: str, status: str, user_id: str = "", result: str | None = None) -> dict:
    """지원 결과를 갱신하고 학습신호 E층에 기록한다.

    status: "지원완료" | "서류통과" | "면접" | "최종합격" | "불합격"
    """
    try:
        from job_agent.features.application.internal.recorder import update_application_status as _update
        return _update(application_id, status, user_id, result)
    except Exception as e:
        return {"결과": "실패", "이유": str(e)}


def get_application_history(user_id: str) -> dict:
    """전체 지원 이력을 조회한다."""
    try:
        from job_agent.features.application.internal.recorder import get_application_history as _history
        return _history(user_id)
    except Exception as e:
        return {"결과": "실패", "이유": str(e)}
