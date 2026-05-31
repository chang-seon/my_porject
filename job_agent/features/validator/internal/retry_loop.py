"""검증 재시도 루프 — Q3 결정사항: 3회 재시도 후 사용자 HITL."""
from __future__ import annotations

from job_agent.features.validator.internal.rule_engine import validate_cover_letter
from job_agent.features.validator.internal.llm_judge import judge_cover_letter

_MAX_RETRIES = 3


def validate_with_retry(
    content: str,
    persona_summary: str = "",
    skip_llm: bool = False,
    generate_fn=None,
) -> dict:
    """1차 룰 + 2차 LLM 검증을 최대 3회 재시도한다.

    통과 못하면 HITL 요청 필요 상태를 반환한다.

    Args:
      content: 검증할 자소서 텍스트
      persona_summary: 페르소나 요약 (LLM 사실 대조용)
      skip_llm: True이면 2차 LLM 검증 건너뜀 (테스트 용도)
      generate_fn: 재시도 시 새 버전 생성 함수 fn(content, attempt) -> str

    반환:
      passed: bool
      attempts: int
      needs_hitl: bool (3회 실패 시 True)
      last_result: 마지막 검증 결과
      history: 시도별 결과 목록
    """
    try:
        history: list[dict] = []
        current = content

        for attempt in range(1, _MAX_RETRIES + 1):
            step1 = validate_cover_letter(current)

            if step1.get("결과") == "실패":
                return {"결과": "실패", "이유": step1.get("이유", "")}

            if not step1["passed"]:
                history.append({"attempt": attempt, "stage": "1차", "passed": False, "result": step1})
                if generate_fn and attempt < _MAX_RETRIES:
                    current = generate_fn(current, attempt)
                continue

            if skip_llm:
                history.append({"attempt": attempt, "stage": "1차-통과", "passed": True, "result": step1})
                return {
                    "결과": "성공",
                    "passed": True,
                    "attempts": attempt,
                    "needs_hitl": False,
                    "last_result": step1,
                    "history": history,
                }

            step2 = judge_cover_letter(current, persona_summary)
            if step2.get("결과") == "실패":
                history.append({"attempt": attempt, "stage": "2차-오류", "passed": False, "result": step2})
                if generate_fn and attempt < _MAX_RETRIES:
                    current = generate_fn(current, attempt)
                continue

            history.append({"attempt": attempt, "stage": "2차", "passed": step2["passed"], "result": step2})

            if step2["passed"]:
                return {
                    "결과": "성공",
                    "passed": True,
                    "attempts": attempt,
                    "needs_hitl": False,
                    "last_result": step2,
                    "history": history,
                }

            if generate_fn and attempt < _MAX_RETRIES:
                current = generate_fn(current, attempt)

        return {
            "결과": "성공",
            "passed": False,
            "attempts": _MAX_RETRIES,
            "needs_hitl": True,
            "last_result": history[-1]["result"] if history else {},
            "history": history,
        }
    except Exception as e:
        return {"결과": "실패", "이유": str(e)}
