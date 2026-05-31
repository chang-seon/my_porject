from __future__ import annotations
from datetime import datetime, timezone
from pathlib import Path

from job_agent.shared.db.connection import get_connection, _DEFAULT_DB_PATH
from job_agent.shared.db.repositories.persona_repo import upsert_persona, get_persona
from job_agent.shared.schemas.persona import Persona


def save_persona(persona: Persona, db_path: Path = _DEFAULT_DB_PATH) -> dict:
    """페르소나를 DB에 저장(upsert)하고 이벤트 로그를 기록한다."""
    try:
        result = upsert_persona(persona, db_path=db_path)
        if result["결과"] == "실패":
            return result
        _log_event(persona.user_id, "persona_saved", {"name": persona.name}, db_path)
        return {"결과": "성공", "user_id": persona.user_id}
    except Exception as e:
        return {"결과": "실패", "이유": str(e)}


def load_persona(user_id: str, db_path: Path = _DEFAULT_DB_PATH) -> dict:
    """DB에서 페르소나를 조회한다."""
    try:
        persona = get_persona(user_id, db_path=db_path)
        if persona is None:
            return {"결과": "실패", "이유": f"페르소나 없음: {user_id}"}
        return {"결과": "성공", "persona": persona.model_dump()}
    except Exception as e:
        return {"결과": "실패", "이유": str(e)}


def _log_event(user_id: str, event_type: str, event_data: dict, db_path: Path) -> None:
    import json
    now = datetime.now(timezone.utc)
    conn = get_connection(db_path)
    try:
        conn.execute(
            "INSERT INTO event_logs (user_id,event_type,event_data,timestamp,year,month,day) VALUES (?,?,?,?,?,?,?)",
            (user_id, event_type, json.dumps(event_data, ensure_ascii=False),
             now.isoformat(), now.year, now.month, now.day),
        )
        conn.commit()
    finally:
        conn.close()
