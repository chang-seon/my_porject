"""지원 기록 저장 및 상태 갱신."""
from __future__ import annotations

import json
import uuid
from datetime import date
from pathlib import Path

from job_agent.shared.db.connection import get_connection, init_db

_DEFAULT_DB_PATH = Path(__file__).parents[4] / "data" / "agent.db"

_VALID_STATUSES = {"지원완료", "서류통과", "면접", "최종합격", "불합격", "보류"}


def record_application(
    job_id: str,
    user_id: str,
    draft_id: str,
    job_posting: dict | None = None,
    db_path: Path | None = None,
) -> dict:
    """지원 기록을 event_logs에 저장하고 application_id를 반환한다."""
    try:
        _db = db_path or _DEFAULT_DB_PATH
        init_db(_db)

        application_id = _make_application_id(user_id, job_id)
        posting = job_posting or {}

        conn = get_connection(_db)
        try:
            conn.execute(
                "INSERT INTO event_logs(user_id, event_type, event_data, year, month, day) VALUES(?,?,?,?,?,?)",
                (
                    user_id,
                    "application_created",
                    json.dumps({
                        "application_id": application_id,
                        "job_id": job_id,
                        "draft_id": draft_id,
                        "company": posting.get("company", ""),
                        "job_title": posting.get("title", ""),
                        "apply_url": posting.get("url", ""),
                        "status": "지원완료",
                    }, ensure_ascii=False),
                    *_today_ymd(),
                ),
            )
            conn.commit()
        finally:
            conn.close()

        return {
            "결과": "성공",
            "application_id": application_id,
            "apply_url": posting.get("url", ""),
            "status": "지원완료",
        }
    except Exception as e:
        return {"결과": "실패", "이유": str(e)}


def update_application_status(
    application_id: str,
    status: str,
    user_id: str = "",
    result: str | None = None,
    db_path: Path | None = None,
) -> dict:
    """지원 상태를 갱신하고 학습신호 E층에 기록한다."""
    try:
        if status not in _VALID_STATUSES:
            return {"결과": "실패", "이유": f"유효하지 않은 상태: {status}. 허용값: {_VALID_STATUSES}"}

        _db = db_path or _DEFAULT_DB_PATH
        conn = get_connection(_db)
        try:
            conn.execute(
                "INSERT INTO event_logs(user_id, event_type, event_data, year, month, day) VALUES(?,?,?,?,?,?)",
                (
                    user_id,
                    "application_updated",
                    json.dumps({
                        "application_id": application_id,
                        "status": status,
                        "result": result or "",
                    }, ensure_ascii=False),
                    *_today_ymd(),
                ),
            )
            # 학습신호 E층: 최종 결과가 나온 경우 기록
            if status in {"최종합격", "불합격"}:
                conn.execute(
                    "INSERT INTO learning_signals(user_id, layer, signal_type, payload, year, month, day) VALUES(?,?,?,?,?,?,?)",
                    (
                        user_id,
                        "E",
                        f"application_{status}",
                        json.dumps({"application_id": application_id, "result": result or ""}, ensure_ascii=False),
                        *_today_ymd(),
                    ),
                )
            conn.commit()
        finally:
            conn.close()

        return {"결과": "성공", "application_id": application_id, "status": status}
    except Exception as e:
        return {"결과": "실패", "이유": str(e)}


def get_application_history(user_id: str, db_path: Path | None = None) -> dict:
    """전체 지원 이력을 조회한다."""
    try:
        _db = db_path or _DEFAULT_DB_PATH
        conn = get_connection(_db)
        try:
            rows = conn.execute(
                "SELECT event_data, year, month, day FROM event_logs "
                "WHERE user_id=? AND event_type='application_created' ORDER BY rowid DESC",
                (user_id,),
            ).fetchall()
        finally:
            conn.close()

        applications = []
        for row in rows:
            data = json.loads(row["event_data"])
            data["date"] = f"{row['year']}-{row['month']:02d}-{row['day']:02d}"
            applications.append(data)

        return {"결과": "성공", "applications": applications, "total": len(applications)}
    except Exception as e:
        return {"결과": "실패", "이유": str(e)}


def _make_application_id(user_id: str, job_id: str) -> str:
    import hashlib
    seed = f"{user_id}:{job_id}:{date.today().isoformat()}"
    return "APP-" + hashlib.sha256(seed.encode()).hexdigest()[:12]


def _today_ymd():
    d = date.today()
    return d.year, d.month, d.day
