"""RAG 인제스트 — 회사 평점컷·면접 기출 등 도메인 지식 적재."""
from __future__ import annotations

from pathlib import Path

from job_agent.features.learner.internal.rag.embedder import embed
from job_agent.features.learner.internal.rag.vector_store import save_knowledge

_DEFAULT_DB_PATH = Path(__file__).parents[5] / "data" / "agent.db"


def ingest_text(
    content: str,
    source: str = "",
    domain: str = "",
    db_path: Path | None = None,
) -> dict:
    """단일 텍스트를 임베딩하고 RAG 스토어에 저장한다."""
    try:
        if not content.strip():
            return {"결과": "실패", "이유": "빈 콘텐츠는 저장할 수 없습니다."}
        _db = db_path or _DEFAULT_DB_PATH
        embedding = embed(content)
        return save_knowledge(content, embedding, source=source, domain=domain, db_path=_db)
    except Exception as e:
        return {"결과": "실패", "이유": str(e)}


def ingest_batch(
    items: list[dict],
    db_path: Path | None = None,
) -> dict:
    """여러 지식 항목을 일괄 적재한다.

    items: [{"content": str, "source": str, "domain": str}, ...]
    """
    try:
        _db = db_path or _DEFAULT_DB_PATH
        success, failed = 0, 0
        errors = []
        for item in items:
            content = item.get("content", "")
            r = ingest_text(content, item.get("source", ""), item.get("domain", ""), db_path=_db)
            if r["결과"] == "성공":
                success += 1
            else:
                failed += 1
                errors.append(r["이유"])
        return {"결과": "성공", "total": len(items), "success": success, "failed": failed, "errors": errors}
    except Exception as e:
        return {"결과": "실패", "이유": str(e)}


def ingest_company_reviews(
    company: str,
    reviews: list[str],
    db_path: Path | None = None,
) -> dict:
    """회사 평판 리뷰를 RAG에 적재한다."""
    items = [{"content": r, "source": company, "domain": "company_review"} for r in reviews if r.strip()]
    return ingest_batch(items, db_path=db_path)


def ingest_interview_questions(
    company: str,
    questions: list[str],
    db_path: Path | None = None,
) -> dict:
    """면접 기출 질문을 RAG에 적재한다."""
    items = [{"content": q, "source": company, "domain": "interview_question"} for q in questions if q.strip()]
    return ingest_batch(items, db_path=db_path)
