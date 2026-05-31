from __future__ import annotations
import os
from typing import Iterator, Optional

import anthropic
from dotenv import load_dotenv

from job_agent.shared.llm.base import LLMClient

load_dotenv()

_DEFAULT_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6")


class ClaudeClient(LLMClient):

    def __init__(self, model: str = _DEFAULT_MODEL):
        self.model = model
        self._client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    def generate(self, prompt: str, system: Optional[str] = None, **kwargs) -> str:
        try:
            messages = [{"role": "user", "content": prompt}]
            params = {"model": self.model, "max_tokens": kwargs.get("max_tokens", 4096), "messages": messages}
            if system:
                params["system"] = system
            response = self._client.messages.create(**params)
            return response.content[0].text
        except Exception as e:
            return f"[오류] Claude 호출 실패: {e}"

    def stream(self, prompt: str, system: Optional[str] = None, **kwargs) -> Iterator[str]:
        try:
            messages = [{"role": "user", "content": prompt}]
            params = {"model": self.model, "max_tokens": kwargs.get("max_tokens", 4096), "messages": messages}
            if system:
                params["system"] = system
            with self._client.messages.stream(**params) as stream:
                for text in stream.text_stream:
                    yield text
        except Exception as e:
            yield f"[오류] Claude 스트리밍 실패: {e}"

    def count_tokens(self, text: str) -> int:
        try:
            response = self._client.messages.count_tokens(
                model=self.model,
                messages=[{"role": "user", "content": text}],
            )
            return response.input_tokens
        except Exception:
            return len(text) // 4
