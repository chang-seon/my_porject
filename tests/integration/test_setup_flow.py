"""DAY 13 — core orchestrator 셋업 흐름 통합 테스트"""
import pytest
from unittest.mock import patch, MagicMock
from job_agent.core import orchestrator


class TestRunSetup:
    def test_setup_returns_failure_on_empty_files(self, tmp_path):
        result = orchestrator.run_setup("u001", [tmp_path / "없음.txt"])
        assert result["결과"] == "실패"

    def test_setup_mocked_success(self, tmp_path):
        txt = tmp_path / "resume.txt"
        txt.write_text("이름: 어창선\nAI 엔지니어 지망", encoding="utf-8")

        import json
        mock_persona_dict = {
            "name": "어창선", "user_id": "u001", "career_stage": "신입",
            "education": [], "target_jobs": [], "content_assets": [],
            "skills": [], "style_markers": [], "anti_patterns": [],
            "traits": [], "values": [], "constraints": [], "career_history": [],
        }
        with patch("job_agent.features.persona.internal.llm_extract.LLMRouter") as MockRouter:
            mock_instance = MagicMock()
            mock_instance.generate.return_value = json.dumps(mock_persona_dict)
            MockRouter.return_value = mock_instance
            with patch("job_agent.features.persona.internal.storage.upsert_persona",
                       return_value={"결과": "성공"}), \
                 patch("job_agent.core.router.call", return_value={"결과": "성공"}):
                result = orchestrator.run_setup("u001", [str(txt)])
        assert result["결과"] == "성공"
        assert result["name"] == "어창선"


class TestRunDailyCycle:
    def test_daily_cycle_calls_fetch_and_filter(self):
        with patch("job_agent.core.router.call", return_value={"결과": "실패", "이유": "stub"}):
            result = orchestrator.run_daily_cycle("u001")
        assert "결과" in result
