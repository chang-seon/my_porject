"""DAY 26 — company_analyzer 테스트."""
import pytest
from unittest.mock import patch
from job_agent.features.job_search.internal.company_analyzer import (
    analyze_company,
    analyze_and_pass,
    _is_negative,
)
from job_agent.shared.db.connection import init_db


@pytest.fixture
def tmp_db(tmp_path):
    db = tmp_path / "test.db"
    init_db(db)
    return db


SAMPLE_POSTING = {"company": "야근컴퍼니", "title": "백엔드", "url": "https://test.com/1", "job_role": "백엔드 개발자"}
GOOD_POSTING = {"company": "좋은컴퍼니", "title": "AI 엔지니어", "url": "https://test.com/2", "job_role": "AI 엔지니어"}


class TestIsNegative:
    def test_negative_keyword_detected(self):
        assert _is_negative("야근이 많습니다") is True

    def test_no_negative_keyword(self):
        assert _is_negative("자유로운 분위기") is False


class TestAnalyzeCompany:
    def test_no_company_name_fails(self, tmp_db):
        result = analyze_company({}, "u1", db_path=tmp_db)
        assert result["결과"] == "실패"
        assert "회사명" in result["이유"]

    def test_no_rag_data_returns_no_pass(self, tmp_db):
        result = analyze_company(GOOD_POSTING, "u1", db_path=tmp_db)
        assert result["결과"] == "성공"
        assert result["should_pass"] is False

    def test_negative_rag_data_triggers_pass(self, tmp_db):
        from job_agent.features.learner.internal.rag.ingest import ingest_company_reviews
        ingest_company_reviews("야근컴퍼니", ["야근이 매우 많습니다", "갑질 문화 있음"], db_path=tmp_db)
        result = analyze_company(SAMPLE_POSTING, "u1", min_reputation_score=0.0, db_path=tmp_db)
        assert result["결과"] == "성공"
        assert result["should_pass"] is True
        assert result["negative_ratio"] > 0

    def test_returns_reputation_items(self, tmp_db):
        from job_agent.features.learner.internal.rag.ingest import ingest_company_reviews
        ingest_company_reviews("테스트컴퍼니", ["복지가 좋습니다"], db_path=tmp_db)
        result = analyze_company({"company": "테스트컴퍼니"}, "u1", db_path=tmp_db)
        assert result["결과"] == "성공"
        assert isinstance(result["reputation_items"], list)


class TestAnalyzeAndPass:
    def test_empty_postings(self, tmp_db):
        result = analyze_and_pass([], "u1", db_path=tmp_db)
        assert result["결과"] == "성공"
        assert result["total"] == 0
        assert result["auto_passed"] == 0

    def test_good_company_accepted(self, tmp_db):
        result = analyze_and_pass([GOOD_POSTING], "u1", db_path=tmp_db)
        assert result["결과"] == "성공"
        assert len(result["accepted"]) == 1
        assert result["auto_passed"] == 0

    def test_bad_company_auto_passed(self, tmp_db):
        from job_agent.features.learner.internal.rag.ingest import ingest_company_reviews
        ingest_company_reviews("야근컴퍼니", ["야근이 매우 많습니다", "갑질 문화 있음"], db_path=tmp_db)
        result = analyze_and_pass([SAMPLE_POSTING], "u1", negative_threshold=0.0, db_path=tmp_db)
        assert result["결과"] == "성공"
        assert result["auto_passed"] == 1
        assert len(result["accepted"]) == 0
