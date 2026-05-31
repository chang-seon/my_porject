# interface version: 1.0
from __future__ import annotations


def fetch_postings(query: dict) -> dict:
    """공고 수집 쿼리(직무·지역·고용형태)로 전체 소스에서 공고를 가져온다.

    query 필드: job_role, location, employment_type, sources(list)
    반환: {"결과": "성공", "postings": list[dict], "total": int}
    """
    try:
        raise NotImplementedError
    except NotImplementedError:
        raise
    except Exception as e:
        return {"결과": "실패", "이유": str(e)}


def filter_postings(postings: list[dict], user_id: str) -> dict:
    """페르소나 제약 조건으로 공고를 필터링하고 패스 처리한다.

    반환: {"결과": "성공", "passed": list[dict], "filtered_out": int, "pass_recorded": int}
    """
    try:
        raise NotImplementedError
    except NotImplementedError:
        raise
    except Exception as e:
        return {"결과": "실패", "이유": str(e)}


def get_posting(job_id: str) -> dict:
    """저장된 공고 단건을 조회한다."""
    try:
        raise NotImplementedError
    except NotImplementedError:
        raise
    except Exception as e:
        return {"결과": "실패", "이유": str(e)}
