# interface version: 1.0
from __future__ import annotations
from typing import Any


def record_signal(signal: dict) -> dict:
    """학습신호 A~E층을 DB에 기록한다.

    signal: LearningSignal.model_dump() 형태의 dict
    반환: {"결과": "성공", "signal_id": int}
    """
    try:
        raise NotImplementedError
    except NotImplementedError:
        raise
    except Exception as e:
        return {"결과": "실패", "이유": str(e)}


def get_dynamic_threshold(domain: str, context_key: str, user_id: str) -> dict:
    """동적 기준값을 조회한다. 없으면 기본값을 반환한다. (#37)

    반환: {"결과": "성공", "value": Any, "source": "db"|"default"}
    """
    try:
        raise NotImplementedError
    except NotImplementedError:
        raise
    except Exception as e:
        return {"결과": "실패", "이유": str(e)}


def update_dynamic_threshold(domain: str, context_key: str, value: Any, user_id: str) -> dict:
    """동적 기준값을 갱신하고 변경 이력을 기록한다. (#37)"""
    try:
        raise NotImplementedError
    except NotImplementedError:
        raise
    except Exception as e:
        return {"결과": "실패", "이유": str(e)}
