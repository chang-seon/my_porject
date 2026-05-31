"""4개 소스 통합 호출 → 정규화 → 중복 제거."""
from __future__ import annotations

from job_agent.features.job_search.internal.sources.saramin import SaraminSource
from job_agent.features.job_search.internal.sources.worknet import WorknetSource
from job_agent.features.job_search.internal.sources.joballio import JoballioSource
from job_agent.features.job_search.internal.sources.gemini_web import GeminiWebSource
from job_agent.features.job_search.internal.normalizer import (
    normalize_saramin,
    normalize_worknet,
    normalize_joballio,
    normalize_gemini,
    deduplicate,
)

_NORMALIZERS = {
    "사람인": normalize_saramin,
    "워크넷": normalize_worknet,
    "잡알리오": normalize_joballio,
    "Gemini웹탐색": normalize_gemini,
}


def fetch_all(query: dict) -> dict:
    """활성화된 소스에서 공고를 수집하고 단일 리스트로 반환한다.

    query 키:
      job_role, location, employment_type, count
      sources (list, optional): 사용할 소스 목록. 없으면 API 키 있는 것만 사용
    반환: {"결과": "성공", "postings": list[dict], "total": int, "errors": list[str]}
    """
    sources_req = query.get("sources", [])
    all_raw: list[dict] = []
    errors: list[str] = []

    source_map = {
        "사람인": SaraminSource(),
        "워크넷": WorknetSource(),
        "잡알리오": JoballioSource(),
        "Gemini웹탐색": GeminiWebSource(),
    }

    active = sources_req if sources_req else list(source_map.keys())

    for name in active:
        src = source_map.get(name)
        if src is None:
            errors.append(f"알 수 없는 소스: {name}")
            continue

        result = src.search(query)
        if result.get("결과") == "성공":
            normalizer = _NORMALIZERS.get(name, normalize_gemini)
            for item in result.get("raw_items", []):
                normalized = normalizer(item)
                if normalized.get("결과") != "실패":
                    all_raw.append(normalized)
        else:
            errors.append(f"{name}: {result.get('이유', '알 수 없는 오류')}")

    postings = deduplicate(all_raw)
    return {"결과": "성공", "postings": postings, "total": len(postings), "errors": errors}
