# interface version: 1.0
from __future__ import annotations


def notify(message: dict) -> dict:
    """텔레그램으로 알림을 발송한다.

    message 필드: type("공고알림"|"자소서검토"|"HITL요청"), content, metadata
    반환: {"결과": "성공", "message_id": str}
    """
    try:
        raise NotImplementedError
    except NotImplementedError:
        raise
    except Exception as e:
        return {"결과": "실패", "이유": str(e)}


def notify_hitl(request_id: str, question: str, options: list[str]) -> dict:
    """HITL 결정 요청 알림을 발송하고 응답을 대기한다."""
    try:
        raise NotImplementedError
    except NotImplementedError:
        raise
    except Exception as e:
        return {"결과": "실패", "이유": str(e)}
