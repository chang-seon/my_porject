"""자동화 전환 로직 — 검증AI N회 연속 OK → 자동화 단계 상승 (#30·#37·M4)."""
from __future__ import annotations

import json
from pathlib import Path

from job_agent.features.learner.internal.dynamic_threshold import get_threshold, update_threshold
from job_agent.shared.db.connection import get_connection, init_db

_DEFAULT_DB_PATH = Path(__file__).parents[4] / "data" / "agent.db"

_AUTOMATION_LEVELS = {
    0: "수동 HITL",
    1: "검증 통과 후 자동 전송",
    2: "검증 없이 자동 전송",
    3: "완전 자동화",
}


def check_promotion(user_id: str, db_path: Path | None = None) -> dict:
    """최근 N회 검증 결과를 확인하고 자동화 단계 상승 여부를 판단한다.

    N 기준: dynamic_thresholds의 automation_promotion_n (기본값: 5, M4 결정)

    반환:
      current_level: 현재 자동화 수준
      promoted: 상승 여부
      new_level: 상승 후 수준 (promoted=True일 때)
      consecutive_ok: 연속 통과 횟수
    """
    try:
        _db = db_path or _DEFAULT_DB_PATH
        init_db(_db)

        n_result = get_threshold("automation", "promotion_n", user_id, db_path=_db)
        n = int(n_result["value"]) if n_result["결과"] == "성공" else 5

        level_result = get_threshold("automation", "current_level", user_id, db_path=_db)
        current_level = int(level_result["value"]) if level_result["결과"] == "성공" else 0

        if current_level >= max(_AUTOMATION_LEVELS.keys()):
            return {
                "결과": "성공",
                "current_level": current_level,
                "promoted": False,
                "consecutive_ok": 0,
                "message": "이미 최고 자동화 단계입니다.",
            }

        consecutive_ok = _count_consecutive_ok(user_id, _db)

        promoted = consecutive_ok >= n
        new_level = current_level + 1 if promoted else current_level

        if promoted:
            update_threshold("automation", "current_level", new_level, user_id, db_path=_db)
            _record_promotion_signal(user_id, current_level, new_level, consecutive_ok, _db)

        return {
            "결과": "성공",
            "current_level": current_level,
            "promoted": promoted,
            "new_level": new_level,
            "consecutive_ok": consecutive_ok,
            "level_name": _AUTOMATION_LEVELS.get(new_level, "알 수 없음"),
            "threshold_n": n,
        }
    except Exception as e:
        return {"결과": "실패", "이유": str(e)}


def get_automation_level(user_id: str, db_path: Path | None = None) -> dict:
    """현재 사용자의 자동화 수준을 조회한다."""
    try:
        _db = db_path or _DEFAULT_DB_PATH
        level_result = get_threshold("automation", "current_level", user_id, db_path=_db)
        level = int(level_result["value"]) if level_result["결과"] == "성공" else 0
        return {
            "결과": "성공",
            "level": level,
            "level_name": _AUTOMATION_LEVELS.get(level, "알 수 없음"),
        }
    except Exception as e:
        return {"결과": "실패", "이유": str(e)}


def reset_automation_level(user_id: str, db_path: Path | None = None) -> dict:
    """자동화 수준을 0(수동 HITL)으로 초기화한다."""
    try:
        _db = db_path or _DEFAULT_DB_PATH
        update_threshold("automation", "current_level", 0, user_id, db_path=_db)
        return {"결과": "성공", "level": 0, "level_name": _AUTOMATION_LEVELS[0]}
    except Exception as e:
        return {"결과": "실패", "이유": str(e)}


def _count_consecutive_ok(user_id: str, db_path: Path) -> int:
    """최근 검증 결과 중 연속으로 통과한 횟수를 센다."""
    conn = get_connection(db_path)
    try:
        rows = conn.execute(
            "SELECT payload FROM learning_signals "
            "WHERE user_id=? AND layer='B' AND signal_type='validation_result' "
            "ORDER BY id DESC LIMIT 20",
            (user_id,),
        ).fetchall()
    finally:
        conn.close()

    count = 0
    for row in rows:
        try:
            data = json.loads(row["payload"])
            if data.get("passed"):
                count += 1
            else:
                break
        except (json.JSONDecodeError, KeyError):
            break
    return count


def _record_promotion_signal(user_id, old_level, new_level, consecutive_ok, db_path):
    """자동화 상승 학습신호를 B층에 기록한다."""
    conn = get_connection(db_path)
    from datetime import date
    d = date.today()
    try:
        conn.execute(
            "INSERT INTO learning_signals(user_id, layer, signal_type, payload, year, month, day) VALUES(?,?,?,?,?,?,?)",
            (
                user_id,
                "B",
                "automation_promoted",
                json.dumps({
                    "old_level": old_level,
                    "new_level": new_level,
                    "consecutive_ok": consecutive_ok,
                }, ensure_ascii=False),
                d.year, d.month, d.day,
            ),
        )
        conn.commit()
    finally:
        conn.close()


def record_validation_signal(user_id: str, passed: bool, draft_id: str = "", db_path: Path | None = None) -> dict:
    """검증 결과를 학습신호 B층에 기록한다 (auto_promotion 평가용)."""
    try:
        import json
        from datetime import date
        _db = db_path or _DEFAULT_DB_PATH
        d = date.today()
        conn = get_connection(_db)
        try:
            conn.execute(
                "INSERT INTO learning_signals(user_id, layer, signal_type, payload, year, month, day) VALUES(?,?,?,?,?,?,?)",
                (
                    user_id,
                    "B",
                    "validation_result",
                    json.dumps({"passed": passed, "draft_id": draft_id}, ensure_ascii=False),
                    d.year, d.month, d.day,
                ),
            )
            conn.commit()
        finally:
            conn.close()
        return {"결과": "성공", "passed": passed}
    except Exception as e:
        return {"결과": "실패", "이유": str(e)}
