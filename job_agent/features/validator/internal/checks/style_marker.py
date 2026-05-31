"""자소서 문체 마커 감지 — 1차 룰 엔진 (LLM 없음, 비용 0)."""
from __future__ import annotations

import re
from typing import Any


def check_style_markers(text: str, markers: list[dict]) -> dict:
    """문체 마커 감지 결과를 반환한다.

    반환:
      hit_ids: 감지된 마커 ID 목록
      score: 가중치 합산 정규화 점수 (0.0~1.0)
      details: 마커별 상세 결과
    """
    results: list[dict] = []
    total_weight = sum(m.get("weight", 1.0) for m in markers)
    hit_weight = 0.0

    for marker in markers:
        hit = _check_single_marker(text, marker)
        if hit:
            hit_weight += marker.get("weight", 1.0)
        results.append({"id": marker["id"], "name": marker["name"], "hit": hit})

    score = round(hit_weight / total_weight, 3) if total_weight > 0 else 0.0
    hit_ids = [r["id"] for r in results if r["hit"]]

    return {"hit_ids": hit_ids, "score": score, "details": results}


def _check_single_marker(text: str, marker: dict) -> bool:
    patterns = marker.get("patterns", [])
    keywords = marker.get("keywords", [])
    min_count = marker.get("min_count", 1)

    # 패턴 검사
    for pattern in patterns:
        if re.search(pattern, text, re.MULTILINE):
            return True

    # 키워드 검사 (min_count 기준)
    if keywords:
        count = sum(1 for kw in keywords if kw in text)
        return count >= min_count

    return False
