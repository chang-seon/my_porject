from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from job_agent.shared.db.connection import get_connection, _DEFAULT_DB_PATH

_DEFAULTS: dict[str, Any] = {
    "automation_promotion_n": 5,
    "pass_ratio_threshold": 0.7,
    "min_score_cover_letter": 0.6,
}


def get_threshold(domain: str, context_key: str, user_id: str,
                  db_path: Path = _DEFAULT_DB_PATH) -> dict:
    """동적 기준값을 DB에서 조회한다. 없으면 기본값을 반환한다. (#37)"""
    try:
        conn = get_connection(db_path)
        row = conn.execute(
            "SELECT value FROM dynamic_thresholds WHERE user_id=? AND domain=? AND context_key=?",
            (user_id, domain, context_key),
        ).fetchone()
        conn.close()
        if row:
            return {"결과": "성공", "value": row["value"], "source": "db"}
        default_key = f"{domain}_{context_key}"
        default = _DEFAULTS.get(default_key, _DEFAULTS.get(context_key))
        if default is not None:
            return {"결과": "성공", "value": default, "source": "default"}
        return {"결과": "실패", "이유": f"기준값 없음: {domain}.{context_key}"}
    except Exception as e:
        return {"결과": "실패", "이유": str(e)}


def update_threshold(domain: str, context_key: str, value: Any, user_id: str,
                     db_path: Path = _DEFAULT_DB_PATH) -> dict:
    """동적 기준값을 갱신하고 변경 이력을 기록한다. (#37)"""
    try:
        now = datetime.now(timezone.utc).isoformat()
        conn = get_connection(db_path)
        existing = conn.execute(
            "SELECT value, change_history FROM dynamic_thresholds WHERE user_id=? AND domain=? AND context_key=?",
            (user_id, domain, context_key),
        ).fetchone()

        if existing:
            history = json.loads(existing["change_history"] or "[]")
            history.append({"old": existing["value"], "changed_at": now})
            conn.execute(
                "UPDATE dynamic_thresholds SET value=?, changed_at=?, change_history=? WHERE user_id=? AND domain=? AND context_key=?",
                (str(value), now, json.dumps(history), user_id, domain, context_key),
            )
        else:
            conn.execute(
                "INSERT INTO dynamic_thresholds (user_id,domain,context_key,value,changed_at,change_history) VALUES (?,?,?,?,?,?)",
                (user_id, domain, context_key, str(value), now, "[]"),
            )
        conn.commit()
        conn.close()
        return {"결과": "성공", "domain": domain, "context_key": context_key, "value": value}
    except Exception as e:
        return {"결과": "실패", "이유": str(e)}
