from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path

from job_agent.shared.db.connection import get_connection, _DEFAULT_DB_PATH


def record_change(
    user_id: str,
    section: str,
    before: dict | None,
    after: dict | None,
    reason: str = "",
    trigger: str = "manual",
    db_path: Path = _DEFAULT_DB_PATH,
) -> dict:
    """페르소나 변경 전·후를 changelog 테이블에 기록한다. (#37)"""
    try:
        now = datetime.now(timezone.utc)
        conn = get_connection(db_path)
        try:
            conn.execute(
                """INSERT INTO persona_changelog
                   (user_id, section, before_json, after_json, reason, trigger,
                    timestamp, year, month, day)
                   VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (user_id, section,
                 json.dumps(before, ensure_ascii=False) if before is not None else None,
                 json.dumps(after, ensure_ascii=False) if after is not None else None,
                 reason, trigger,
                 now.isoformat(), now.year, now.month, now.day),
            )
            conn.commit()
        finally:
            conn.close()
        return {"결과": "성공", "section": section}
    except Exception as e:
        return {"결과": "실패", "이유": str(e)}


def get_changelog(user_id: str, section: str | None = None, db_path: Path = _DEFAULT_DB_PATH) -> dict:
    """변경 이력을 조회한다. section 지정 시 해당 섹션만."""
    try:
        conn = get_connection(db_path)
        try:
            if section:
                rows = conn.execute(
                    "SELECT * FROM persona_changelog WHERE user_id=? AND section=? ORDER BY id DESC",
                    (user_id, section)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM persona_changelog WHERE user_id=? ORDER BY id DESC",
                    (user_id,)
                ).fetchall()
        finally:
            conn.close()
        return {"결과": "성공", "history": [dict(r) for r in rows]}
    except Exception as e:
        return {"결과": "실패", "이유": str(e)}
