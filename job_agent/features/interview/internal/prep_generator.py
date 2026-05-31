"""면접 준비 자료 생성 — RAG 기출 + Claude 모의 질문."""
from __future__ import annotations

from pathlib import Path

from job_agent.features.learner.internal.rag.retriever import (
    retrieve_company_info,
    retrieve_interview_questions,
)
from job_agent.shared.llm.router import LLMRouter

_DEFAULT_DB_PATH = Path(__file__).parents[4] / "data" / "agent.db"
_router: LLMRouter | None = None


def _get_router() -> LLMRouter:
    global _router
    if _router is None:
        _router = LLMRouter()
    return _router


def generate_prep(
    job_posting: dict,
    persona_summary: str = "",
    db_path: Path | None = None,
    skip_llm: bool = False,
) -> dict:
    """면접 준비 자료를 생성한다.

    흐름: RAG 기출 검색 → LLM 모의 질문 생성 → 회사 정보 취합
    반환:
      questions: 예상 질문 목록
      tips: 준비 팁 목록
      company_info: RAG 회사 정보 요약
    """
    try:
        _db = db_path or _DEFAULT_DB_PATH
        company = job_posting.get("company", "")
        job_role = job_posting.get("title", job_posting.get("job_role", ""))

        company_result = retrieve_company_info(company, top_k=3, db_path=_db)
        company_items = company_result.get("results", []) if company_result["결과"] == "성공" else []

        rag_result = retrieve_interview_questions(company, job_role, top_k=5, db_path=_db)
        rag_questions = [r["content"] for r in rag_result.get("results", [])] if rag_result["결과"] == "성공" else []

        if skip_llm:
            questions = rag_questions or _default_questions(job_role)
            tips = _default_tips()
        else:
            llm_result = _generate_with_llm(job_posting, rag_questions, persona_summary, company_items)
            questions = llm_result.get("questions", rag_questions or _default_questions(job_role))
            tips = llm_result.get("tips", _default_tips())

        return {
            "결과": "성공",
            "questions": questions,
            "tips": tips,
            "company_info": {
                "company": company,
                "reputation_items": [c["content"] for c in company_items],
            },
        }
    except Exception as e:
        return {"결과": "실패", "이유": str(e)}


def _generate_with_llm(
    job_posting: dict,
    rag_questions: list[str],
    persona_summary: str,
    company_items: list[dict],
) -> dict:
    try:
        company = job_posting.get("company", "")
        role = job_posting.get("title", "")
        rag_text = "\n".join(f"- {q}" for q in rag_questions) if rag_questions else "(없음)"
        company_text = "\n".join(f"- {c['content']}" for c in company_items) if company_items else "(없음)"

        prompt = f"""당신은 {role} 면접 코치입니다.

회사: {company}
직무: {role}
지원자 요약: {persona_summary or '(없음)'}
RAG 기출 질문: {rag_text}
회사 평판: {company_text}

위 정보를 바탕으로 예상 면접 질문 5개와 준비 팁 3개를 생성하세요.

출력 형식:
QUESTIONS:
1. ...
2. ...
...

TIPS:
1. ...
2. ...
"""
        response = _get_router().generate(prompt, task_type="generate_document")
        if response.get("결과") == "실패":
            return {}
        return _parse_prep_response(response.get("text", ""))
    except Exception:
        return {}


def _parse_prep_response(text: str) -> dict:
    questions, tips = [], []
    mode = None
    for line in text.splitlines():
        line = line.strip()
        if line.upper().startswith("QUESTIONS"):
            mode = "q"
        elif line.upper().startswith("TIPS"):
            mode = "t"
        elif line and line[0].isdigit() and ". " in line:
            content = line.split(". ", 1)[1].strip()
            if mode == "q":
                questions.append(content)
            elif mode == "t":
                tips.append(content)
    return {"questions": questions, "tips": tips}


def _default_questions(job_role: str) -> list[str]:
    return [
        f"{job_role} 직무를 선택한 이유는 무엇인가요?",
        "본인의 강점과 약점을 말씀해주세요.",
        "가장 도전적이었던 프로젝트 경험을 공유해주세요.",
        "5년 후 목표는 무엇인가요?",
        "팀 내 갈등 상황을 어떻게 해결하셨나요?",
    ]


def _default_tips() -> list[str]:
    return [
        "STAR 방식(상황-과제-행동-결과)으로 답변을 준비하세요.",
        "회사의 최근 뉴스와 사업 방향을 미리 파악하세요.",
        "기술 질문은 경험 기반으로 구체적 수치를 포함해 답변하세요.",
    ]
