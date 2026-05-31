"""DAY 06/13 — orchestrator 함수 존재 + 반환 형식 검증"""
import pytest
from job_agent.core import orchestrator, router

ORCHESTRATOR_FNS = [
    "run_setup", "fetch_and_filter", "generate_and_validate",
    "hitl_review", "submit_application", "track_result",
    "handle_pass", "prepare_interview", "debrief_interview", "run_daily_cycle",
]


class TestOrchestratorExists:
    @pytest.mark.parametrize("fn_name", ORCHESTRATOR_FNS)
    def test_function_exists_and_callable(self, fn_name):
        fn = getattr(orchestrator, fn_name, None)
        assert fn is not None, f"{fn_name} 없음"
        assert callable(fn)

    @pytest.mark.parametrize("fn_name", ORCHESTRATOR_FNS)
    def test_returns_dict_on_error(self, fn_name):
        """잘못된 인자로 호출 시 dict를 반환하거나 예외를 발생시킨다 (구현된 함수)."""
        fn = getattr(orchestrator, fn_name)
        import inspect
        params = list(inspect.signature(fn).parameters.keys())
        kwargs = {p: "invalid_test_value" for p in params}
        try:
            result = fn(**kwargs)
            assert isinstance(result, dict), f"{fn_name}: dict 반환 필요"
            assert "결과" in result
        except (NotImplementedError, TypeError):
            pass  # stub 또는 인자 오류 — 허용


class TestRouter:
    def test_unknown_module_returns_failure(self):
        result = router.call("없는모듈", "some_fn")
        assert result["결과"] == "실패"
        assert "알 수 없는 모듈" in result["이유"]

    def test_unknown_function_returns_failure(self):
        result = router.call("persona", "없는함수")
        assert result["결과"] == "실패"
        assert "함수 없음" in result["이유"]

    def test_valid_call_returns_dict(self):
        result = router.call("persona", "extract_persona", files=[], user_id="test")
        assert isinstance(result, dict)
        assert "결과" in result
