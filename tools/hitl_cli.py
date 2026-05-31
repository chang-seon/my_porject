"""HITL CLI — 사용자 결정 수신 도구"""
import argparse
import sys
from job_agent.core.hitl_bus import get_pending, respond


def main():
    parser = argparse.ArgumentParser(description="HITL 요청 처리 CLI")
    sub = parser.add_subparsers(dest="command")

    # 대기 목록 조회
    list_cmd = sub.add_parser("list", help="대기 중인 요청 목록")
    list_cmd.add_argument("--user", default="default_user", help="사용자 ID")

    # 응답
    resp_cmd = sub.add_parser("respond", help="요청에 응답")
    resp_cmd.add_argument("--id", required=True, help="요청 ID")
    resp_cmd.add_argument("--answer", required=True, help="응답 내용")

    args = parser.parse_args()

    if args.command == "list":
        result = get_pending(args.user)
        if result["결과"] == "실패":
            print(f"오류: {result['이유']}")
            sys.exit(1)
        requests = result["requests"]
        if not requests:
            print("대기 중인 요청 없음")
            return
        for r in requests:
            import json
            options = json.loads(r["options"])
            print(f"\n[{r['request_id']}] {r['question']}")
            for i, opt in enumerate(options, 1):
                print(f"  {i}. {opt}")

    elif args.command == "respond":
        result = respond(args.id, args.answer)
        if result["결과"] == "성공":
            print(f"응답 완료: {args.id} → {args.answer}")
        else:
            print(f"오류: {result['이유']}")
            sys.exit(1)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
