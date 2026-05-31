"""패스(pass) 및 배제(reject) 처리 — 동일 조건 반복 차단."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from job_agent.shared.db.connection import get_connection, _DEFAULT_DB_PATH

# M11 결정: 동일 조건 = (user_id, company, job_role) 조합이 pass_records에 존재
_SAME_CONDITION_COLS = ("company", "job_role")


def is_passed(posting: dict, user_id: str, db_path: Path = _DEFAULT_DB_PATH) -> bool:
    """이 공고가 이미 패스 처리됐는지 확인한다."""
    try:
        conn = get_connection(db_path)
        row = conn.execute(
            "SELECT 1 FROM pass_records WHERE user_id = ? AND job_url = ? AND is_active = 1",
            (user_id, posting.get("url", "")),
        ).fetchone()
        return row is not None
    except Exception:
        return False


def is_same_condition_passed(posting: dict, user_id: str, db_path: Path = _DEFAULT_DB_PATH) -> bool:
    """동일 조건(회사+직무)으로 이미 패스한 기록이 있는지 확인한다 (M11)."""
    try:
        company = posting.get("company", "")
        job_role = posting.get("job_role", "")
        if not company and not job_role:
            return False
        conn = get_connection(db_path)
        row = conn.execute(
            "SELECT 1 FROM pass_records WHERE user_id = ? AND company = ? AND job_role = ? AND is_active = 1",
            (user_id, company, job_role),
        ).fetchone()
        return row is not None
    except Exception:
        return False


def record_pass(posting: dict, user_id: str, reason: str = "", db_path: Path = _DEFAULT_DB_PATH) -> dict:
    """공고를 패스 처리하고 DB에 기록한다."""
    try:
        now = datetime.now(timezone.utc).isoformat()
        conn = get_connection(db_path)
        conn.execute(
            """INSERT OR REPLACE INTO pass_records
               (user_id, job_url, company, job_role, reason, passed_at, is_active)
               VALUES (?, ?, ?, ?, ?, ?, 1)""",
            (
                user_id,
                posting.get("url", ""),
                posting.get("company", ""),
                posting.get("job_role", ""),
                reason,
                now,
            ),
        )
        conn.commit()
        return {"결과": "성공", "job_url": posting.get("url")}
    except Exception as e:
        return {"결과": "실패", "이유": str(e)}


def reset_pass(user_id: str, db_path: Path = _DEFAULT_DB_PATH) -> dict:
    """이직 후 패스 기록을 초기화한다 (is_active=0으로 소프트 삭제)."""
    try:
        conn = get_connection(db_path)
        conn.execute(
            "UPDATE pass_records SET is_active = 0 WHERE user_id = ?",
            (user_id,),
        )
        conn.commit()
        return {"결과": "성공"}
    except Exception as e:
        return {"결과": "실패", "이유": str(e)}


def apply_pass_filter(postings: list[dict], user_id: str, db_path: Path = _DEFAULT_DB_PATH) -> dict:
    """패스 및 동일조건 반복 차단 필터를 적용한다.

    반환: {"결과": "성공", "passed": list[dict], "pass_recorded": int}
    """
    try:
        result: list[dict] = []
        pass_recorded = 0
        for p in postings:
            if is_passed(p, user_id, db_path):
                pass_recorded += 1
                continue
            if is_same_condition_passed(p, user_id, db_path):
                pass_recorded += 1
                continue
            result.append(p)
        return {"결과": "성공", "passed": result, "pass_recorded": pass_recorded}
    except Exception as e:
        return {"결과": "실패", "이유": str(e)}
