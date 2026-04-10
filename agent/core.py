"""에이전트 코어 - LLM 호출과 도구 실행 루프를 담당한다."""

import json
import anthropic
from config import settings
from agent.memory import AgentMemory
from tools import system_tools, file_tools, web_tools, notify, file_organizer

# ── 에이전트가 사용할 도구 정의 (Anthropic tool_use 스키마) ─────────────────────

TOOLS = [
    {
        "name": "get_pc_overview",
        "description": "PC 전체 개요를 조회한다. 사용자명, 홈·바탕화면·다운로드·문서·사진·음악·동영상 폴더 경로, 전체 드라이브 현황, 운영체제 정보를 반환한다.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_system_status",
        "description": "현재 PC의 CPU·메모리·전체 드라이브 사용 현황을 조회한다.",
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
    {
        "name": "smart_organize_folder",
        "description": "지정 폴더의 파일을 내용·확장자 분석으로 자동 분류·정리한다. PII(주민번호·카드번호 등) 탐지 시 자동 격리하고 감사 로그를 기록한다.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "정리할 폴더 경로"},
            },
            "required": ["path"],
        },
    },
    {
        "name": "find_duplicate_files",
        "description": "지정 폴더에서 파일명이 달라도 내용이 완전히 동일한 중복 파일을 SHA-256 해시로 찾아 보고한다.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "탐색할 폴더 경로"},
            },
            "required": ["path"],
        },
    },
    {
        "name": "approve_pending_file",
        "description": "PII 탐지 또는 저신뢰 분류로 보류(pending)된 파일의 처리를 관리자 승인 후 최종 실행한다.",
        "input_schema": {
            "type": "object",
            "properties": {
                "target_dir":        {"type": "string", "description": "원본 폴더 경로"},
                "pending_json_path": {"type": "string", "description": "pending JSON 파일 경로"},
            },
            "required": ["target_dir", "pending_json_path"],
        },
    },
]

# ── 도구 실행 디스패처 ──────────────────────────────────────────────────────────

TOOL_HANDLERS = {
    "get_pc_overview":   lambda args: system_tools.get_pc_overview(),
    "get_system_status": lambda args: system_tools.get_system_status(),
    "list_top_processes": lambda args: system_tools.list_top_processes(args.get("n", 10)),
    "list_directory": lambda args: file_tools.list_directory(args["path"], args.get("pattern", "*")),
    "find_large_files": lambda args: file_tools.find_large_files(args["path"], args.get("min_size_mb", 100)),
    "organize_downloads": lambda args: file_tools.organize_downloads(args["downloads_path"]),
    "search_web": lambda args: web_tools.search_duckduckgo(args["query"], args.get("max_results", 5)),
    "send_notification":   lambda args: notify.send_notification(args["title"], args["message"]),
    "smart_organize_folder": lambda args: file_organizer.organize_folder(args["path"]),
    "find_duplicate_files":  lambda args: file_organizer.find_duplicate_files(args["path"]),
    "approve_pending_file":  lambda args: file_organizer.approve_pending(args["target_dir"], args["pending_json_path"]),
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

    def __init__(self, session_id: str = "default"):
        settings.validate()
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.memory = AgentMemory(session_id)
        self._system_prompt = self._build_system_prompt()

    @staticmethod
    def _build_system_prompt() -> str:
        """실행 시점의 실제 PC 경로를 포함한 시스템 프롬프트를 생성한다."""
        return f"""당신은 {settings.USERNAME} 님의 PC 전체를 관리하는 AI 에이전트입니다.

사용자 PC 정보:
- 사용자명:    {settings.USERNAME}
- 홈 디렉터리: {settings.HOME_DIR}
- 바탕화면:    {settings.DESKTOP_DIR}
- 다운로드:    {settings.DOWNLOADS_DIR}
- 문서:        {settings.DOCUMENTS_DIR}
- 사진:        {settings.PICTURES_DIR}
- 음악:        {settings.MUSIC_DIR}
- 동영상:      {settings.VIDEOS_DIR}

역할:
- PC 전체의 CPU·메모리·전체 드라이브 상태를 모니터링하고 이상 징후를 보고한다.
- 바탕화면·다운로드·문서·사진 등 주요 폴더의 파일을 정리·분류·검색한다.
- PII(주민번호·카드번호 등 개인정보) 포함 파일을 자동 감지해 격리한다.
- 중복 파일을 찾아 정리를 제안한다.
- 웹 검색으로 필요한 정보를 찾아 보고한다.
- 사용자가 요청한 반복 작업을 자동화한다.

원칙:
- 파일 삭제·프로세스 종료 등 위험한 작업은 반드시 사용자에게 확인 후 실행한다.
- 경로를 추측하지 않고, 위에 명시된 실제 PC 경로를 기준으로 작업한다.
- 모든 응답은 한국어로 간결하고 명확하게 작성한다.
- 도구 실행 결과는 사용자가 이해하기 쉽게 요약해서 전달한다.
"""

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
                system=self._system_prompt,
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
