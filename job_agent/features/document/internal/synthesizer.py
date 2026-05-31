"""자소서 합성기 — Claude 호출 + 본인 문체 마커 주입."""
from __future__ import annotations

import hashlib
from pathlib import Path

from job_agent.shared.llm.router import LLMRouter

_PROMPT_PATH = Path(__file__).parent / "prompts" / "generate_cover_letter.md"
_router: LLMRouter | None = None


def _get_router() -> LLMRouter:
    global _router
    if _router is None:
        _router = LLMRouter()
    return _router


def synthesize(
    job_posting: dict,
    content_pool: list[str],
    style_markers: list[str],
    anti_patterns: list[str],
) -> dict:
    """Claude로 자소서 초안을 생성한다.

    반환:
      content: 생성된 자소서 텍스트
      draft_id: SHA256 해시 기반 고유 ID
      token_used: 사용된 토큰 수 (근사치)
    """
    try:
        prompt_template = _PROMPT_PATH.read_text(encoding="utf-8")
        prompt = _fill_prompt(prompt_template, job_posting, content_pool, style_markers, anti_patterns)

        response = _get_router().generate(prompt, task_type="generate_document")
        if response.get("결과") == "실패":
            return {"결과": "실패", "이유": response.get("이유", "LLM 호출 실패")}

        content = response.get("text", "").strip()
        if not content:
            return {"결과": "실패", "이유": "LLM이 빈 응답 반환"}

        draft_id = _make_draft_id(content)
        return {
            "결과": "성공",
            "content": content,
            "draft_id": draft_id,
            "token_used": response.get("token_used", 0),
        }
    except Exception as e:
        return {"결과": "실패", "이유": str(e)}


def _fill_prompt(
    template: str,
    job_posting: dict,
    content_pool: list[str],
    style_markers: list[str],
    anti_patterns: list[str],
) -> str:
    job_text = (
        f"회사: {job_posting.get('company', '미상')}\n"
        f"직무: {job_posting.get('title', '미상')}\n"
        f"지역: {job_posting.get('location', '미상')}\n"
        f"필요스킬: {', '.join(job_posting.get('skills_required', []))}"
    )
    pool_text = "\n".join(f"- {item}" for item in content_pool) if content_pool else "(없음)"
    sm_text = "\n".join(f"- {m}" for m in style_markers) if style_markers else "(없음)"
    ap_text = "\n".join(f"- {a}" for a in anti_patterns) if anti_patterns else "(없음)"

    return (
        template
        .replace("{{job_posting}}", job_text)
        .replace("{{content_pool}}", pool_text)
        .replace("{{style_markers}}", sm_text)
        .replace("{{anti_patterns}}", ap_text)
    )


def _make_draft_id(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]
