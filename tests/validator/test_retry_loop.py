"""DAY 21 — LLM 심사 + 재시도 루프 + 저장 테스트."""
import pytest
from unittest.mock import patch, MagicMock

from job_agent.features.validator.internal.llm_judge import judge_cover_letter, _parse_judge_response
from job_agent.features.validator.internal.retry_loop import validate_with_retry
from job_agent.features.validator.internal.storage import save_validation_result, get_validation_history
from job_agent.shared.db.connection import init_db

GOOD_TEXT = """
AI 개발 역량을 바탕으로 귀사에 기여하겠습니다.
처리 속도를 40% 개선했습니다. 문제를 원인 분석 후 해결한 결과
팀 배포 주기를 2배 단축했습니다. 이 경험을 통해 역량을 키웠으며
도전과 성장을 거듭하면서 기여하겠습니다.
"""

BAD_TEXT = "저는 분석했습니다. 중요하다고 생각합니다. 최고의 성과 노력하겠습니다."


@pytest.fixture
def tmp_db(tmp_path):
    db_path = tmp_path / "test.db"
    init_db(db_path)
    return db_path


# ──────────────────────────────────────────
# _parse_judge_response
# ──────────────────────────────────────────

class TestParseJudgeResponse:
    def test_valid_json(self):
        raw = '{"passed": true, "score": 0.85, "issues": [], "summary": "좋음"}'
        result = _parse_judge_response(raw)
        assert result["passed"] is True
        assert result["score"] == 0.85

    def test_json_in_code_block(self):
        raw = '```json\n{"passed": false, "score": 0.3, "issues": [], "summary": "나쁨"}\n```'
        result = _parse_judge_response(raw)
        assert result["passed"] is False

    def test_invalid_json_returns_fallback(self):
        result = _parse_judge_response("이것은 JSON이 아닙니다")
        assert result["passed"] is False
        assert result["score"] == 0.0


# ──────────────────────────────────────────
# judge_cover_letter
# ──────────────────────────────────────────

class TestJudgeCoverLetter:
    def test_llm_pass(self):
        mock_response = {"결과": "성공", "text": '{"passed": true, "score": 0.9, "issues": [], "summary": "통과"}'}
        with patch("job_agent.features.validator.internal.llm_judge._router") as mock_router:
            mock_router.generate.return_value = mock_response
            result = judge_cover_letter(GOOD_TEXT)

        assert result["결과"] == "성공"
        assert result["passed"] is True

    def test_llm_failure_propagated(self):
        with patch("job_agent.features.validator.internal.llm_judge._router") as mock_router:
            mock_router.generate.return_value = {"결과": "실패", "이유": "API 오류"}
            result = judge_cover_letter(GOOD_TEXT)

        assert result["결과"] == "실패"


# ──────────────────────────────────────────
# validate_with_retry
# ──────────────────────────────────────────

class TestValidateWithRetry:
    def test_passes_on_first_attempt_skip_llm(self):
        result = validate_with_retry(GOOD_TEXT, skip_llm=True)
        assert result["결과"] == "성공"
        assert result["passed"] is True
        assert result["attempts"] == 1

    def test_bad_text_needs_hitl_after_3_retries(self):
        result = validate_with_retry(BAD_TEXT, skip_llm=True)
        assert result["결과"] == "성공"
        assert result["passed"] is False
        assert result["needs_hitl"] is True
        assert result["attempts"] == 3

    def test_retry_with_generate_fn(self):
        """generate_fn이 있으면 실패 시 새 버전으로 재시도한다."""
        call_count = [0]

        def fake_generate(content, attempt):
            call_count[0] += 1
            return GOOD_TEXT  # 2번째부터 좋은 텍스트 반환

        result = validate_with_retry(BAD_TEXT, skip_llm=True, generate_fn=fake_generate)
        assert result["결과"] == "성공"
        assert call_count[0] >= 1

    def test_llm_pass_returns_passed(self):
        mock_judge = {"결과": "성공", "passed": True, "score": 0.9, "issues": [], "summary": "통과"}
        with patch("job_agent.features.validator.internal.retry_loop.judge_cover_letter", return_value=mock_judge):
            result = validate_with_retry(GOOD_TEXT)
        assert result["passed"] is True

    def test_history_recorded(self):
        result = validate_with_retry(BAD_TEXT, skip_llm=True)
        assert len(result["history"]) > 0


# ──────────────────────────────────────────
# storage
# ──────────────────────────────────────────

class TestValidationStorage:
    def test_save_and_retrieve(self, tmp_db):
        result = {"passed": True, "score": 0.85, "reasons": [], "attempts": 1, "needs_hitl": False}
        save_result = save_validation_result("u1", "cover_letter", "hash123", result, tmp_db)
        assert save_result["결과"] == "성공"

        history = get_validation_history("u1", "cover_letter", db_path=tmp_db)
        assert history["결과"] == "성공"
        assert history["total"] == 1
        assert history["history"][0]["passed"] is True

    def test_empty_history(self, tmp_db):
        history = get_validation_history("u_none", db_path=tmp_db)
        assert history["total"] == 0
