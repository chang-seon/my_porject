"""2차 LLM 심사관 — Claude로 자소서 심층 검증."""
from __future__ import annotations

import json
from pathlib import Path

from job_agent.shared.llm.router import LLMRouter

_PROMPT_PATH = Path(__file__).parent / "prompts" / "cover_letter_judge.md"
_router: LLMRouter | None = None


def _get_router() -> LLMRouter:
    global _router
    if _router is None:
        _router = LLMRouter()
    return _router


def judge_cover_letter(content: str, persona_summary: str = "") -> dict:
    """Claude로 자소서를 2차 심사한다.

    반환:
      passed: bool
      score: float
      issues: list[dict]
      summary: str
      raw_response: str (디버그용)
    """
    try:
        prompt_template = _PROMPT_PATH.read_text(encoding="utf-8")
        prompt = prompt_template.replace("{{content}}", content).replace("{{persona_summary}}", persona_summary)

        response = _get_router().generate(prompt, task_type="validate_cover_letter")
        if response.get("결과") == "실패":
            return {"결과": "실패", "이유": response.get("이유", "LLM 호출 실패")}

        raw_text = response.get("text", "")
        parsed = _parse_judge_response(raw_text)
        parsed["raw_response"] = raw_text
        parsed["결과"] = "성공"
        return parsed
    except Exception as e:
        return {"결과": "실패", "이유": str(e)}


def _parse_judge_response(text: str) -> dict:
    """LLM 응답에서 JSON을 추출한다."""
    try:
        if "```" in text:
            start = text.find("{", text.find("```"))
            end = text.rfind("}") + 1
            text = text[start:end]
        else:
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                text = text[start:end]

        data = json.loads(text)
        return {
            "passed": bool(data.get("passed", False)),
            "score": float(data.get("score", 0.0)),
            "issues": data.get("issues", []),
            "summary": data.get("summary", ""),
        }
    except Exception:
        return {"passed": False, "score": 0.0, "issues": [], "summary": "파싱 실패"}
