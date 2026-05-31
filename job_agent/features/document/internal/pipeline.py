"""자소서 생성 → 검증 → 재시도 → HITL2 통합 파이프라인."""
from __future__ import annotations

from pathlib import Path

from job_agent.features.document.internal.pool_loader import load_content_pool
from job_agent.features.document.internal.synthesizer import synthesize
from job_agent.features.validator.internal.retry_loop import validate_with_retry
from job_agent.shared.db.connection import get_connection, init_db

_DEFAULT_DB_PATH = Path(__file__).parents[4] / "data" / "agent.db"


def generate_and_validate(
    job_posting: dict,
    user_id: str,
    db_path: Path | None = None,
    skip_llm: bool = False,
) -> dict:
    """공고 + 페르소나로 자소서를 생성하고 검증한다.

    흐름: pool_loader → synthesizer → validate_with_retry(Q3)
    검증 3회 실패 시 needs_hitl=True 반환.

    반환:
      draft_id: str
      content: str
      validation: dict (passed, attempts, needs_hitl, history)
      token_used: int
    """
    try:
        _db = db_path or _DEFAULT_DB_PATH
        init_db(_db)

        pool_result = load_content_pool(user_id, db_path=_db)
        if pool_result["결과"] == "실패":
            return pool_result

        content_pool = pool_result["content_pool"]
        style_markers = pool_result["style_markers"]
        anti_patterns = pool_result["anti_patterns"]
        persona_summary = pool_result["persona_summary"]

        synth_result = synthesize(job_posting, content_pool, style_markers, anti_patterns)
        if synth_result["결과"] == "실패":
            return synth_result

        content = synth_result["content"]
        draft_id = synth_result["draft_id"]
        token_used = synth_result.get("token_used", 0)

        def regenerate(current_content: str, attempt: int) -> str:
            r = synthesize(job_posting, content_pool, style_markers, anti_patterns)
            return r.get("content", current_content) if r.get("결과") == "성공" else current_content

        validation = validate_with_retry(
            content=content,
            persona_summary=persona_summary,
            skip_llm=skip_llm,
            generate_fn=regenerate,
        )

        _save_draft(draft_id, user_id, content, job_posting, validation, _db)

        return {
            "결과": "성공",
            "draft_id": draft_id,
            "content": content,
            "validation": validation,
            "token_used": token_used,
        }
    except Exception as e:
        return {"결과": "실패", "이유": str(e)}


def get_draft(draft_id: str, db_path: Path | None = None) -> dict:
    """저장된 자소서 초안을 조회한다."""
    try:
        _db = db_path or _DEFAULT_DB_PATH
        conn = get_connection(_db)
        try:
            row = conn.execute(
                "SELECT * FROM event_logs WHERE event_type='draft_saved' AND json_extract(event_data,'$.draft_id')=?",
                (draft_id,),
            ).fetchone()
        finally:
            conn.close()

        if row is None:
            return {"결과": "실패", "이유": f"초안 없음: draft_id={draft_id}"}
        import json
        data = json.loads(row["event_data"])
        return {"결과": "성공", "draft_id": draft_id, "content": data.get("content", ""), "data": data}
    except Exception as e:
        return {"결과": "실패", "이유": str(e)}


def update_draft(draft_id: str, content: str, reason: str, user_id: str = "", db_path: Path | None = None) -> dict:
    """사용자가 수정한 자소서를 저장한다."""
    try:
        import json, hashlib, datetime
        _db = db_path or _DEFAULT_DB_PATH
        new_draft_id = hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]
        conn = get_connection(_db)
        try:
            conn.execute(
                "INSERT INTO event_logs(user_id, event_type, event_data, year, month, day) VALUES(?,?,?,?,?,?)",
                (
                    user_id,
                    "draft_updated",
                    json.dumps({"draft_id": new_draft_id, "prev_draft_id": draft_id, "content": content, "reason": reason}, ensure_ascii=False),
                    *_today_ymd(),
                ),
            )
            conn.commit()
        finally:
            conn.close()
        return {"결과": "성공", "draft_id": new_draft_id, "prev_draft_id": draft_id}
    except Exception as e:
        return {"결과": "실패", "이유": str(e)}


def _save_draft(draft_id, user_id, content, job_posting, validation, db_path):
    """자소서 초안을 event_logs에 저장한다."""
    import json
    conn = get_connection(db_path)
    try:
        conn.execute(
            "INSERT INTO event_logs(user_id, event_type, event_data, year, month, day) VALUES(?,?,?,?,?,?)",
            (
                user_id,
                "draft_saved",
                json.dumps({
                    "draft_id": draft_id,
                    "content": content,
                    "company": job_posting.get("company", ""),
                    "job_title": job_posting.get("title", ""),
                    "validation_passed": validation.get("passed", False),
                    "needs_hitl": validation.get("needs_hitl", False),
                }, ensure_ascii=False),
                *_today_ymd(),
            ),
        )
        conn.commit()
    finally:
        conn.close()


def _today_ymd():
    from datetime import date
    d = date.today()
    return d.year, d.month, d.day
