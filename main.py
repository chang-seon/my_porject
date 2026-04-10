"""PC 에이전트 AI 진입점 - 대화형 모드와 스케줄러 모드를 지원한다."""

import argparse
import sys
from agent.core import PCAgent
from tools.notify import log_alert


def run_chat_mode():
    """대화형 CLI 모드로 에이전트를 실행한다."""
    log_alert("INFO", "PC 에이전트 AI 가 시작되었습니다. 종료하려면 'exit' 또는 'quit' 을 입력하세요.")
    agent = PCAgent()

    while True:
        try:
            user_input = input("\n사용자 > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n에이전트를 종료합니다.")
            break

        if not user_input:
            continue
        if user_input.lower() in ("exit", "quit", "종료"):
            print("에이전트를 종료합니다.")
            break

        try:
            response = agent.chat(user_input)
            print(f"\n에이전트 > {response}")
        except Exception as e:
            log_alert("ERROR", f"오류가 발생했습니다: {e}")


def run_scheduler_mode():
    """백그라운드 스케줄러 모드로 에이전트를 실행한다."""
    from tools import scheduler, system_tools
    from tools.notify import send_notification
    from config.settings import SCHEDULER_INTERVAL

    log_alert("INFO", f"스케줄러 모드 시작 - {SCHEDULER_INTERVAL}초 주기로 시스템을 모니터링합니다.")

    def monitor_task():
        status = system_tools.get_system_status()
        cpu = status["cpu"]["사용률(%)"]
        mem = status["memory"]["사용률(%)"]
        disk = status["disk"]["사용률(%)"]
        log_alert("INFO", f"시스템 상태 - CPU: {cpu}% | 메모리: {mem}% | 디스크: {disk}%")

        # 임계값 초과 시 알림
        if cpu > 85:
            send_notification("CPU 경고", f"CPU 사용률이 {cpu}% 입니다.")
        if mem > 90:
            send_notification("메모리 경고", f"메모리 사용률이 {mem}% 입니다.")
        if disk > 90:
            send_notification("디스크 경고", f"디스크 사용률이 {disk}% 입니다.")

    scheduler.add_job(monitor_task, SCHEDULER_INTERVAL, label="시스템 모니터링")
    scheduler.run_scheduler(blocking=True)


def main():
    parser = argparse.ArgumentParser(description="PC 에이전트 AI")
    parser.add_argument(
        "--mode",
        choices=["chat", "scheduler"],
        default="chat",
        help="실행 모드 선택 (기본: chat)",
    )
    args = parser.parse_args()

    if args.mode == "chat":
        run_chat_mode()
    elif args.mode == "scheduler":
        run_scheduler_mode()


if __name__ == "__main__":
    main()
