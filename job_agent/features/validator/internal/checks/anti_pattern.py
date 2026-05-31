"""자소서 안티패턴 감지 — 1차 룰 엔진 (LLM 없음, 비용 0)."""
from __future__ import annotations

import re


def check_anti_patterns(text: str, anti_patterns: list[dict]) -> dict:
    """안티패턴 감지 결과를 반환한다.

    반환:
      hit_ids: 감지된 안티패턴 ID 목록
      severity_count: {"high": N, "medium": N, "low": N}
      details: 안티패턴별 상세 결과
    """
    results: list[dict] = []
    severity_count: dict[str, int] = {"high": 0, "medium": 0, "low": 0}

    for ap in anti_patterns:
        hits = _find_hits(text, ap)
        hit = len(hits) > 0
        if hit:
            sev = ap.get("severity", "low")
            severity_count[sev] = severity_count.get(sev, 0) + 1
        results.append({
            "id": ap["id"],
            "name": ap["name"],
            "hit": hit,
            "severity": ap.get("severity", "low"),
            "matched": hits[:3],  # 최대 3개 샘플
        })

    hit_ids = [r["id"] for r in results if r["hit"]]
    return {"hit_ids": hit_ids, "severity_count": severity_count, "details": results}


def _find_hits(text: str, ap: dict) -> list[str]:
    patterns = ap.get("patterns", [])
    found: list[str] = []
    for pattern in patterns:
        matches = re.findall(pattern, text, re.MULTILINE)
        found.extend(matches)
    return found
