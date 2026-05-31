"""소스별 원본 공고 데이터 → JobPosting 표준 JSON 변환."""
from __future__ import annotations

from datetime import datetime


def normalize_saramin(raw: dict) -> dict:
    """사람인 API 원본 항목 → JobPosting dict."""
    try:
        position = raw.get("position", {})
        company = raw.get("company", {})
        detail = raw.get("url", {})

        posted_str = raw.get("posting-date", "") or raw.get("posted-date", "")
        deadline_str = raw.get("expiration-date", "")

        year, month, day = _parse_ymd(posted_str)

        skills_raw = position.get("job-code", {})
        if isinstance(skills_raw, dict):
            skills_text = skills_raw.get("#text", "") or ""
        else:
            skills_text = str(skills_raw) if skills_raw else ""
        skills = [s.strip() for s in skills_text.split(",") if s.strip()] if skills_text else []

        return {
            "job_id": str(raw.get("id", "")),
            "source": "사람인",
            "url": detail if isinstance(detail, str) else (detail.get("#text", "") if isinstance(detail, dict) else ""),
            "title": position.get("title", ""),
            "company": company.get("detail", {}).get("name", "") if isinstance(company.get("detail"), dict) else "",
            "location": _extract_location(position),
            "job_role": position.get("title", ""),
            "employment_type": _extract_employment(position),
            "salary": raw.get("salary", {}).get("#text", "") if isinstance(raw.get("salary"), dict) else None,
            "skills_required": skills,
            "raw_text": None,
            "posted_date": posted_str or None,
            "deadline": deadline_str or None,
            "year": year,
            "month": month,
            "day": day,
        }
    except Exception as e:
        return {"결과": "실패", "이유": f"사람인 정규화 오류: {e}"}


def normalize_worknet(raw: dict) -> dict:
    """워크넷 원본 항목 → JobPosting dict."""
    try:
        posted_str = raw.get("REGIST_DT", "") or raw.get("regist_dt", "")
        deadline_str = raw.get("DEADLINE_DT", "") or raw.get("deadline_dt", "")
        year, month, day = _parse_ymd(posted_str)

        skills_text = raw.get("REQUIRED_CAREER", "") or raw.get("required_career", "") or ""
        skills = [s.strip() for s in skills_text.split(",") if s.strip()] if skills_text else []

        return {
            "job_id": str(raw.get("JO_SN", raw.get("jo_sn", ""))),
            "source": "워크넷",
            "url": raw.get("WANTEDMAIN_URL", raw.get("wantedmain_url", "")),
            "title": raw.get("JO_NM", raw.get("jo_nm", "")),
            "company": raw.get("CMPNY_NM", raw.get("cmpny_nm", "")),
            "location": raw.get("WORK_REGION_NM", raw.get("work_region_nm", "")),
            "job_role": raw.get("OCCUPATION_NM", raw.get("occupation_nm", "")),
            "employment_type": raw.get("EMPLMT_STLE_NM", raw.get("emplmt_stle_nm", "")),
            "salary": raw.get("SALARY_COND_NM", raw.get("salary_cond_nm", "")),
            "skills_required": skills,
            "raw_text": None,
            "posted_date": posted_str or None,
            "deadline": deadline_str or None,
            "year": year,
            "month": month,
            "day": day,
        }
    except Exception as e:
        return {"결과": "실패", "이유": f"워크넷 정규화 오류: {e}"}


def normalize_joballio(raw: dict) -> dict:
    """잡알리오 원본 항목 → JobPosting dict."""
    try:
        posted_str = raw.get("reg_date", "")
        deadline_str = raw.get("end_date", "")
        year, month, day = _parse_ymd(posted_str)

        skills_text = raw.get("req_skill", "") or ""
        skills = [s.strip() for s in skills_text.split(",") if s.strip()] if skills_text else []

        return {
            "job_id": str(raw.get("recruit_no", "")),
            "source": "잡알리오",
            "url": raw.get("url", ""),
            "title": raw.get("title", ""),
            "company": raw.get("company_nm", ""),
            "location": raw.get("work_place", ""),
            "job_role": raw.get("occupation", ""),
            "employment_type": raw.get("emp_type", ""),
            "salary": raw.get("salary", ""),
            "skills_required": skills,
            "raw_text": None,
            "posted_date": posted_str or None,
            "deadline": deadline_str or None,
            "year": year,
            "month": month,
            "day": day,
        }
    except Exception as e:
        return {"결과": "실패", "이유": f"잡알리오 정규화 오류: {e}"}


def normalize_gemini(raw: dict) -> dict:
    """Gemini 웹탐색 결과 → JobPosting dict (표준 필드 그대로 전달)."""
    try:
        posted_str = raw.get("posted_date", "")
        year, month, day = _parse_ymd(posted_str)

        skills = raw.get("skills_required", [])
        if isinstance(skills, str):
            skills = [s.strip() for s in skills.split(",") if s.strip()]

        return {
            "job_id": str(raw.get("job_id", "")),
            "source": raw.get("source", "기타"),
            "url": raw.get("url", ""),
            "title": raw.get("title", ""),
            "company": raw.get("company", ""),
            "location": raw.get("location"),
            "job_role": raw.get("job_role"),
            "employment_type": raw.get("employment_type"),
            "salary": raw.get("salary"),
            "skills_required": skills,
            "raw_text": raw.get("raw_text"),
            "posted_date": posted_str or None,
            "deadline": raw.get("deadline"),
            "year": year,
            "month": month,
            "day": day,
        }
    except Exception as e:
        return {"결과": "실패", "이유": f"Gemini 정규화 오류: {e}"}


def deduplicate(postings: list[dict]) -> list[dict]:
    """URL 기준 중복 공고를 제거한다."""
    seen: set[str] = set()
    result: list[dict] = []
    for p in postings:
        url = p.get("url", "")
        if url and url in seen:
            continue
        if url:
            seen.add(url)
        result.append(p)
    return result


def _parse_ymd(date_str: str) -> tuple[int | None, int | None, int | None]:
    """날짜 문자열에서 year, month, day를 추출한다."""
    if not date_str:
        return None, None, None
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y%m%d", "%Y-%m-%dT%H:%M:%S"):
        try:
            dt = datetime.strptime(date_str[:len(fmt.replace("%Y", "0000").replace("%m", "00").replace("%d", "00").replace("%H", "00").replace("%M", "00").replace("%S", "00"))], fmt)
            return dt.year, dt.month, dt.day
        except ValueError:
            continue
    return None, None, None


def _extract_location(position: dict) -> str | None:
    loc = position.get("location", {})
    if isinstance(loc, dict):
        return loc.get("#text") or loc.get("name")
    return str(loc) if loc else None


def _extract_employment(position: dict) -> str | None:
    emp = position.get("job-type", {})
    if isinstance(emp, dict):
        return emp.get("#text") or emp.get("name")
    return str(emp) if emp else None
