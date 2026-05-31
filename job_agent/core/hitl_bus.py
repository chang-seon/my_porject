# 보호 컴포넌트 — 수정 시 사용자 승인 필수 (CLAUDE.md 참조)
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path

from job_agent.shared.db.connection import get_connection, _DEFAULT_DB_PATH

_CREATE = """
CREATE TABLE IF NOT EXISTS hitl_requests (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id  TEXT NOT NULL UNIQUE,
    user_id     TEXT NOT NULL,
    question    TEXT NOT NULL,
    options     TEXT NOT NULL,
    status      TEXT DEFAULT 'pending',
    response    TEXT,
    created_at  TEXT,
    responded_at TEXT
);
"""


def _ensure_table(db_path: Path) -> None:
    conn = get_connection(db_path)
    conn.executescript(_CREATE)
    conn.commit()
    conn.close()


def create_request(request_id: str, user_id: str, question: str,
                   options: list[str], db_path: Path = _DEFAULT_DB_PATH) -> dict:
    """HITL 요청을 DB에 생성한다."""
    try:
        _ensure_table(db_path)
        now = datetime.now(timezone.utc).isoformat()
        conn = get_connection(db_path)
        conn.execute(
            "INSERT INTO hitl_requests (request_id,user_id,question,options,created_at) VALUES (?,?,?,?,?)",
            (request_id, user_id, question, json.dumps(options, ensure_ascii=False), now),
        )
        conn.commit()
        conn.close()
        return {"결과": "성공", "request_id": request_id}
    except Exception as e:
        return {"결과": "실패", "이유": str(e)}


def respond(request_id: str, response: str, db_path: Path = _DEFAULT_DB_PATH) -> dict:
    """HITL 요청에 응답을 기록한다."""
    try:
        _ensure_table(db_path)
        now = datetime.now(timezone.utc).isoformat()
        conn = get_connection(db_path)
        conn.execute(
            "UPDATE hitl_requests SET status='responded', response=?, responded_at=? WHERE request_id=?",
            (response, now, request_id),
        )
        conn.commit()
        conn.close()
        return {"결과": "성공", "request_id": request_id, "response": response}
    except Exception as e:
        return {"결과": "실패", "이유": str(e)}


def get_pending(user_id: str, db_path: Path = _DEFAULT_DB_PATH) -> dict:
    """대기 중인 HITL 요청 목록을 반환한다."""
    try:
        _ensure_table(db_path)
        conn = get_connection(db_path)
        rows = conn.execute(
            "SELECT * FROM hitl_requests WHERE user_id=? AND status='pending' ORDER BY id",
            (user_id,),
        ).fetchall()
        conn.close()
        return {"결과": "성공", "requests": [dict(r) for r in rows]}
    except Exception as e:
        return {"결과": "실패", "이유": str(e)}
