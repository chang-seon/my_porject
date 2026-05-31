from __future__ import annotations
import os
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

_DB_PATH = Path(os.getenv("DB_PATH", r"D:\IT\Agentic_AI\data\agent.db"))

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS cost_log (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    model         TEXT NOT NULL,
    input_tokens  INTEGER NOT NULL,
    output_tokens INTEGER NOT NULL,
    cost_usd      REAL NOT NULL,
    source_module TEXT,
    task_type     TEXT,
    timestamp     TEXT,
    year          INTEGER,
    month         INTEGER,
    day           INTEGER
);
"""


def _ensure_table() -> None:
    import sqlite3
    _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(_DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript(_CREATE_TABLE)
    conn.commit()
    conn.close()


def record_cost(
    model: str,
    input_tokens: int,
    output_tokens: int,
    cost_usd: float,
    source_module: str = "unknown",
    task_type: str = "unknown",
) -> None:
    try:
        import sqlite3
        _ensure_table()
        now = datetime.now(timezone.utc)
        conn = sqlite3.connect(str(_DB_PATH))
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute(
            """INSERT INTO cost_log
               (model, input_tokens, output_tokens, cost_usd, source_module, task_type,
                timestamp, year, month, day)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (model, input_tokens, output_tokens, cost_usd, source_module, task_type,
             now.isoformat(), now.year, now.month, now.day),
        )
        conn.commit()
        conn.close()
    except Exception:
        pass  # 비용 추적 실패가 주 기능을 막지 않도록


def get_daily_summary(year: int, month: int, day: int) -> dict:
    try:
        import sqlite3
        _ensure_table()
        conn = sqlite3.connect(str(_DB_PATH))
        rows = conn.execute(
            """SELECT model, SUM(input_tokens), SUM(output_tokens), SUM(cost_usd)
               FROM cost_log WHERE year=? AND month=? AND day=?
               GROUP BY model""",
            (year, month, day),
        ).fetchall()
        conn.close()
        return {
            "결과": "성공",
            "날짜": f"{year}-{month:02d}-{day:02d}",
            "모델별": [
                {"model": r[0], "입력토큰": r[1], "출력토큰": r[2], "비용USD": round(r[3], 6)}
                for r in rows
            ],
        }
    except Exception as e:
        return {"결과": "실패", "이유": str(e)}
