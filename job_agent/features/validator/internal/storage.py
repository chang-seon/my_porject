"""검증 결과 저장 — Q5: 전 과정 DB 기록."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from job_agent.shared.db.connection import get_connection, _DEFAULT_DB_PATH


def save_validation_result(
    user_id: str,
    target: str,
    content_hash: str,
    result: dict,
    db_path: Path = _DEFAULT_DB_PATH,
) -> dict:
    """검증 결과를 event_logs 테이블에 저장한다 (Q5)."""
    try:
        now = datetime.now(timezone.utc)
        conn = get_connection(db_path)
        conn.execute(
            """INSERT INTO event_logs
               (user_id, event_type, event_data, timestamp, year, month, day)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                user_id,
                f"validation_{target}",
                json.dumps(
                    {
                        "content_hash": content_hash,
                        "passed": result.get("passed"),
                        "score": result.get("score"),
                        "reasons": result.get("reasons", []),
                        "attempts": result.get("attempts", 1),
                        "needs_hitl": result.get("needs_hitl", False),
                    },
                    ensure_ascii=False,
                ),
                now.isoformat(),
                now.year,
                now.month,
                now.day,
            ),
        )
        conn.commit()
        return {"결과": "성공"}
    except Exception as e:
        return {"결과": "실패", "이유": str(e)}


def get_validation_history(
    user_id: str,
    target: str = "cover_letter",
    limit: int = 20,
    db_path: Path = _DEFAULT_DB_PATH,
) -> dict:
    """최근 검증 이력을 반환한다."""
    try:
        conn = get_connection(db_path)
        rows = conn.execute(
            """SELECT event_data, timestamp FROM event_logs
               WHERE user_id = ? AND event_type = ?
               ORDER BY id DESC LIMIT ?""",
            (user_id, f"validation_{target}", limit),
        ).fetchall()
        history = []
        for row in rows:
            try:
                data = json.loads(row["event_data"])
                data["timestamp"] = row["timestamp"]
                history.append(data)
            except Exception:
                pass
        return {"결과": "성공", "history": history, "total": len(history)}
    except Exception as e:
        return {"결과": "실패", "이유": str(e)}
