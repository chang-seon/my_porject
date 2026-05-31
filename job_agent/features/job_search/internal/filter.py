"""페르소나 제약조건으로 공고를 필터링한다."""
from __future__ import annotations

from pathlib import Path

from job_agent.shared.db.repositories.persona_repo import get_persona


def filter_by_persona(postings: list[dict], user_id: str, db_path: Path | None = None) -> dict:
    """페르소나의 제약조건(블랙리스트, 지역, 고용형태)으로 공고를 걸러낸다.

    반환: {"결과": "성공", "passed": list[dict], "filtered_out": int, "reasons": dict}
    """
    try:
        kwargs = {"db_path": db_path} if db_path else {}
        persona = get_persona(user_id, **kwargs)

        if persona is None:
            return {
                "결과": "성공",
                "passed": postings,
                "filtered_out": 0,
                "reasons": {"경고": "페르소나 없음 — 필터 미적용"},
            }

        constraints = persona.constraints or []
        blacklist_companies = {
            c.detail.lower()
            for c in constraints
            if c.type == "blacklist_company" and c.detail
        }
        blacklist_keywords = {
            c.detail.lower()
            for c in constraints
            if c.type == "blacklist_keyword" and c.detail
        }
        preferred_locations = {
            c.detail.lower()
            for c in constraints
            if c.type == "preferred_location" and c.detail
        }
        preferred_employment = {
            c.detail.lower()
            for c in constraints
            if c.type == "preferred_employment" and c.detail
        }

        passed: list[dict] = []
        filtered_out = 0
        reasons: dict[str, list[str]] = {}

        for p in postings:
            job_id = p.get("job_id", p.get("url", "unknown"))
            reason = _check_filters(
                p,
                blacklist_companies,
                blacklist_keywords,
                preferred_locations,
                preferred_employment,
            )
            if reason:
                filtered_out += 1
                reasons[str(job_id)] = reason
            else:
                passed.append(p)

        return {"결과": "성공", "passed": passed, "filtered_out": filtered_out, "reasons": reasons}
    except Exception as e:
        return {"결과": "실패", "이유": str(e)}


def _check_filters(
    posting: dict,
    blacklist_companies: set[str],
    blacklist_keywords: set[str],
    preferred_locations: set[str],
    preferred_employment: set[str],
) -> list[str]:
    """필터 위반 이유 목록을 반환한다. 빈 리스트면 통과."""
    reasons: list[str] = []

    company = (posting.get("company") or "").lower()
    if any(bl in company for bl in blacklist_companies):
        reasons.append(f"블랙리스트 회사: {company}")

    title = (posting.get("title") or "").lower()
    raw = (posting.get("raw_text") or "").lower()
    for kw in blacklist_keywords:
        if kw in title or kw in raw:
            reasons.append(f"블랙리스트 키워드: {kw}")
            break

    if preferred_locations:
        location = (posting.get("location") or "").lower()
        if not any(loc in location for loc in preferred_locations):
            reasons.append(f"선호 지역 불일치: {location}")

    if preferred_employment:
        emp = (posting.get("employment_type") or "").lower()
        if emp and not any(e in emp for e in preferred_employment):
            reasons.append(f"선호 고용형태 불일치: {emp}")

    return reasons
