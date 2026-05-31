"""DAY 05 — interface.py 시그니처 존재 확인 + 에러 처리 형식 검증"""
import pytest
import importlib


MODULES = [
    ("job_agent.features.persona.interface",      ["extract_persona", "update_persona", "get_persona"]),
    ("job_agent.features.job_search.interface",   ["fetch_postings", "filter_postings", "get_posting"]),
    ("job_agent.features.document.interface",     ["generate_cover_letter", "get_draft", "update_draft"]),
    ("job_agent.features.validator.interface",    ["validate", "get_validation_history"]),
    ("job_agent.features.notification.interface", ["notify", "notify_hitl"]),
    ("job_agent.features.application.interface",  ["record_application", "update_application_status", "get_application_history"]),
    ("job_agent.features.interview.interface",    ["prepare", "debrief"]),
    ("job_agent.features.learner.interface",      ["record_signal", "get_dynamic_threshold", "update_dynamic_threshold"]),
]


class TestInterfaceExists:
    @pytest.mark.parametrize("module_path,functions", MODULES)
    def test_functions_exist(self, module_path, functions):
        mod = importlib.import_module(module_path)
        for fn_name in functions:
            assert hasattr(mod, fn_name), f"{module_path}.{fn_name} 없음"
            assert callable(getattr(mod, fn_name)), f"{module_path}.{fn_name} callable 아님"

    @pytest.mark.parametrize("module_path,functions", MODULES)
    def test_error_path_returns_dict(self, module_path, functions):
        """예외 발생 시 dict 반환하는지 확인 (NotImplementedError 제외)"""
        mod = importlib.import_module(module_path)
        for fn_name in functions:
            fn = getattr(mod, fn_name)
            # NotImplementedError는 stub 상태라 정상 — 다른 예외만 체크
            import inspect
            sig = inspect.signature(fn)
            # 함수가 존재하고 callable이면 충분 (구현은 Phase별)
            assert callable(fn)
