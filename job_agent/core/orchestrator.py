# 보호 컴포넌트 — 수정 시 사용자 승인 필수 (CLAUDE.md 참조)
from __future__ import annotations
from pathlib import Path

from job_agent.core import router


def run_setup(user_id: str, files: list) -> dict:
    """① 셋업 — 파일 → 텍스트 → 페르소나 추출 → DB 저장 → 알림"""
    try:
        from job_agent.features.persona.internal.extractor import extract_texts_from_files
        from job_agent.features.persona.internal.llm_extract import extract_persona_from_text
        from job_agent.features.persona.internal.storage import save_persona
        from job_agent.shared.schemas.persona import Persona

        # 파일 텍스트 추출
        paths = [Path(f) for f in files]
        extract_result = extract_texts_from_files(paths)
        if extract_result["결과"] == "실패":
            return extract_result

        # LLM 페르소나 추출
        extract_persona_result = extract_persona_from_text(
            extract_result["combined_text"], user_id
        )
        if extract_persona_result["결과"] == "실패":
            return extract_persona_result

        # DB 저장
        persona = Persona(**extract_persona_result["persona"])
        save_result = save_persona(persona)
        if save_result["결과"] == "실패":
            return save_result

        # 알림
        router.call("notification", "notify", message={
            "type": "HITL요청",
            "content": f"페르소나 초기 설정이 완료됐습니다. 확인해주세요.",
            "metadata": {"user_id": user_id},
        })

        return {"결과": "성공", "user_id": user_id, "name": persona.name}
    except Exception as e:
        return {"결과": "실패", "이유": str(e)}


def fetch_and_filter(user_id: str) -> dict:
    """② 공고 수집 + ③ 필터링"""
    try:
        fetch = router.call("job_search", "fetch_postings", query={
            "job_role": None, "location": None, "employment_type": None,
        })
        if fetch["결과"] == "실패":
            return fetch
        filtered = router.call("job_search", "filter_postings",
                               postings=fetch.get("postings", []), user_id=user_id)
        return filtered
    except Exception as e:
        return {"결과": "실패", "이유": str(e)}


def generate_and_validate(user_id: str, job_id: str, job_posting: dict | None = None) -> dict:
    """④ 자소서 생성 + ⑤ 검증AI (생성→검증→최대 3회 재시도)"""
    try:
        gen = router.call(
            "document", "generate_cover_letter",
            job_id=job_id, user_id=user_id,
            job_posting=job_posting or {"job_id": job_id},
        )
        if gen["결과"] == "실패":
            return gen

        validation = gen.get("validation", {})
        if validation.get("needs_hitl"):
            router.call("notification", "notify", message={
                "type": "HITL요청",
                "content": f"자소서 검증 3회 실패 — 직접 검토 필요 (draft_id={gen.get('draft_id')})",
                "metadata": {"user_id": user_id, "draft_id": gen.get("draft_id")},
            })

        return {
            "결과": "성공",
            "draft_id": gen.get("draft_id"),
            "content": gen.get("content"),
            "validation": validation,
        }
    except Exception as e:
        return {"결과": "실패", "이유": str(e)}


def hitl_review(user_id: str, draft_id: str) -> dict:
    """⑥ HITL 1 — 자소서 검토 요청 (hitl_bus에 요청 등록 + 텔레그램 알림)"""
    try:
        from job_agent.core import hitl_bus
        request_result = hitl_bus.request_hitl(
            request_id=draft_id,
            user_id=user_id,
            question="자소서를 검토해주세요.",
            options=["승인", "수정", "폐기"],
        )
        router.call("notification", "notify", message={
            "type": "HITL요청",
            "content": f"자소서 검토를 요청드립니다. (draft_id={draft_id})\n옵션: 승인 / 수정 / 폐기",
            "metadata": {"user_id": user_id, "draft_id": draft_id},
        })
        return {"결과": "성공", "request_id": draft_id, "hitl": request_result}
    except Exception as e:
        return {"결과": "실패", "이유": str(e)}


def submit_application(user_id: str, draft_id: str, job_id: str, job_posting: dict | None = None) -> dict:
    """⑦ 지원 실행 — 지원 기록 저장 + 링크 전달 알림"""
    try:
        result = router.call(
            "application", "record_application",
            job_id=job_id, user_id=user_id, draft_id=draft_id,
            job_posting=job_posting,
        )
        if result["결과"] == "성공":
            router.call("notification", "notify", message={
                "type": "지원알림",
                "content": f"지원 완료: {(job_posting or {}).get('company', job_id)}\n링크: {result.get('apply_url', '-')}",
                "metadata": {"user_id": user_id, "application_id": result.get("application_id")},
            })
        return result
    except Exception as e:
        return {"결과": "실패", "이유": str(e)}


def track_result(user_id: str, application_id: str, status: str, result: str | None = None) -> dict:
    """⑧ 결과 추적 — 상태 갱신 + 학습신호 E층 기록"""
    try:
        return router.call(
            "application", "update_application_status",
            application_id=application_id, status=status,
            user_id=user_id, result=result,
        )
    except Exception as e:
        return {"결과": "실패", "이유": str(e)}


def handle_pass(user_id: str, job_id: str, reason: str) -> dict:
    """⑨ 패스 처리"""
    try:
        return router.call("job_search", "filter_postings",
                           postings=[], user_id=user_id)
    except Exception as e:
        return {"결과": "실패", "이유": str(e)}


def prepare_interview(user_id: str, application_id: str) -> dict:
    """⑩ 면접 준비"""
    try:
        return router.call("interview", "prepare", job_id=application_id, user_id=user_id)
    except Exception as e:
        return {"결과": "실패", "이유": str(e)}


def debrief_interview(user_id: str, application_id: str, feedback: str) -> dict:
    """⑪ 면접 회고"""
    try:
        return router.call("interview", "debrief",
                           application_id=application_id, feedback=feedback, user_id=user_id)
    except Exception as e:
        return {"결과": "실패", "이유": str(e)}


def run_daily_cycle(user_id: str) -> dict:
    """일일 반복 사이클 ②~⑨ 자동 실행"""
    try:
        result = fetch_and_filter(user_id)
        return {"결과": "성공", "cycle": "daily", "filter_result": result}
    except Exception as e:
        return {"결과": "실패", "이유": str(e)}
