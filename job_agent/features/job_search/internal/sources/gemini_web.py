"""Gemini 웹탐색 폴백 — 공식 API가 없는 사이트 공고 수집.

직접 크롤링 없이 Gemini의 웹 검색 기능으로 공고 정보를 구조화한다.
환경변수: GOOGLE_AI_API_KEY
"""
from __future__ import annotations

import json
import os

from job_agent.features.job_search.internal.sources.base import JobSource

_SYSTEM_PROMPT = """당신은 채용공고 수집 보조 AI입니다.
주어진 검색 조건으로 최신 채용공고를 찾아 아래 JSON 형식으로 반환하세요.
반드시 JSON 배열만 반환하고 다른 텍스트는 포함하지 마세요.

[
  {
    "job_id": "고유 ID (소스명+숫자)",
    "source": "소스 사이트명",
    "url": "공고 URL",
    "title": "공고 제목",
    "company": "회사명",
    "location": "근무지",
    "job_role": "직무",
    "employment_type": "고용형태",
    "salary": "급여 (없으면 null)",
    "skills_required": ["기술1", "기술2"],
    "posted_date": "YYYY-MM-DD",
    "deadline": "YYYY-MM-DD 또는 null"
  }
]"""


class GeminiWebSource(JobSource):
    source_name = "Gemini웹탐색"

    def __init__(self, api_key: str | None = None):
        self._api_key = api_key or os.getenv("GOOGLE_AI_API_KEY", "")

    def search(self, query: dict) -> dict:
        """Gemini로 웹탐색하여 공고를 수집한다."""
        try:
            if not self._api_key:
                return self._make_error("GOOGLE_AI_API_KEY 환경변수 미설정")

            from google import genai
            from google.genai import types

            client = genai.Client(api_key=self._api_key)
            user_prompt = self._build_prompt(query)

            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=_SYSTEM_PROMPT,
                    temperature=0.1,
                ),
            )
            raw_text = response.text.strip()
            raw_items = self._parse_json(raw_text)
            return {"결과": "성공", "raw_items": raw_items, "total": len(raw_items), "source": self.source_name}
        except Exception as e:
            return self._make_error(str(e))

    def _build_prompt(self, query: dict) -> str:
        parts = []
        if query.get("job_role"):
            parts.append(f"직무: {query['job_role']}")
        if query.get("location"):
            parts.append(f"지역: {query['location']}")
        if query.get("employment_type"):
            parts.append(f"고용형태: {query['employment_type']}")
        count = query.get("count", 10)
        parts.append(f"최대 {count}건")
        return "다음 조건에 맞는 최신 채용공고를 찾아주세요: " + ", ".join(parts)

    @staticmethod
    def _parse_json(text: str) -> list[dict]:
        try:
            # 코드 블록 제거
            if "```" in text:
                lines = text.split("\n")
                lines = [l for l in lines if not l.strip().startswith("```")]
                text = "\n".join(lines)
            return json.loads(text)
        except Exception:
            return []
