"""1차 룰 엔진 — YAML 룰 로드 + 문체마커/안티패턴 판정."""
from __future__ import annotations

from pathlib import Path
import yaml

from job_agent.features.validator.internal.checks.style_marker import check_style_markers
from job_agent.features.validator.internal.checks.anti_pattern import check_anti_patterns

_RULES_DIR = Path(__file__).parent / "rules"


def load_rules(target: str) -> dict:
    """YAML 룰파일을 로드한다. target: cover_letter | code | job_posting | interview"""
    rule_file = _RULES_DIR / f"{target}_rules.yaml"
    if not rule_file.exists():
        return {}
    with rule_file.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def validate_cover_letter(text: str, rules: dict | None = None) -> dict:
    """자소서 1차 룰 검증.

    반환:
      passed: bool
      style_markers: 마커 결과
      anti_patterns: 안티패턴 결과
      score: 종합 점수 (0.0~1.0)
      reason: 실패 사유 목록
    """
    try:
        if rules is None:
            rules = load_rules("cover_letter")

        markers = rules.get("style_markers", [])
        anti_patterns_def = rules.get("anti_patterns", [])
        thresholds = rules.get("thresholds", {})

        min_hit = thresholds.get("min_style_markers_hit", 3)
        max_ap = thresholds.get("max_anti_patterns_hit", 1)
        min_score = thresholds.get("min_score", 0.6)

        sm_result = check_style_markers(text, markers)
        ap_result = check_anti_patterns(text, anti_patterns_def)

        reasons: list[str] = []
        hit_count = len(sm_result["hit_ids"])
        ap_count = len(ap_result["hit_ids"])

        if hit_count < min_hit:
            reasons.append(f"문체 마커 {hit_count}/{min_hit} 미달")
        if ap_count > max_ap:
            reasons.append(f"안티패턴 {ap_count}건 (최대 {max_ap}건)")
        if sm_result["score"] < min_score:
            reasons.append(f"종합 점수 {sm_result['score']} < {min_score}")

        passed = len(reasons) == 0
        return {
            "결과": "성공",
            "passed": passed,
            "score": sm_result["score"],
            "style_markers": sm_result,
            "anti_patterns": ap_result,
            "reasons": reasons,
        }
    except Exception as e:
        return {"결과": "실패", "이유": str(e)}


def validate(target: str, content: str, rules: dict | None = None) -> dict:
    """target에 맞는 검증을 실행한다.

    target: cover_letter | code | job_posting | interview
    """
    try:
        if target == "cover_letter":
            return validate_cover_letter(content, rules)
        else:
            loaded = rules or load_rules(target)
            return {
                "결과": "성공",
                "passed": True,
                "score": 1.0,
                "style_markers": {},
                "anti_patterns": {},
                "reasons": [],
                "note": f"{target} 전용 룰 미구현 (DAY 20 범위 외)",
            }
    except Exception as e:
        return {"결과": "실패", "이유": str(e)}
