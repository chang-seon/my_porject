"""DAY 14 — HITL Bus 테스트"""
import pytest
from job_agent.shared.db.connection import init_db
from job_agent.core.hitl_bus import create_request, respond, get_pending


@pytest.fixture
def tmp_db(tmp_path):
    db_path = tmp_path / "test.db"
    init_db(db_path)
    return db_path


class TestHitlBus:
    def test_create_and_get_pending(self, tmp_db):
        result = create_request("req-001", "u001", "승인하시겠습니까?",
                                ["승인", "거부"], db_path=tmp_db)
        assert result["결과"] == "성공"
        pending = get_pending("u001", db_path=tmp_db)
        assert len(pending["requests"]) == 1
        assert pending["requests"][0]["question"] == "승인하시겠습니까?"

    def test_respond_changes_status(self, tmp_db):
        create_request("req-002", "u001", "질문", ["예", "아니오"], db_path=tmp_db)
        result = respond("req-002", "예", db_path=tmp_db)
        assert result["결과"] == "성공"
        pending = get_pending("u001", db_path=tmp_db)
        assert len(pending["requests"]) == 0

    def test_duplicate_request_id_fails(self, tmp_db):
        create_request("req-dup", "u001", "질문1", ["예"], db_path=tmp_db)
        result = create_request("req-dup", "u001", "질문2", ["예"], db_path=tmp_db)
        assert result["결과"] == "실패"
