# interface version: 1.0
from __future__ import annotations


def prepare(job_id: str, user_id: str, job_posting: dict | None = None, skip_llm: bool = False) -> dict:
    """공고 + 페르소나 + RAG 기반으로 면접 준비 자료를 생성한다.

    반환: {"결과": "성공", "questions": list[str], "tips": list[str], "company_info": dict}
    """
    try:
        from job_agent.features.interview.internal.prep_generator import generate_prep
        return generate_prep(job_posting or {"job_id": job_id}, skip_llm=skip_llm)
    except Exception as e:
        return {"결과": "실패", "이유": str(e)}


def debrief(application_id: str, feedback: str, user_id: str, questions: list | None = None, result: str = "") -> dict:
    """면접 회고를 기록하고 학습신호(B·C층)를 적재한다.

    반환: {"결과": "성공", "signals_recorded": int}
    """
    try:
        from job_agent.features.interview.internal.debrief import record_debrief
        return record_debrief(application_id, feedback, user_id, questions, result)
    except Exception as e:
        return {"결과": "실패", "이유": str(e)}
