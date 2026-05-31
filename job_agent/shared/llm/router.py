from __future__ import annotations
from typing import Optional

from job_agent.shared.llm.base import LLMClient
from job_agent.shared.llm.claude_client import ClaudeClient
from job_agent.shared.llm.gemini_client import GeminiClient
from job_agent.shared.llm.cost_tracker import record_cost

# 작업 유형별 모델 라우팅 (PLAN_DAYS.md 1-2 분배 원칙)
_ROUTING: dict[str, str] = {
    "architecture_review": "claude-opus-4-8",
    "interface_design":    "claude-opus-4-8",
    "decision":            "claude-opus-4-8",
    "implementation":      "claude-sonnet-4-6",
    "test":                "claude-sonnet-4-6",
    "document":            "claude-sonnet-4-6",
    "web_search":          "gemini",
    "fallback":            "claude-sonnet-4-6",
}

# 모델별 1K 토큰당 비용 (USD, 입력 기준)
_COST_PER_1K: dict[str, float] = {
    "claude-opus-4-8":   0.015,
    "claude-sonnet-4-6": 0.003,
    "gemini":            0.00035,
}


class LLMRouter:

    def __init__(self):
        self._claude_sonnet = ClaudeClient(model="claude-sonnet-4-6")
        self._claude_opus   = ClaudeClient(model="claude-opus-4-8")
        self._gemini        = GeminiClient()

    def _get_client(self, task_type: str) -> tuple[LLMClient, str]:
        model_key = _ROUTING.get(task_type, _ROUTING["fallback"])
        if model_key == "gemini":
            return self._gemini, "gemini"
        if "opus" in model_key:
            return self._claude_opus, model_key
        return self._claude_sonnet, model_key

    def generate(
        self,
        prompt: str,
        task_type: str = "implementation",
        system: Optional[str] = None,
        source_module: str = "unknown",
        **kwargs,
    ) -> str:
        client, model_key = self._get_client(task_type)
        input_tokens = client.count_tokens(prompt)
        result = client.generate(prompt, system=system, **kwargs)
        output_tokens = client.count_tokens(result)
        cost = (input_tokens + output_tokens) / 1000 * _COST_PER_1K.get(model_key, 0)
        record_cost(model=model_key, input_tokens=input_tokens,
                    output_tokens=output_tokens, cost_usd=cost,
                    source_module=source_module, task_type=task_type)
        return result
