"""
Agentic AI v3 — 바톤 터치 멀티에이전트 사령부 진입점.

실행:
  venv/Scripts/python main.py --mission "이력서 작성해줘"
  venv/Scripts/python main.py --mission "기획서 작성" --no-interrupt
  venv/Scripts/python main.py --boot-report   # Discord 구축 완료 보고만 전송
"""
from __future__ import annotations

import argparse
import asyncio
import os
import sys


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Agentic AI v3 — 바톤 터치 멀티에이전트 사령부",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  venv/Scripts/python main.py --mission "파이썬 튜토리얼 작성"
  venv/Scripts/python main.py --mission "스타트업 IR 제안서" --no-interrupt
  venv/Scripts/python main.py --boot-report
        """,
    )
    p.add_argument("--mission", type=str, default=None,
                   help="수행할 미션 (미지정 시 대화형 입력)")
    p.add_argument("--no-interrupt", action="store_true",
                   help="골든 타임 인터럽트 비활성화 (완전 자동 모드)")
    p.add_argument("--boot-report", action="store_true",
                   help="Discord에 구축 완료 보고만 전송하고 종료")
    return p.parse_args()


async def send_boot_report() -> None:
    """Discord에 시스템 구축 완료 보고를 전송한다."""
    from engine.workflow import load_env
    from utils.discord import DiscordReporter

    load_env()
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL", "")
    if not webhook_url:
        print("[경고] DISCORD_WEBHOOK_URL 미설정 — config/.env를 확인하세요.")
        return

    reporter = DiscordReporter(webhook_url)
    try:
        await reporter.send_boot_report()
        print("[OK] Discord 구축 완료 보고 전송 성공")
    finally:
        await reporter.close()


async def run(mission: str, no_interrupt: bool) -> None:
    """전체 워크플로우를 실행한다."""
    from engine.workflow import load_env, run_mission
    import engine.orchestrator as _orch

    load_env()

    # 자동 모드: 골든 타임을 0.1초로 단축하여 인터럽트 없이 진행
    if no_interrupt:
        _orch.INTERRUPT_TIMEOUT = 0.1

    result = await run_mission(mission)
    print("\n" + "=" * 70)
    print(result)
    print("=" * 70)


def _interactive_mission() -> str:
    """터미널에서 미션을 직접 입력받는다."""
    print("\n" + "=" * 60)
    print("  Agentic AI v3 — 바톤 터치 멀티에이전트 사령부")
    print("=" * 60)
    mission = input("\n[사령관] 미션을 입력하세요:\n> ").strip()
    if not mission:
        print("[오류] 미션이 비어 있습니다.")
        sys.exit(1)
    return mission


def main() -> None:
    """CLI 진입점."""
    from utils.logger import setup_logging
    setup_logging()

    args = _parse_args()

    if args.boot_report:
        asyncio.run(send_boot_report())
        return

    mission = args.mission if args.mission else _interactive_mission()
    print(f"\n[사령부] 미션 수신: {mission}")
    print("[사령부] 요원 소집 중...\n")

    asyncio.run(run(mission=mission, no_interrupt=args.no_interrupt))


if __name__ == "__main__":
    main()
