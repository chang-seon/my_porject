# 보호 컴포넌트 — 수정 시 사용자 승인 필수 (CLAUDE.md 참조)
# features/ 모듈간 직접 import 금지 — 반드시 이 파일을 거친다
from __future__ import annotations

import job_agent.features.persona.interface as persona
import job_agent.features.job_search.interface as job_search
import job_agent.features.document.interface as document
import job_agent.features.validator.interface as validator
import job_agent.features.notification.interface as notification
import job_agent.features.application.interface as application
import job_agent.features.interview.interface as interview
import job_agent.features.learner.interface as learner


def call(module: str, fn: str, **kwargs) -> dict:
    """모듈명 + 함수명으로 features/ 함수를 호출한다.

    module: "persona" | "job_search" | "document" | "validator" |
            "notification" | "application" | "interview" | "learner"
    """
    _map = {
        "persona":      persona,
        "job_search":   job_search,
        "document":     document,
        "validator":    validator,
        "notification": notification,
        "application":  application,
        "interview":    interview,
        "learner":      learner,
    }
    try:
        mod = _map.get(module)
        if mod is None:
            return {"결과": "실패", "이유": f"알 수 없는 모듈: {module}"}
        func = getattr(mod, fn, None)
        if func is None:
            return {"결과": "실패", "이유": f"{module}.{fn} 함수 없음"}
        return func(**kwargs)
    except Exception as e:
        return {"결과": "실패", "이유": str(e)}
