# interface version: 1.0
from __future__ import annotations
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


def extract_persona(files: list[Path], user_id: str) -> dict:
    """문서 파일 목록에서 페르소나 11섹션을 추출해 DB에 저장한다."""
    try:
        raise NotImplementedError
    except NotImplementedError:
        raise
    except Exception as e:
        return {"결과": "실패", "이유": str(e)}


def update_persona(user_id: str, diff: dict) -> dict:
    """페르소나 특정 섹션을 수정하고 changelog에 기록한다."""
    try:
        raise NotImplementedError
    except NotImplementedError:
        raise
    except Exception as e:
        return {"결과": "실패", "이유": str(e)}


def get_persona(user_id: str) -> dict:
    """현재 페르소나를 조회한다."""
    try:
        raise NotImplementedError
    except NotImplementedError:
        raise
    except Exception as e:
        return {"결과": "실패", "이유": str(e)}
