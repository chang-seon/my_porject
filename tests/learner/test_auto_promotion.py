"""DAY 28 — auto_promotion 테스트."""
import pytest
from job_agent.features.learner.internal.auto_promotion import (
    check_promotion,
    get_automation_level,
    reset_automation_level,
    record_validation_signal,
    _count_consecutive_ok,
    _AUTOMATION_LEVELS,
)
from job_agent.features.learner.internal.dynamic_threshold import update_threshold
from job_agent.shared.db.connection import init_db


@pytest.fixture
def tmp_db(tmp_path):
    db = tmp_path / "test.db"
    init_db(db)
    return db


class TestCheckPromotion:
    def test_no_signals_no_promotion(self, tmp_db):
        result = check_promotion("u1", db_path=tmp_db)
        assert result["결과"] == "성공"
        assert result["promoted"] is False
        assert result["current_level"] == 0

    def test_five_ok_signals_triggers_promotion(self, tmp_db):
        for i in range(5):
            record_validation_signal("u1", passed=True, db_path=tmp_db)
        result = check_promotion("u1", db_path=tmp_db)
        assert result["결과"] == "성공"
        assert result["promoted"] is True
        assert result["new_level"] == 1

    def test_four_ok_no_promotion(self, tmp_db):
        for i in range(4):
            record_validation_signal("u1", passed=True, db_path=tmp_db)
        result = check_promotion("u1", db_path=tmp_db)
        assert result["promoted"] is False

    def test_fail_breaks_streak(self, tmp_db):
        for i in range(3):
            record_validation_signal("u1", passed=True, db_path=tmp_db)
        record_validation_signal("u1", passed=False, db_path=tmp_db)
        for i in range(3):
            record_validation_signal("u1", passed=True, db_path=tmp_db)
        result = check_promotion("u1", db_path=tmp_db)
        assert result["consecutive_ok"] == 3
        assert result["promoted"] is False

    def test_custom_n_threshold(self, tmp_db):
        update_threshold("automation", "promotion_n", 3, "u1", db_path=tmp_db)
        for i in range(3):
            record_validation_signal("u1", passed=True, db_path=tmp_db)
        result = check_promotion("u1", db_path=tmp_db)
        assert result["promoted"] is True

    def test_max_level_no_further_promotion(self, tmp_db):
        update_threshold("automation", "current_level", 3, "u1", db_path=tmp_db)
        for i in range(10):
            record_validation_signal("u1", passed=True, db_path=tmp_db)
        result = check_promotion("u1", db_path=tmp_db)
        assert result["promoted"] is False
        assert "최고" in result["message"]


class TestGetAutomationLevel:
    def test_default_level_is_zero(self, tmp_db):
        result = get_automation_level("u1", db_path=tmp_db)
        assert result["결과"] == "성공"
        assert result["level"] == 0
        assert result["level_name"] == _AUTOMATION_LEVELS[0]

    def test_level_after_promotion(self, tmp_db):
        update_threshold("automation", "current_level", 2, "u1", db_path=tmp_db)
        result = get_automation_level("u1", db_path=tmp_db)
        assert result["level"] == 2


class TestResetAutomationLevel:
    def test_reset_to_zero(self, tmp_db):
        update_threshold("automation", "current_level", 2, "u1", db_path=tmp_db)
        result = reset_automation_level("u1", db_path=tmp_db)
        assert result["결과"] == "성공"
        assert result["level"] == 0
        lvl = get_automation_level("u1", db_path=tmp_db)
        assert lvl["level"] == 0


class TestRecordValidationSignal:
    def test_record_passed(self, tmp_db):
        result = record_validation_signal("u1", passed=True, draft_id="abc123", db_path=tmp_db)
        assert result["결과"] == "성공"
        assert result["passed"] is True

    def test_count_consecutive_ok(self, tmp_db):
        for i in range(3):
            record_validation_signal("u1", passed=True, db_path=tmp_db)
        count = _count_consecutive_ok("u1", tmp_db)
        assert count == 3
