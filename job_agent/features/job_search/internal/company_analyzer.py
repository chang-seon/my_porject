"""회사 분석 — RAG 평판 조회 + 패스 핸들러 연동."""
from __future__ import annotations

from pathlib import Path

from job_agent.features.learner.internal.rag.retriever import retrieve_company_info
from job_agent.features.job_search.internal.pass_handler import record_pass

_DEFAULT_DB_PATH = Path(__file__).parents[4] / "data" / "agent.db"


def analyze_company(
    posting: dict,
    user_id: str,
    min_reputation_score: float = 0.0,
    db_path: Path | None = None,
) -> dict:
    """RAG에서 회사 평판을 조회하고 패스 여부를 판단한다.

    반환:
      company: 회사명
      reputation_items: 평판 정보 목록
      should_pass: 평판이 기준 미달이면 True
      reason: 패스 사유 (should_pass=True일 때)
    """
    try:
        _db = db_path or _DEFAULT_DB_PATH
        company = posting.get("company", "")
        if not company:
            return {"결과": "실패", "이유": "공고에 회사명이 없습니다."}

        rep_result = retrieve_company_info(company, top_k=3, db_path=_db)
        if rep_result["결과"] == "실패":
            return {"결과": "성공", "company": company, "reputation_items": [], "should_pass": False, "reason": ""}

        reputation_items = rep_result["results"]
        negative_count = sum(1 for r in reputation_items if _is_negative(r["content"]))
        total = len(reputation_items)

        negative_ratio = negative_count / total if total > 0 else 0.0
        should_pass = negative_ratio > min_reputation_score and total > 0

        reason = ""
        if should_pass:
            reason = f"평판 분석: {total}건 중 {negative_count}건 부정 ({negative_ratio:.0%})"

        return {
            "결과": "성공",
            "company": company,
            "reputation_items": reputation_items,
            "should_pass": should_pass,
            "reason": reason,
            "negative_ratio": negative_ratio,
        }
    except Exception as e:
        return {"결과": "실패", "이유": str(e)}


def analyze_and_pass(
    postings: list[dict],
    user_id: str,
    negative_threshold: float = 0.7,
    db_path: Path | None = None,
) -> dict:
    """공고 목록에서 평판 기반 자동 패스를 처리한다.

    반환:
      accepted: 통과된 공고 목록
      auto_passed: 자동 패스된 공고 수
    """
    try:
        _db = db_path or _DEFAULT_DB_PATH
        accepted = []
        auto_passed = 0
        for posting in postings:
            analysis = analyze_company(posting, user_id, db_path=_db)
            if analysis.get("결과") == "성공" and analysis.get("should_pass"):
                record_pass(posting, user_id, reason=analysis.get("reason", "평판 기준 미달"), db_path=_db)
                auto_passed += 1
            else:
                accepted.append(posting)
        return {
            "결과": "성공",
            "accepted": accepted,
            "auto_passed": auto_passed,
            "total": len(postings),
        }
    except Exception as e:
        return {"결과": "실패", "이유": str(e)}


def _is_negative(text: str) -> bool:
    """평판 텍스트에 부정 키워드가 있는지 확인한다."""
    negative_keywords = ["야근", "갑질", "저연봉", "계약해지", "워라밸 최악", "퇴사율", "불만"]
    return any(kw in text for kw in negative_keywords)
