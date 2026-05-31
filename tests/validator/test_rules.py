"""DAY 20 — 검증AI 1차 룰 엔진 테스트."""
import pytest

from job_agent.features.validator.internal.checks.style_marker import check_style_markers
from job_agent.features.validator.internal.checks.anti_pattern import check_anti_patterns
from job_agent.features.validator.internal.rule_engine import (
    load_rules,
    validate_cover_letter,
    validate,
)

# ──────────────────────────────────────────
# 테스트용 자소서 샘플
# ──────────────────────────────────────────

# 문체 마커가 많은 자소서 (통과 예상)
GOOD_COVER_LETTER = """
AI 개발 역량을 바탕으로 귀사에 기여하겠습니다.

저는 머신러닝 파이프라인을 구축하여 처리 속도를 40% 개선했습니다.
문제를 분석하고 원인을 파악하여 최적 해결책을 도출한 결과,
팀 전체의 배포 주기를 2배 단축시켰습니다.

이 경험을 통해 역량을 키웠으며, 도전과 성장을 거듭하면서
귀사에 기여하겠습니다.
"""

# 안티패턴이 많은 자소서 (실패 예상)
BAD_COVER_LETTER = """
저는 AI 분야가 중요하다고 생각합니다.
귀사에서 더욱 발전하고 싶습니다.
저는 최고의 성과를 내기 위해 노력하겠습니다.
항상 살펴보았습니다. 분석했습니다.
"""


# ──────────────────────────────────────────
# check_style_markers
# ──────────────────────────────────────────

class TestStyleMarker:
    def test_numeric_pattern_detected(self):
        markers = [{"id": "SM-01", "name": "수치", "patterns": ["\\d+%"], "weight": 1.0}]
        result = check_style_markers("성과를 40% 개선했습니다.", markers)
        assert "SM-01" in result["hit_ids"]
        assert result["score"] == 1.0

    def test_keyword_min_count(self):
        markers = [{"id": "SM-03", "name": "문제해결", "keywords": ["문제", "원인", "해결"], "min_count": 2, "weight": 1.0}]
        text = "문제를 파악하고 원인을 분석했습니다."
        result = check_style_markers(text, markers)
        assert "SM-03" in result["hit_ids"]

    def test_keyword_below_min_count(self):
        markers = [{"id": "SM-03", "name": "문제해결", "keywords": ["문제", "원인", "해결"], "min_count": 3, "weight": 1.0}]
        text = "문제를 파악했습니다."
        result = check_style_markers(text, markers)
        assert "SM-03" not in result["hit_ids"]

    def test_empty_text_no_hits(self):
        rules = load_rules("cover_letter")
        markers = rules.get("style_markers", [])
        result = check_style_markers("", markers)
        assert result["score"] == 0.0
        assert result["hit_ids"] == []


# ──────────────────────────────────────────
# check_anti_patterns
# ──────────────────────────────────────────

class TestAntiPattern:
    def test_gpt_phrase_detected(self):
        ap = [{"id": "AP-01", "name": "GPT투명체", "patterns": ["분석했습니다", "살펴보았습니다"], "severity": "high"}]
        result = check_anti_patterns("저는 시장을 분석했습니다.", ap)
        assert "AP-01" in result["hit_ids"]
        assert result["severity_count"]["high"] == 1

    def test_no_anti_pattern_in_good_text(self):
        rules = load_rules("cover_letter")
        ap_defs = rules.get("anti_patterns", [])
        result = check_anti_patterns("Python으로 ML 모델을 구축했습니다.", ap_defs)
        assert result["hit_ids"] == []


# ──────────────────────────────────────────
# validate_cover_letter (통합)
# ──────────────────────────────────────────

class TestValidateCoverLetter:
    def test_good_cover_letter_passes(self):
        result = validate_cover_letter(GOOD_COVER_LETTER)
        assert result["결과"] == "성공"
        assert result["passed"] is True
        assert result["score"] > 0

    def test_bad_cover_letter_fails(self):
        result = validate_cover_letter(BAD_COVER_LETTER)
        assert result["결과"] == "성공"
        assert result["passed"] is False
        assert len(result["reasons"]) > 0

    def test_empty_text_fails(self):
        result = validate_cover_letter("")
        assert result["결과"] == "성공"
        assert result["passed"] is False

    def test_custom_rules_override(self):
        """낮은 기준값으로 모든 텍스트가 통과하는지 확인."""
        custom_rules = {
            "style_markers": [],
            "anti_patterns": [],
            "thresholds": {"min_style_markers_hit": 0, "max_anti_patterns_hit": 99, "min_score": 0.0},
        }
        result = validate_cover_letter("아무 텍스트", custom_rules)
        assert result["passed"] is True


# ──────────────────────────────────────────
# validate (다목적 엔트리)
# ──────────────────────────────────────────

class TestValidate:
    def test_cover_letter_target(self):
        result = validate("cover_letter", GOOD_COVER_LETTER)
        assert result["결과"] == "성공"
        assert "passed" in result

    def test_unknown_target_passes_with_note(self):
        result = validate("interview", "면접 준비 내용")
        assert result["결과"] == "성공"
        assert result["passed"] is True
        assert "note" in result


# ──────────────────────────────────────────
# load_rules
# ──────────────────────────────────────────

class TestLoadRules:
    def test_cover_letter_rules_loaded(self):
        rules = load_rules("cover_letter")
        assert "style_markers" in rules
        assert len(rules["style_markers"]) == 6

    def test_nonexistent_rules_returns_empty(self):
        rules = load_rules("nonexistent_target_xyz")
        assert rules == {}
