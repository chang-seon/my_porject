"""DAY 24 — application recorder + link_handler 테스트."""
import pytest
from job_agent.features.application.internal.recorder import (
    record_application,
    update_application_status,
    get_application_history,
)
from job_agent.features.application.internal.link_handler import (
    get_apply_link,
    format_apply_message,
    validate_url,
)
from job_agent.shared.db.connection import init_db

SAMPLE_POSTING = {
    "company": "테스트컴퍼니",
    "title": "AI 엔지니어",
    "url": "https://example.com/apply/123",
}


@pytest.fixture
def tmp_db(tmp_path):
    db = tmp_path / "test.db"
    init_db(db)
    return db


class TestRecorder:
    def test_record_application_success(self, tmp_db):
        result = record_application("job-001", "u1", "draft-abc", SAMPLE_POSTING, db_path=tmp_db)
        assert result["결과"] == "성공"
        assert result["application_id"].startswith("APP-")
        assert result["apply_url"] == "https://example.com/apply/123"

    def test_record_without_url(self, tmp_db):
        posting = {"company": "무링크컴퍼니", "title": "백엔드"}
        result = record_application("job-002", "u1", "draft-def", posting, db_path=tmp_db)
        assert result["결과"] == "성공"
        assert result["apply_url"] == ""

    def test_application_id_deterministic_per_day(self, tmp_db):
        r1 = record_application("job-001", "u1", "d1", db_path=tmp_db)
        r2 = record_application("job-001", "u1", "d2", db_path=tmp_db)
        assert r1["application_id"] == r2["application_id"]

    def test_update_valid_status(self, tmp_db):
        r = record_application("job-001", "u1", "draft-abc", db_path=tmp_db)
        result = update_application_status(r["application_id"], "서류통과", user_id="u1", db_path=tmp_db)
        assert result["결과"] == "성공"
        assert result["status"] == "서류통과"

    def test_update_invalid_status(self, tmp_db):
        result = update_application_status("APP-dummy", "이상한상태", db_path=tmp_db)
        assert result["결과"] == "실패"
        assert "유효하지 않은 상태" in result["이유"]

    def test_update_final_result_records_signal(self, tmp_db):
        r = record_application("job-fin", "u1", "draft-fin", db_path=tmp_db)
        result = update_application_status(r["application_id"], "최종합격", user_id="u1", db_path=tmp_db)
        assert result["결과"] == "성공"
        from job_agent.shared.db.connection import get_connection
        conn = get_connection(tmp_db)
        row = conn.execute(
            "SELECT * FROM learning_signals WHERE user_id='u1' AND layer='E'"
        ).fetchone()
        conn.close()
        assert row is not None

    def test_get_application_history(self, tmp_db):
        record_application("job-001", "u1", "d1", SAMPLE_POSTING, db_path=tmp_db)
        record_application("job-002", "u1", "d2", SAMPLE_POSTING, db_path=tmp_db)
        result = get_application_history("u1", db_path=tmp_db)
        assert result["결과"] == "성공"
        assert result["total"] >= 2

    def test_get_history_empty(self, tmp_db):
        result = get_application_history("u_none", db_path=tmp_db)
        assert result["결과"] == "성공"
        assert result["total"] == 0


class TestLinkHandler:
    def test_get_apply_link_success(self):
        result = get_apply_link(SAMPLE_POSTING)
        assert result["결과"] == "성공"
        assert "example.com" in result["apply_url"]

    def test_get_apply_link_missing_url(self):
        result = get_apply_link({"company": "링크없음컴퍼니"})
        assert result["결과"] == "실패"

    def test_format_apply_message_with_draft(self):
        result = format_apply_message(SAMPLE_POSTING, draft_id="abc123")
        assert result["결과"] == "성공"
        assert "테스트컴퍼니" in result["message"]
        assert "abc123" in result["message"]

    def test_validate_url_valid(self):
        result = validate_url("https://saramin.co.kr/apply/123")
        assert result["결과"] == "성공"
        assert result["valid"] is True

    def test_validate_url_invalid(self):
        result = validate_url("not-a-url")
        assert result["결과"] == "실패"

    def test_validate_url_empty(self):
        result = validate_url("")
        assert result["결과"] == "실패"
