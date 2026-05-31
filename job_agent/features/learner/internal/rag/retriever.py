"""RAG 리트리버 — 쿼리 텍스트로 관련 지식 검색."""
from __future__ import annotations

from pathlib import Path

from job_agent.features.learner.internal.rag.embedder import embed
from job_agent.features.learner.internal.rag.vector_store import search_similar

_DEFAULT_DB_PATH = Path(__file__).parents[5] / "data" / "agent.db"


def retrieve(
    query: str,
    top_k: int = 5,
    domain: str | None = None,
    min_score: float = 0.1,
    db_path: Path | None = None,
) -> dict:
    """쿼리와 유사한 지식을 검색한다.

    반환:
      results: [{"id": int, "content": str, "score": float, "domain": str}, ...]
      total: 반환된 결과 수
    """
    try:
        _db = db_path or _DEFAULT_DB_PATH
        if not query.strip():
            return {"결과": "실패", "이유": "빈 쿼리는 검색할 수 없습니다."}
        query_emb = embed(query)
        result = search_similar(query_emb, top_k=top_k, domain=domain, db_path=_db)
        if result["결과"] == "실패":
            return result
        filtered = [r for r in result["results"] if r["score"] >= min_score]
        return {"결과": "성공", "results": filtered, "total": len(filtered)}
    except Exception as e:
        return {"결과": "실패", "이유": str(e)}


def retrieve_company_info(company: str, top_k: int = 3, db_path: Path | None = None) -> dict:
    """특정 회사의 평판·평점 정보를 검색한다."""
    return retrieve(company, top_k=top_k, domain="company_review", db_path=db_path)


def retrieve_interview_questions(company: str, job_role: str = "", top_k: int = 5, db_path: Path | None = None) -> dict:
    """회사·직무 관련 면접 기출 질문을 검색한다."""
    query = f"{company} {job_role}".strip()
    return retrieve(query, top_k=top_k, domain="interview_question", db_path=db_path)
