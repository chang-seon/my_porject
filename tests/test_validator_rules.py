"""DAY 07 — 검증AI 룰셋 YAML 파싱 테스트"""
import pytest
from pathlib import Path
import yaml

RULES_DIR = Path("job_agent/features/validator/internal/rules")

RULE_FILES = [
    "cover_letter_rules.yaml",
    "code_rules.yaml",
    "job_posting_rules.yaml",
    "interview_rules.yaml",
]


class TestRulesParsing:
    @pytest.mark.parametrize("filename", RULE_FILES)
    def test_yaml_parses_without_error(self, filename):
        path = RULES_DIR / filename
        assert path.exists(), f"{filename} 파일 없음"
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert data is not None

    @pytest.mark.parametrize("filename", RULE_FILES)
    def test_required_fields_present(self, filename):
        path = RULES_DIR / filename
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert "version" in data, f"{filename}: version 필드 없음"
        assert "target" in data, f"{filename}: target 필드 없음"

    def test_cover_letter_has_six_style_markers(self):
        path = RULES_DIR / "cover_letter_rules.yaml"
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        markers = data.get("style_markers", [])
        assert len(markers) == 6, f"문체 마커 6종 필요, 현재 {len(markers)}종"

    def test_cover_letter_has_four_anti_patterns(self):
        path = RULES_DIR / "cover_letter_rules.yaml"
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        patterns = data.get("anti_patterns", [])
        assert len(patterns) == 4, f"안티패턴 4종 필요, 현재 {len(patterns)}종"

    def test_code_rules_has_critical_anti_pattern(self):
        path = RULES_DIR / "code_rules.yaml"
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        severities = [ap["severity"] for ap in data.get("anti_patterns", [])]
        assert "critical" in severities, "code_rules에 critical 안티패턴 없음"

    def test_all_rules_have_thresholds(self):
        for filename in RULE_FILES:
            path = RULES_DIR / filename
            with open(path, encoding="utf-8") as f:
                data = yaml.safe_load(f)
            assert "thresholds" in data, f"{filename}: thresholds 없음"
