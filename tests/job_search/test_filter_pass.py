"""DAY 19 — 필터링·매칭 + 패스 처리 테스트."""
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from job_agent.features.job_search.internal.filter import filter_by_persona, _check_filters
from job_agent.features.job_search.internal.pass_handler import (
    record_pass,
    is_passed,
    is_same_condition_passed,
    apply_pass_filter,
    reset_pass,
)
from job_agent.shared.db.connection import init_db


SAMPLE_POSTING = {
    "job_id": "TEST001",
    "source": "사람인",
    "url": "https://saramin.co.kr/job/TEST001",
    "title": "AI 엔지니어",
    "company": "테스트컴퍼니",
    "location": "서울 마곡",
    "job_role": "AI엔지니어",
    "employment_type": "정규직",
    "salary": None,
    "skills_required": ["Python"],
    "posted_date": "2026-05-31",
    "year": 2026,
    "month": 5,
    "day": 31,
}


@pytest.fixture
def tmp_db(tmp_path):
    db_path = tmp_path / "test.db"
    init_db(db_path)
    return db_path


# ──────────────────────────────────────────
# _check_filters
# ──────────────────────────────────────────

class TestCheckFilters:
    def test_no_constraints_passes(self):
        result = _check_filters(SAMPLE_POSTING, set(), set(), set(), set())
        assert result == []

    def test_blacklist_company_blocked(self):
        result = _check_filters(
            SAMPLE_POSTING,
            blacklist_companies={"테스트컴퍼니"},
            blacklist_keywords=set(),
            preferred_locations=set(),
            preferred_employment=set(),
        )
        assert len(result) == 1
        assert "블랙리스트" in result[0]

    def test_blacklist_keyword_in_title(self):
        result = _check_filters(
            {**SAMPLE_POSTING, "title": "AI 영업직"},
            blacklist_companies=set(),
            blacklist_keywords={"영업"},
            preferred_locations=set(),
            preferred_employment=set(),
        )
        assert len(result) == 1

    def test_preferred_location_mismatch(self):
        result = _check_filters(
            {**SAMPLE_POSTING, "location": "부산"},
            blacklist_companies=set(),
            blacklist_keywords=set(),
            preferred_locations={"서울"},
            preferred_employment=set(),
        )
        assert len(result) == 1

    def test_preferred_location_match(self):
        result = _check_filters(
            SAMPLE_POSTING,
            blacklist_companies=set(),
            blacklist_keywords=set(),
            preferred_locations={"서울"},
            preferred_employment=set(),
        )
        assert result == []

    def test_preferred_employment_mismatch(self):
        result = _check_filters(
            {**SAMPLE_POSTING, "employment_type": "인턴"},
            blacklist_companies=set(),
            blacklist_keywords=set(),
            preferred_locations=set(),
            preferred_employment={"정규직"},
        )
        assert len(result) == 1


# ──────────────────────────────────────────
# filter_by_persona (페르소나 없음 케이스)
# ──────────────────────────────────────────

class TestFilterByPersona:
    def test_no_persona_passes_all(self, tmp_db):
        result = filter_by_persona([SAMPLE_POSTING], user_id="user_no_persona", db_path=tmp_db)
        assert result["결과"] == "성공"
        assert len(result["passed"]) == 1
        assert result["filtered_out"] == 0

    def test_with_mock_persona_blacklist(self, tmp_db):
        mock_persona = MagicMock()
        mock_constraint = MagicMock()
        mock_constraint.type = "blacklist_company"
        mock_constraint.detail = "테스트컴퍼니"
        mock_persona.constraints = [mock_constraint]

        with patch("job_agent.features.job_search.internal.filter.get_persona", return_value=mock_persona):
            result = filter_by_persona([SAMPLE_POSTING], user_id="u1", db_path=tmp_db)

        assert result["결과"] == "성공"
        assert result["filtered_out"] == 1
        assert len(result["passed"]) == 0


# ──────────────────────────────────────────
# pass_handler
# ──────────────────────────────────────────

class TestPassHandler:
    def test_record_and_check_pass(self, tmp_db):
        result = record_pass(SAMPLE_POSTING, user_id="u1", reason="관심 없음", db_path=tmp_db)
        assert result["결과"] == "성공"
        assert is_passed(SAMPLE_POSTING, user_id="u1", db_path=tmp_db) is True

    def test_not_passed_initially(self, tmp_db):
        assert is_passed(SAMPLE_POSTING, user_id="u1", db_path=tmp_db) is False

    def test_same_condition_pass(self, tmp_db):
        record_pass(SAMPLE_POSTING, user_id="u1", db_path=tmp_db)
        same_condition = {**SAMPLE_POSTING, "url": "https://other.url/2", "job_id": "OTHER002"}
        assert is_same_condition_passed(same_condition, user_id="u1", db_path=tmp_db) is True

    def test_apply_pass_filter(self, tmp_db):
        record_pass(SAMPLE_POSTING, user_id="u1", db_path=tmp_db)
        new_posting = {**SAMPLE_POSTING, "url": "https://new.com/999", "job_id": "NEW999",
                       "company": "새컴퍼니", "job_role": "다른직무"}
        result = apply_pass_filter([SAMPLE_POSTING, new_posting], user_id="u1", db_path=tmp_db)
        assert result["결과"] == "성공"
        assert len(result["passed"]) == 1
        assert result["pass_recorded"] == 1

    def test_reset_pass(self, tmp_db):
        record_pass(SAMPLE_POSTING, user_id="u1", db_path=tmp_db)
        reset_pass(user_id="u1", db_path=tmp_db)
        assert is_passed(SAMPLE_POSTING, user_id="u1", db_path=tmp_db) is False
