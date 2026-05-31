from __future__ import annotations
import os
from typing import Iterator, Optional

from google import genai
from google.genai import types
from dotenv import load_dotenv

from job_agent.shared.llm.base import LLMClient

load_dotenv()

_DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")


class GeminiClient(LLMClient):

    def __init__(self, model: str = _DEFAULT_MODEL):
        self.model = model
        self._client = genai.Client(api_key=os.getenv("GOOGLE_AI_API_KEY", ""))

    def generate(self, prompt: str, system: Optional[str] = None, **kwargs) -> str:
        try:
            config = types.GenerateContentConfig(system_instruction=system) if system else None
            response = self._client.models.generate_content(
                model=self.model, contents=prompt, config=config
            )
            return response.text
        except Exception as e:
            return f"[오류] Gemini 호출 실패: {e}"

    def stream(self, prompt: str, system: Optional[str] = None, **kwargs) -> Iterator[str]:
        try:
            config = types.GenerateContentConfig(system_instruction=system) if system else None
            for chunk in self._client.models.generate_content_stream(
                model=self.model, contents=prompt, config=config
            ):
                yield chunk.text
        except Exception as e:
            yield f"[오류] Gemini 스트리밍 실패: {e}"

    def count_tokens(self, text: str) -> int:
        try:
            result = self._client.models.count_tokens(model=self.model, contents=text)
            return result.total_tokens
        except Exception:
            return len(text) // 4
