import pytest
from unittest.mock import MagicMock, patch
from job_agent.shared.llm.router import LLMRouter, _ROUTING, _COST_PER_1K
from job_agent.shared.llm.cost_tracker import get_daily_summary


class TestRouting:
    def test_implementation_routes_to_sonnet(self):
        assert "sonnet" in _ROUTING["implementation"]

    def test_architecture_routes_to_opus(self):
        assert "opus" in _ROUTING["architecture_review"]

    def test_web_search_routes_to_gemini(self):
        assert _ROUTING["web_search"] == "gemini"

    def test_fallback_is_sonnet(self):
        assert "sonnet" in _ROUTING["fallback"]

    def test_all_routed_models_have_cost(self):
        for task, model in _ROUTING.items():
            assert model in _COST_PER_1K, f"{task} → {model} 비용 테이블 누락"


class TestLLMRouter:
    @pytest.fixture
    def router_with_mocks(self):
        router = LLMRouter.__new__(LLMRouter)
        mock_client = MagicMock()
        mock_client.generate.return_value = "모의 응답"
        mock_client.count_tokens.return_value = 10
        router._claude_sonnet = mock_client
        router._claude_opus   = mock_client
        router._gemini        = mock_client
        return router

    def test_generate_returns_string(self, router_with_mocks):
        with patch("job_agent.shared.llm.router.record_cost"):
            result = router_with_mocks.generate("테스트 프롬프트", task_type="implementation")
        assert result == "모의 응답"

    def test_generate_calls_record_cost(self, router_with_mocks):
        with patch("job_agent.shared.llm.router.record_cost") as mock_record:
            router_with_mocks.generate("프롬프트", task_type="document", source_module="test")
            mock_record.assert_called_once()
            call_kwargs = mock_record.call_args[1]
            assert call_kwargs["source_module"] == "test"
            assert call_kwargs["task_type"] == "document"

    def test_unknown_task_type_uses_fallback(self, router_with_mocks):
        with patch("job_agent.shared.llm.router.record_cost"):
            result = router_with_mocks.generate("프롬프트", task_type="없는작업유형")
        assert result == "모의 응답"


class TestCostTracker:
    def test_daily_summary_returns_dict(self, tmp_path):
        with patch("job_agent.shared.llm.cost_tracker._DB_PATH", tmp_path / "test.db"):
            result = get_daily_summary(2026, 5, 31)
        assert result["결과"] == "성공"
        assert "모델별" in result
