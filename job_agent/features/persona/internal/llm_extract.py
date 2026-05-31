from __future__ import annotations
import json
from pathlib import Path

from job_agent.shared.llm.router import LLMRouter
from job_agent.shared.schemas.persona import Persona

_PROMPT_PATH = Path(__file__).parent / "prompts" / "extract_persona.md"


def extract_persona_from_text(text: str, user_id: str, router: LLMRouter | None = None) -> dict:
    """텍스트에서 Claude를 이용해 페르소나 11섹션을 추출한다."""
    try:
        if router is None:
            router = LLMRouter()
        system = _PROMPT_PATH.read_text(encoding="utf-8")
        raw = router.generate(
            prompt=f"아래 텍스트에서 페르소나를 추출하세요:\n\n{text}",
            task_type="implementation",
            system=system,
            source_module="persona",
        )
        # JSON 블록 추출
        raw = raw.strip()
        if "```json" in raw:
            raw = raw.split("```json")[1].split("```")[0].strip()
        elif "```" in raw:
            raw = raw.split("```")[1].split("```")[0].strip()

        data = json.loads(raw)
        data["user_id"] = user_id
        persona = Persona(**data)
        return {"결과": "성공", "persona": persona.model_dump()}
    except json.JSONDecodeError as e:
        return {"결과": "실패", "이유": f"JSON 파싱 실패: {e}"}
    except Exception as e:
        return {"결과": "실패", "이유": str(e)}
