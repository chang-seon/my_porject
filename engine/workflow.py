"""
workflow.py: 워크플로우 진입 도우미.

Orchestrator를 구성하고 실행하는 팩토리 함수를 제공한다.
main.py에서 직접 사용하며, 환경 초기화 및 의존성 주입을 담당한다.
"""
from __future__ import annotations

import logging
import os
from pathlib import Path

from dotenv import load_dotenv

logger = logging.getLogger(__name__)


def load_env() -> None:
    """
    config/.env 파일에서 환경변수를 로드한다.
    GEMINI_API_KEY, DISCORD_WEBHOOK_URL 등이 여기서 설정된다.
    """
    env_path = Path("config/.env")
    load_dotenv(dotenv_path=env_path if env_path.exists() else Path(".env"))
    logger.info("환경변수 로드 완료")


def build_orchestrator():
    """
    GeminiEngine → Director → DiscordReporter → Orchestrator 순서로
    의존성을 조립하여 실행 준비된 Orchestrator를 반환한다.

    출력: Orchestrator 인스턴스
    오류: EnvironmentError — GEMINI_API_KEY 미설정 시
    """
    from agents.engine import GeminiEngine
    from agents.director import Director
    from engine.orchestrator import Orchestrator
    from utils.discord import DiscordReporter

    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "GEMINI_API_KEY가 설정되지 않았습니다. config/.env를 확인하세요."
        )

    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL", "")
    if not webhook_url:
        logger.warning("DISCORD_WEBHOOK_URL 미설정 — Discord 알림 비활성화")

    engine = GeminiEngine(api_key=api_key)
    director = Director(engine=engine)
    discord = DiscordReporter(webhook_url=webhook_url)
    return Orchestrator(engine=engine, director=director, discord=discord)


async def run_mission(mission: str) -> str:
    """
    미션 문자열을 받아 전체 워크플로우를 실행하고 최종 결과물을 반환.

    입력: mission — 창선님이 하달한 업무
    출력: 최종 결과물 텍스트
    """
    orchestrator = build_orchestrator()
    return await orchestrator.run(mission)
