from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path

from job_agent.shared.db.connection import get_connection, _DEFAULT_DB_PATH
from job_agent.shared.schemas.learning_signal import LearningSignal, SignalLayer


def record_signal(signal: LearningSignal, db_path: Path = _DEFAULT_DB_PATH) -> dict:
    """학습신호 A~E층을 DB에 기록한다."""
    try:
        now = datetime.now(timezone.utc)
        timestamp = signal.timestamp or now.isoformat()
        year = signal.year or now.year
        month = signal.month or now.month
        day = signal.day or now.day

        conn = get_connection(db_path)
        cursor = conn.execute(
            """INSERT INTO learning_signals
               (user_id, layer, signal_type, payload, source_module, reference_id,
                is_labeled, label, revision_history, timestamp, year, month, day)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (signal.user_id, signal.layer.value, signal.signal_type,
             json.dumps(signal.payload, ensure_ascii=False),
             signal.source_module, signal.reference_id,
             int(signal.is_labeled), signal.label,
             json.dumps(signal.revision_history, ensure_ascii=False),
             timestamp, year, month, day),
        )
        conn.commit()
        signal_id = cursor.lastrowid
        conn.close()
        return {"결과": "성공", "signal_id": signal_id, "layer": signal.layer.value}
    except Exception as e:
        return {"결과": "실패", "이유": str(e)}


def get_signals(user_id: str, layer: str | None = None,
                db_path: Path = _DEFAULT_DB_PATH) -> dict:
    """학습신호를 조회한다. layer 지정 시 해당 층만."""
    try:
        conn = get_connection(db_path)
        if layer:
            rows = conn.execute(
                "SELECT * FROM learning_signals WHERE user_id=? AND layer=? ORDER BY id DESC",
                (user_id, layer)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM learning_signals WHERE user_id=? ORDER BY id DESC",
                (user_id,)
            ).fetchall()
        conn.close()
        return {"결과": "성공", "signals": [dict(r) for r in rows]}
    except Exception as e:
        return {"결과": "실패", "이유": str(e)}
