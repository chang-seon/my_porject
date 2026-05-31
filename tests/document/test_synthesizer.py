"""DAY 22 — pool_loader + synthesizer 테스트."""
import pytest
from unittest.mock import patch, MagicMock

from job_agent.features.document.internal.synthesizer import synthesize, _fill_prompt, _make_draft_id
from job_agent.features.document.internal.pool_loader import load_content_pool
from job_agent.shared.db.connection import init_db


SAMPLE_JOB = {
    "company": "테스트컴퍼니",
    "title": "AI 엔지니어",
    "location": "서울 마곡",
    "skills_required": ["Python", "PyTorch"],
}

SAMPLE_POOL = ["학력: 한국대학교 컴퓨터공학과 (학사)", "스킬: Python (수준: 고급)"]
SAMPLE_MARKERS = ["SM-01: 수치 표현 (예시: 40% 개선)"]
SAMPLE_APS = ["AP-01: AI 투명체 표현 금지"]


@pytest.fixture
def tmp_db(tmp_path):
    db = tmp_path / "test.db"
    init_db(db)
    return db


# ──────────────────────────────────────────
# synthesizer
# ──────────────────────────────────────────

class TestSynthesizer:
    def test_synthesize_success(self):
        mock_response = {
            "결과": "성공",
            "text": "저는 AI 개발 역량을 바탕으로 귀사에 기여하겠습니다. 처리 속도를 40% 개선했습니다.",
            "token_used": 100,
        }
        with patch("job_agent.features.document.internal.synthesizer._get_router") as mock_get:
            mock_router = MagicMock()
            mock_router.generate.return_value = mock_response
            mock_get.return_value = mock_router

            result = synthesize(SAMPLE_JOB, SAMPLE_POOL, SAMPLE_MARKERS, SAMPLE_APS)

        assert result["결과"] == "성공"
        assert len(result["content"]) > 0
        assert len(result["draft_id"]) == 16

    def test_llm_failure_returns_failure(self):
        with patch("job_agent.features.document.internal.synthesizer._get_router") as mock_get:
            mock_router = MagicMock()
            mock_router.generate.return_value = {"결과": "실패", "이유": "API 오류"}
            mock_get.return_value = mock_router

            result = synthesize(SAMPLE_JOB, SAMPLE_POOL, SAMPLE_MARKERS, SAMPLE_APS)

        assert result["결과"] == "실패"

    def test_empty_llm_response_returns_failure(self):
        with patch("job_agent.features.document.internal.synthesizer._get_router") as mock_get:
            mock_router = MagicMock()
            mock_router.generate.return_value = {"결과": "성공", "text": ""}
            mock_get.return_value = mock_router

            result = synthesize(SAMPLE_JOB, SAMPLE_POOL, SAMPLE_MARKERS, SAMPLE_APS)

        assert result["결과"] == "실패"
        assert "빈 응답" in result["이유"]

    def test_draft_id_deterministic(self):
        content = "같은 내용의 자소서"
        id1 = _make_draft_id(content)
        id2 = _make_draft_id(content)
        assert id1 == id2
        assert len(id1) == 16

    def test_fill_prompt_includes_job_info(self):
        template = "회사: {{job_posting}}\n풀: {{content_pool}}\n마커: {{style_markers}}\n안티: {{anti_patterns}}"
        filled = _fill_prompt(template, SAMPLE_JOB, SAMPLE_POOL, SAMPLE_MARKERS, SAMPLE_APS)
        assert "테스트컴퍼니" in filled
        assert "Python" in filled

    def test_fill_prompt_empty_pool(self):
        template = "풀: {{content_pool}}"
        filled = _fill_prompt(template, SAMPLE_JOB, [], [], [])
        assert "(없음)" in filled


# ──────────────────────────────────────────
# pool_loader
# ──────────────────────────────────────────

class TestPoolLoader:
    def test_no_persona_returns_failure(self, tmp_db):
        result = load_content_pool("user_없음", db_path=tmp_db)
        assert result["결과"] == "실패"
        assert "페르소나 없음" in result["이유"]

    def test_with_mock_persona(self):
        mock_persona = MagicMock()
        mock_persona.name = "어창선"
        mock_persona.educations = [MagicMock(school="한국대", major="컴공", degree="학사")]
        mock_persona.skills = [MagicMock(name="Python", level="고급")]
        mock_persona.content_assets = []
        mock_persona.career_history = []
        mock_persona.style_markers = [MagicMock(marker_id="SM-01", description="수치 표현", example="40%")]
        mock_persona.anti_patterns = [MagicMock(pattern_id="AP-01", description="AI 투명체")]
        mock_persona.target_jobs = [MagicMock(job_role="AI 엔지니어", industry="IT")]

        with patch("job_agent.features.document.internal.pool_loader.get_persona", return_value=mock_persona):
            result = load_content_pool("u1")

        assert result["결과"] == "성공"
        assert any("한국대" in item for item in result["content_pool"])
        assert any("Python" in item for item in result["content_pool"])
        assert any("SM-01" in m for m in result["style_markers"])
        assert "어창선" in result["persona_summary"]
