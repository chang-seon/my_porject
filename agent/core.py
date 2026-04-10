"""에이전트 코어 - LLM 호출과 도구 실행 루프를 담당한다."""

import json
import anthropic
from config import settings
from agent.memory import AgentMemory
from tools import system_tools, file_tools, web_tools, notify

# ── 에이전트가 사용할 도구 정의 (Anthropic tool_use 스키마) ─────────────────────

TOOLS = [
    {
        "name": "get_system_status",
        "description": "현재 PC의 CPU·메모리·디스크 사용 현황을 조회한다.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "list_top_processes",
        "description": "CPU 사용량 상위 프로세스 목록을 조회한다.",
        "input_schema": {
            "type": "object",
            "properties": {"n": {"type": "integer", "description": "조회할 프로세스 수 (기본 10)"}},
            "required": [],
        },
    },
    {
        "name": "list_directory",
        "description": "지정 경로의 파일·폴더 목록을 조회한다.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "조회할 디렉터리 경로"},
                "pattern": {"type": "string", "description": "파일 패턴 (예: *.txt)"},
            },
            "required": ["path"],
        },
    },
    {
        "name": "find_large_files",
        "description": "지정 경로에서 특정 크기 이상의 대용량 파일을 찾는다.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "min_size_mb": {"type": "number", "description": "최소 파일 크기 (MB)"},
            },
            "required": ["path"],
        },
    },
    {
        "name": "organize_downloads",
        "description": "다운로드 폴더를 확장자별 하위 폴더로 자동 정리한다.",
        "input_schema": {
            "type": "object",
            "properties": {"downloads_path": {"type": "string"}},
            "required": ["downloads_path"],
        },
    },
    {
        "name": "search_web",
        "description": "DuckDuckGo 로 웹을 검색하고 결과를 반환한다.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "검색 쿼리"},
                "max_results": {"type": "integer"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "send_notification",
        "description": "윈도우 데스크톱 알림을 전송한다.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "message": {"type": "string"},
            },
            "required": ["title", "message"],
        },
    },
]

# ── 도구 실행 디스패처 ──────────────────────────────────────────────────────────

TOOL_HANDLERS = {
    "get_system_status": lambda args: system_tools.get_system_status(),
    "list_top_processes": lambda args: system_tools.list_top_processes(args.get("n", 10)),
    "list_directory": lambda args: file_tools.list_directory(args["path"], args.get("pattern", "*")),
    "find_large_files": lambda args: file_tools.find_large_files(args["path"], args.get("min_size_mb", 100)),
    "organize_downloads": lambda args: file_tools.organize_downloads(args["downloads_path"]),
    "search_web": lambda args: web_tools.search_duckduckgo(args["query"], args.get("max_results", 5)),
    "send_notification": lambda args: notify.send_notification(args["title"], args["message"]),
}


def _run_tool(name: str, args: dict) -> str:
    handler = TOOL_HANDLERS.get(name)
    if handler is None:
        return json.dumps({"오류": f"알 수 없는 도구: {name}"}, ensure_ascii=False)
    result = handler(args)
    return json.dumps(result, ensure_ascii=False, indent=2)


# ── 에이전트 클래스 ─────────────────────────────────────────────────────────────

class PCAgent:
    """사용자의 PC를 관리·자동화하는 에이전트."""

    SYSTEM_PROMPT = """당신은 사용자의 Windows PC를 관리하는 AI 에이전트입니다.

역할:
- 시스템 상태(CPU·메모리·디스크)를 모니터링하고 이상 징후를 보고한다.
- 파일 정리·검색·이동 등 파일 관리 작업을 수행한다.
- 웹 검색으로 필요한 정보를 찾아 보고한다.
- 사용자가 요청한 반복 작업을 자동화한다.

원칙:
- 파일 삭제, 프로세스 종료 등 위험한 작업은 반드시 사용자에게 확인 후 실행한다.
- 모든 응답은 한국어로 간결하고 명확하게 작성한다.
- 도구 실행 결과는 사용자가 이해하기 쉽게 요약해서 전달한다.
"""

    def __init__(self, session_id: str = "default"):
        settings.validate()
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.memory = AgentMemory(session_id)

    def chat(self, user_input: str) -> str:
        """사용자 입력을 받아 에이전트 응답을 반환한다."""
        self.memory.add_message("user", user_input)
        messages = self.memory.get_messages()

        response_text = self._run_agent_loop(messages)
        self.memory.add_message("assistant", response_text)
        return response_text

    def _run_agent_loop(self, messages: list[dict]) -> str:
        """LLM + 도구 호출 루프를 실행하고 최종 텍스트 응답을 반환한다."""
        loop_messages = list(messages)

        while True:
            response = self.client.messages.create(
                model=settings.AGENT_MODEL,
                max_tokens=settings.AGENT_MAX_TOKENS,
                system=self.SYSTEM_PROMPT,
                tools=TOOLS,
                messages=loop_messages,
            )

            # 텍스트만 반환하는 경우
            if response.stop_reason == "end_turn":
                return "".join(
                    block.text for block in response.content if hasattr(block, "text")
                )

            # 도구 호출이 있는 경우
            if response.stop_reason == "tool_use":
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        print(f"  [도구 실행] {block.name}({block.input})")
                        result = _run_tool(block.name, block.input)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result,
                        })

                # 어시스턴트 응답 + 도구 결과를 메시지에 추가
                loop_messages.append({"role": "assistant", "content": response.content})
                loop_messages.append({"role": "user", "content": tool_results})
            else:
                # 예상치 못한 stop_reason
                break

        return "에이전트 루프가 예기치 않게 종료되었습니다."
