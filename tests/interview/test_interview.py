"""DAY 27 — interview prep_generator + debrief 테스트."""
import pytest
from unittest.mock import patch, MagicMock
from job_agent.features.interview.internal.prep_generator import (
    generate_prep,
    _default_questions,
    _default_tips,
    _parse_prep_response,
)
from job_agent.features.interview.internal.debrief import (
    record_debrief,
    get_debrief_history,
)
from job_agent.shared.db.connection import init_db, get_connection

SAMPLE_POSTING = {"company": "테스트컴퍼니", "title": "AI 엔지니어", "job_role": "AI 엔지니어"}


@pytest.fixture
def tmp_db(tmp_path):
    db = tmp_path / "test.db"
    init_db(db)
    return db


class TestPrepGenerator:
    def test_generate_prep_skip_llm_success(self, tmp_db):
        result = generate_prep(SAMPLE_POSTING, db_path=tmp_db, skip_llm=True)
        assert result["결과"] == "성공"
        assert len(result["questions"]) > 0
        assert len(result["tips"]) > 0
        assert "company" in result["company_info"]

    def test_generate_prep_with_rag_data(self, tmp_db):
        from job_agent.features.learner.internal.rag.ingest import ingest_interview_questions
        ingest_interview_questions("테스트컴퍼니", ["기술 스택 질문입니다"], db_path=tmp_db)
        result = generate_prep(SAMPLE_POSTING, db_path=tmp_db, skip_llm=True)
        assert result["결과"] == "성공"
        assert len(result["questions"]) > 0

    def test_default_questions_has_job_role(self):
        questions = _default_questions("AI 엔지니어")
        assert any("AI 엔지니어" in q for q in questions)

    def test_default_tips_returns_list(self):
        tips = _default_tips()
        assert len(tips) >= 3

    def test_parse_prep_response(self):
        text = """QUESTIONS:
1. 자기소개 해주세요.
2. 강점을 말씀해주세요.

TIPS:
1. STAR 방식을 사용하세요.
2. 구체적 수치를 활용하세요.
"""
        result = _parse_prep_response(text)
        assert len(result["questions"]) == 2
        assert len(result["tips"]) == 2

    def test_generate_prep_with_llm(self, tmp_db):
        mock_resp = {
            "결과": "성공",
            "text": "QUESTIONS:\n1. 자기소개 해주세요.\n\nTIPS:\n1. STAR 방식을 사용하세요.",
        }
        with patch("job_agent.features.interview.internal.prep_generator._get_router") as mock_get:
            mock_router = MagicMock()
            mock_router.generate.return_value = mock_resp
            mock_get.return_value = mock_router
            result = generate_prep(SAMPLE_POSTING, db_path=tmp_db, skip_llm=False)
        assert result["결과"] == "성공"


class TestDebrief:
    def test_record_debrief_basic(self, tmp_db):
        result = record_debrief("APP-001", "면접이 어려웠습니다.", "u1", db_path=tmp_db)
        assert result["결과"] == "성공"
        assert result["signals_recorded"] >= 1

    def test_record_debrief_with_questions(self, tmp_db):
        questions = ["자기소개 하세요", "강점은 무엇인가요"]
        result = record_debrief("APP-002", "잘 준비했습니다.", "u1", questions=questions, db_path=tmp_db)
        assert result["결과"] == "성공"
        assert result["signals_recorded"] >= 3
        assert result["rag_ingested"] == 2

    def test_record_debrief_final_result_signal(self, tmp_db):
        result = record_debrief("APP-003", "좋은 경험이었습니다.", "u1", result="최종합격", db_path=tmp_db)
        assert result["결과"] == "성공"
        conn = get_connection(tmp_db)
        row = conn.execute(
            "SELECT 1 FROM learning_signals WHERE user_id='u1' AND layer='E' AND signal_type='interview_최종합격'"
        ).fetchone()
        conn.close()
        assert row is not None

    def test_get_debrief_history(self, tmp_db):
        record_debrief("APP-001", "첫 번째 회고", "u1", db_path=tmp_db)
        record_debrief("APP-002", "두 번째 회고", "u1", db_path=tmp_db)
        result = get_debrief_history("u1", db_path=tmp_db)
        assert result["결과"] == "성공"
        assert result["total"] >= 2

    def test_get_debrief_history_empty(self, tmp_db):
        result = get_debrief_history("u_none", db_path=tmp_db)
        assert result["결과"] == "성공"
        assert result["total"] == 0
