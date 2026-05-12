"""하네스 엔지니어링 프레임워크 — 진입점."""
from __future__ import annotations
import sys
import config
from rich.console import Console

console = Console()


def main() -> None:
    try:
        config.validate()
    except ValueError as e:
        console.print(f"[red][오류] {e}[/red]")
        sys.exit(1)

    console.print("[green]환경 설정 OK - 하네스 엔지니어링 준비 완료[/green]")
    console.print(f"  엔드포인트: {config.LOCAL_ENDPOINT}")
    console.print(f"  모델:       {config.AGENT_MODEL}")
    console.print(f"  합격 기준:  {config.PASS_THRESHOLD}점")
    console.print(f"  최대 시도:  {config.MAX_RETRIES}회")
    console.print(f"  Discord:    {'연결됨' if config.DISCORD_WEBHOOK_URL else '미설정'}")


if __name__ == "__main__":
    main()
