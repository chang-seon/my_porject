"""지원 링크 처리 — v1: 링크 전달 (직접 브라우저 열기는 v1.1)."""
from __future__ import annotations


def get_apply_link(job_posting: dict) -> dict:
    """공고에서 지원 링크를 추출하거나 생성한다."""
    try:
        url = job_posting.get("url") or job_posting.get("apply_url") or ""
        if not url:
            return {"결과": "실패", "이유": "공고에 지원 링크가 없습니다."}
        return {"결과": "성공", "apply_url": url, "company": job_posting.get("company", "")}
    except Exception as e:
        return {"결과": "실패", "이유": str(e)}


def format_apply_message(job_posting: dict, draft_id: str = "") -> dict:
    """지원 안내 메시지를 생성한다 (텔레그램 알림용)."""
    try:
        company = job_posting.get("company", "미상")
        title = job_posting.get("title", "미상")
        url = job_posting.get("url") or job_posting.get("apply_url") or "(링크 없음)"
        lines = [
            f"📋 지원 준비 완료",
            f"• 회사: {company}",
            f"• 직무: {title}",
            f"• 링크: {url}",
        ]
        if draft_id:
            lines.append(f"• 자소서 ID: {draft_id}")
        return {"결과": "성공", "message": "\n".join(lines)}
    except Exception as e:
        return {"결과": "실패", "이유": str(e)}


def validate_url(url: str) -> dict:
    """지원 URL의 기본 유효성을 검사한다."""
    try:
        if not url:
            return {"결과": "실패", "이유": "URL이 비어있습니다."}
        if not (url.startswith("http://") or url.startswith("https://")):
            return {"결과": "실패", "이유": "유효하지 않은 URL 형식입니다."}
        return {"결과": "성공", "url": url, "valid": True}
    except Exception as e:
        return {"결과": "실패", "이유": str(e)}
