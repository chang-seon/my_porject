"""면접 회고 기록 — 학습신호 B·C층 적재."""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from job_agent.shared.db.connection import get_connection, init_db
from job_agent.features.learner.internal.rag.ingest import ingest_text

_DEFAULT_DB_PATH = Path(__file__).parents[4] / "data" / "agent.db"


def record_debrief(
    application_id: str,
    feedback: str,
    user_id: str,
    questions: list[str] | None = None,
    result: str = "",
    db_path: Path | None = None,
) -> dict:
    """면접 회고를 기록하고 학습신호를 적재한다.

    B층: 면접 질문·회고 내용 (도메인 지식 누적)
    C층: 피드백 기반 개선 신호

    반환:
      signals_recorded: 적재된 학습신호 수
      rag_ingested: RAG에 저장된 항목 수
    """
    try:
        _db = db_path or _DEFAULT_DB_PATH
        init_db(_db)
        d = date.today()
        signals_recorded = 0
        rag_ingested = 0

        conn = get_connection(_db)
        try:
            # C층: 회고 피드백 학습신호
            conn.execute(
                "INSERT INTO learning_signals(user_id, layer, signal_type, payload, year, month, day) VALUES(?,?,?,?,?,?,?)",
                (
                    user_id,
                    "C",
                    "interview_debrief",
                    json.dumps({
                        "application_id": application_id,
                        "feedback": feedback,
                        "result": result,
                    }, ensure_ascii=False),
                    d.year, d.month, d.day,
                ),
            )
            signals_recorded += 1

            # B층: 면접 질문이 있으면 지식으로 누적
            if questions:
                for q in questions:
                    conn.execute(
                        "INSERT INTO learning_signals(user_id, layer, signal_type, payload, year, month, day) VALUES(?,?,?,?,?,?,?)",
                        (
                            user_id,
                            "B",
                            "interview_question_observed",
                            json.dumps({"application_id": application_id, "question": q}, ensure_ascii=False),
                            d.year, d.month, d.day,
                        ),
                    )
                    signals_recorded += 1

            # 최종 결과가 있으면 E층 적재
            if result in {"합격", "불합격", "최종합격"}:
                conn.execute(
                    "INSERT INTO learning_signals(user_id, layer, signal_type, payload, year, month, day) VALUES(?,?,?,?,?,?,?)",
                    (
                        user_id,
                        "E",
                        f"interview_{result}",
                        json.dumps({"application_id": application_id}, ensure_ascii=False),
                        d.year, d.month, d.day,
                    ),
                )
                signals_recorded += 1

            conn.commit()
        finally:
            conn.close()

        # 면접 질문을 RAG에 도메인 지식으로 저장 (#36 RAG 메타학습)
        if questions:
            for q in questions:
                r = ingest_text(q, source=application_id, domain="interview_question", db_path=_db)
                if r["결과"] == "성공":
                    rag_ingested += 1

        return {
            "결과": "성공",
            "signals_recorded": signals_recorded,
            "rag_ingested": rag_ingested,
        }
    except Exception as e:
        return {"결과": "실패", "이유": str(e)}


def get_debrief_history(user_id: str, db_path: Path | None = None) -> dict:
    """면접 회고 이력을 조회한다."""
    try:
        _db = db_path or _DEFAULT_DB_PATH
        conn = get_connection(_db)
        try:
            rows = conn.execute(
                "SELECT payload, year, month, day FROM learning_signals "
                "WHERE user_id=? AND layer='C' AND signal_type='interview_debrief' ORDER BY id DESC",
                (user_id,),
            ).fetchall()
        finally:
            conn.close()
        debriefs = []
        for row in rows:
            data = json.loads(row["payload"])
            data["date"] = f"{row['year']}-{row['month']:02d}-{row['day']:02d}"
            debriefs.append(data)
        return {"결과": "성공", "debriefs": debriefs, "total": len(debriefs)}
    except Exception as e:
        return {"결과": "실패", "이유": str(e)}
