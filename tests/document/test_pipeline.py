"""DAY 23 — document pipeline 통합 테스트."""
import pytest
from unittest.mock import patch, MagicMock

from job_agent.features.document.internal.pipeline import (
    generate_and_validate,
    get_draft,
    update_draft,
)
from job_agent.shared.db.connection import init_db


SAMPLE_JOB = {"company": "테스트컴퍼니", "title": "AI 엔지니어", "location": "서울", "skills_required": ["Python"]}


@pytest.fixture
def tmp_db(tmp_path):
    db = tmp_path / "test.db"
    init_db(db)
    return db


@pytest.fixture
def mock_pool():
    return {
        "결과": "성공",
        "content_pool": ["학력: 한국대학교 컴퓨터공학과 (학사)"],
        "style_markers": ["SM-01: 수치 표현 (예시: 40%)"],
        "anti_patterns": ["AP-01: AI 투명체 금지"],
        "persona_summary": "이름: 어창선\n목표직무: AI 엔지니어 (IT)",
    }


@pytest.fixture
def mock_synth():
    return {
        "결과": "성공",
        "content": "AI 개발 역량으로 귀사에 기여하겠습니다. 처리 속도를 40% 개선했습니다. 도전과 성장을 거듭하겠습니다.",
        "draft_id": "abcd1234ef567890",
        "token_used": 100,
    }


class TestGenerateAndValidate:
    def test_success_path(self, tmp_db, mock_pool, mock_synth):
        """생성 → 검증 통과 경로."""
        with patch("job_agent.features.document.internal.pipeline.load_content_pool", return_value=mock_pool), \
             patch("job_agent.features.document.internal.pipeline.synthesize", return_value=mock_synth), \
             patch("job_agent.features.document.internal.pipeline.validate_with_retry") as mock_val:
            mock_val.return_value = {"결과": "성공", "passed": True, "attempts": 1, "needs_hitl": False, "history": []}
            result = generate_and_validate(SAMPLE_JOB, "u1", db_path=tmp_db, skip_llm=True)

        assert result["결과"] == "성공"
        assert result["draft_id"] == "abcd1234ef567890"
        assert result["validation"]["passed"] is True

    def test_pool_failure_returns_failure(self, tmp_db):
        """페르소나 없으면 즉시 실패."""
        with patch("job_agent.features.document.internal.pipeline.load_content_pool",
                   return_value={"결과": "실패", "이유": "페르소나 없음: user_id=u_bad"}):
            result = generate_and_validate(SAMPLE_JOB, "u_bad", db_path=tmp_db)
        assert result["결과"] == "실패"
        assert "페르소나" in result["이유"]

    def test_synth_failure_returns_failure(self, tmp_db, mock_pool):
        """LLM 생성 실패 시 즉시 실패."""
        with patch("job_agent.features.document.internal.pipeline.load_content_pool", return_value=mock_pool), \
             patch("job_agent.features.document.internal.pipeline.synthesize",
                   return_value={"결과": "실패", "이유": "LLM 호출 실패"}):
            result = generate_and_validate(SAMPLE_JOB, "u1", db_path=tmp_db)
        assert result["결과"] == "실패"

    def test_needs_hitl_when_validation_fails(self, tmp_db, mock_pool, mock_synth):
        """3회 검증 실패 시 needs_hitl=True."""
        with patch("job_agent.features.document.internal.pipeline.load_content_pool", return_value=mock_pool), \
             patch("job_agent.features.document.internal.pipeline.synthesize", return_value=mock_synth), \
             patch("job_agent.features.document.internal.pipeline.validate_with_retry") as mock_val:
            mock_val.return_value = {"결과": "성공", "passed": False, "attempts": 3, "needs_hitl": True, "history": []}
            result = generate_and_validate(SAMPLE_JOB, "u1", db_path=tmp_db, skip_llm=True)

        assert result["결과"] == "성공"
        assert result["validation"]["needs_hitl"] is True

    def test_draft_saved_to_db(self, tmp_db, mock_pool, mock_synth):
        """생성된 초안이 event_logs에 저장된다."""
        with patch("job_agent.features.document.internal.pipeline.load_content_pool", return_value=mock_pool), \
             patch("job_agent.features.document.internal.pipeline.synthesize", return_value=mock_synth), \
             patch("job_agent.features.document.internal.pipeline.validate_with_retry") as mock_val:
            mock_val.return_value = {"결과": "성공", "passed": True, "attempts": 1, "needs_hitl": False, "history": []}
            result = generate_and_validate(SAMPLE_JOB, "u1", db_path=tmp_db)

        assert result["결과"] == "성공"
        get_result = get_draft(result["draft_id"], db_path=tmp_db)
        assert get_result["결과"] == "성공"
        assert get_result["draft_id"] == result["draft_id"]

    def test_get_draft_not_found(self, tmp_db):
        """존재하지 않는 draft_id 조회."""
        result = get_draft("nonexistent000000", db_path=tmp_db)
        assert result["결과"] == "실패"
        assert "초안 없음" in result["이유"]

    def test_update_draft_creates_new_id(self, tmp_db):
        """초안 수정 시 새 draft_id 발급."""
        result = update_draft("old_draft_id00000", "수정된 자소서 내용입니다.", "문체 개선", user_id="u1", db_path=tmp_db)
        assert result["결과"] == "성공"
        assert result["draft_id"] != "old_draft_id00000"
        assert result["prev_draft_id"] == "old_draft_id00000"

    def test_update_draft_deterministic_id(self, tmp_db):
        """같은 내용은 같은 draft_id를 생성한다."""
        content = "동일한 자소서 내용"
        r1 = update_draft("old1", content, "이유1", db_path=tmp_db)
        r2 = update_draft("old2", content, "이유2", db_path=tmp_db)
        assert r1["draft_id"] == r2["draft_id"]
