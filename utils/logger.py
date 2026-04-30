"""
logger.py: 콘솔 로깅 설정 모듈.

LOG_LEVEL 환경변수로 레벨을 조정한다. (기본: INFO)
"""
from __future__ import annotations

import logging
import os


def setup_logging() -> None:
    """애플리케이션 전역 로깅 설정."""
    level_str = os.environ.get("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_str, logging.INFO)

    logging.basicConfig(
        level=level,
        format="[%(asctime)s] %(levelname)s %(name)s — %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
