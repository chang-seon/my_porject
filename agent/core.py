"""에이전트 코어 - LLM 호출과 도구 실행 루프를 담당한다."""

import json
import anthropic
from config import settings
from agent.memory import AgentMemory
from tools import system_tools, file_tools, web_tools, notify, file_organizer, job_tools, image_organizer, office_tools

# ── 에이전트가 사용할 도구 정의 (Anthropic tool_use 스키마) ─────────────────────

TOOLS = [
    {
        "name": "get_pc_overview",
        "description": "PC 전체 개요를 조회한다. 사용자명, 홈·바탕화면·다운로드·문서·사진·음악·동영상 폴더 경로, 전체 드라이브 현황(내장·이동식 구분 포함), 운영체제 정보를 반환한다.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_removable_drives",
        "description": "현재 PC에 연결된 이동식 드라이브(USB·외장HDD·SD카드 등)만 조회한다. 연결 여부 확인 및 용량 점검에 사용한다.",
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

    # ── 채용 자동화 도구 ────────────────────────────────────────────────────────
    {
        "name": "load_resume_profile",
        "description": "저장된 이력서·자소서 프로필을 불러온다. 자소서 작성 전 반드시 먼저 호출해 지원자 정보를 파악한다.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "save_resume_profile",
        "description": "사용자가 제공한 이력서·자소서 정보를 JSON 프로필로 저장한다.",
        "input_schema": {
            "type": "object",
            "properties": {
                "profile": {"type": "object", "description": "저장할 이력서 프로필 딕셔너리"},
            },
            "required": ["profile"],
        },
    },
    {
        "name": "crawl_job_postings",
        "description": "사람인·원티드에서 채용공고를 키워드로 크롤링한다.",
        "input_schema": {
            "type": "object",
            "properties": {
                "keyword": {"type": "string", "description": "검색 키워드 (예: '행정사무', '회계')"},
                "site":    {"type": "string", "description": "크롤링 대상: 'saramin' | 'wanted' | 'all' (기본 all)"},
                "count":   {"type": "integer", "description": "사이트당 최대 공고 수 (기본 10)"},
            },
            "required": ["keyword"],
        },
    },
    {
        "name": "fetch_job_detail",
        "description": "채용공고 URL에서 담당업무·자격요건·우대조건·회사소개 등 상세 정보를 가져온다. 자소서 맞춤 작성에 사용한다.",
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "채용공고 상세 페이지 URL"},
            },
            "required": ["url"],
        },
    },
    {
        "name": "analyze_company_culture",
        "description": "회사명으로 인재상·핵심가치·기업문화를 웹 검색해 수집한다. 자소서 작성 방향 설정에 사용한다.",
        "input_schema": {
            "type": "object",
            "properties": {
                "company_name": {"type": "string", "description": "분석할 회사명"},
            },
            "required": ["company_name"],
        },
    },
    {
        "name": "save_cover_letter",
        "description": "작성 완료된 자소서를 파일로 저장한다.",
        "input_schema": {
            "type": "object",
            "properties": {
                "company":   {"type": "string", "description": "회사명"},
                "job_title": {"type": "string", "description": "지원 직무명"},
                "content":   {"type": "string", "description": "저장할 자소서 전문"},
            },
            "required": ["company", "job_title", "content"],
        },
    },
    {
        "name": "list_cover_letters",
        "description": "저장된 자소서 파일 목록을 최신순으로 반환한다.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_job_briefing",
        "description": "여러 키워드로 맞춤 공고를 한꺼번에 검색해 브리핑 형태로 반환한다.",
        "input_schema": {
            "type": "object",
            "properties": {
                "keywords":           {"type": "array", "items": {"type": "string"}, "description": "검색 키워드 목록"},
                "count_per_keyword":  {"type": "integer", "description": "키워드당 최대 공고 수 (기본 5)"},
            },
            "required": ["keywords"],
        },
    },
    {
        "name": "validate_cover_letter",
        "description": "작성된 자소서를 resume_profile.json 과 대조해 프로필에 없는 내용(없는 자격증·경력·수상 등)을 탐지한다. 자소서 저장 전 반드시 호출한다.",
        "input_schema": {
            "type": "object",
            "properties": {
                "cover_letter_text": {"type": "string", "description": "검증할 자소서 전문"},
            },
            "required": ["cover_letter_text"],
        },
    },
    {
        "name": "open_job_posting",
        "description": "채용공고 URL을 기본 브라우저로 열어 지원 페이지로 바로 이동한다.",
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "열 채용공고 URL"},
            },
            "required": ["url"],
        },
    },

    # ── 오피스 자동화 도구 ───────────────────────────────────────────────────────
    {
        "name": "create_pptx",
        "description": "PowerPoint(.pptx) 파일을 자동 생성한다. 제목과 슬라이드 목록을 받아 완성된 PPT 파일을 저장한다.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title":       {"type": "string",  "description": "프레젠테이션 전체 제목"},
                "slides":      {
                    "type": "array",
                    "description": "슬라이드 목록. 각 항목: {제목, 내용(list), 레이아웃(title|content|two_column|blank), 노트(선택)}",
                    "items": {"type": "object"}
                },
                "output_path": {"type": "string",  "description": "저장 경로(.pptx). 비워두면 Documents/AgentAI_문서에 자동 저장"},
                "theme":       {"type": "string",  "description": "테마: default(파랑) | dark | minimal"},
                "open_after":  {"type": "boolean", "description": "생성 후 파일 바로 열기 (기본 true)"},
            },
            "required": ["title", "slides"],
        },
    },
    {
        "name": "create_excel",
        "description": "Excel(.xlsx) 파일을 자동 생성한다. 여러 시트에 표·수식·자동필터를 포함한 완성된 파일을 저장한다.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title":       {"type": "string", "description": "파일 대표 제목 (첫 시트 상단 표시)"},
                "sheets":      {
                    "type": "array",
                    "description": "시트 목록. 각 항목: {시트명, 헤더(list), 데이터(list of list), 수식(dict, 선택), 너비(dict, 선택)}",
                    "items": {"type": "object"}
                },
                "output_path": {"type": "string",  "description": "저장 경로(.xlsx)"},
                "open_after":  {"type": "boolean", "description": "생성 후 파일 바로 열기 (기본 true)"},
            },
            "required": ["title", "sheets"],
        },
    },
    {
        "name": "create_document",
        "description": "한글/Word 문서(.docx)를 자동 생성한다. HWP 2020 이상에서도 바로 열 수 있다. 제목·소제목·본문·표·목록을 포함한 완성된 문서를 저장한다.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title":       {"type": "string", "description": "문서 제목"},
                "sections":    {
                    "type": "array",
                    "description": "섹션 목록. 각 항목: {제목(선택), 레벨(1~3), 내용(본문텍스트), 목록(list,선택), 표(dict,선택)}",
                    "items": {"type": "object"}
                },
                "output_path": {"type": "string",  "description": "저장 경로(.docx)"},
                "open_after":  {"type": "boolean", "description": "생성 후 파일 바로 열기 (기본 true)"},
            },
            "required": ["title", "sections"],
        },
    },

    # ── 이미지 캐릭터 분류 도구 ──────────────────────────────────────────────────
    {
        "name": "analyze_image_character",
        "description": "단일 이미지 파일을 Claude Vision으로 분석해 등장 캐릭터 이름을 반환한다.",
        "input_schema": {
            "type": "object",
            "properties": {
                "image_path": {"type": "string", "description": "분석할 이미지 파일 경로"},
            },
            "required": ["image_path"],
        },
    },
    {
        "name": "preview_image_organization",
        "description": "폴더 내 이미지를 실제로 이동하지 않고 캐릭터별 분류 결과를 미리 보여준다. 실제 이동 전 반드시 먼저 호출한다.",
        "input_schema": {
            "type": "object",
            "properties": {
                "folder_path": {"type": "string", "description": "미리보기할 이미지 폴더 경로 (USB·외장하드·로컬 모두 가능)"},
            },
            "required": ["folder_path"],
        },
    },
    {
        "name": "organize_images_by_character",
        "description": "폴더 내 이미지를 Claude Vision으로 분석해 캐릭터별 하위 폴더로 자동 이동한다. confirm=True 여야 실제 이동이 실행된다.",
        "input_schema": {
            "type": "object",
            "properties": {
                "folder_path": {"type": "string", "description": "정리할 이미지 폴더 경로"},
                "confirm":     {"type": "boolean", "description": "true 여야 실제 이동 실행"},
            },
            "required": ["folder_path", "confirm"],
        },
    },
]

# ── 도구 실행 디스패처 ──────────────────────────────────────────────────────────

TOOL_HANDLERS = {
    "get_pc_overview":      lambda args: system_tools.get_pc_overview(),
    "get_removable_drives": lambda args: system_tools.get_removable_drives(),
    "get_system_status":    lambda args: system_tools.get_system_status(),
    "list_top_processes": lambda args: system_tools.list_top_processes(args.get("n", 10)),
    "list_directory": lambda args: file_tools.list_directory(args["path"], args.get("pattern", "*")),
    "find_large_files": lambda args: file_tools.find_large_files(args["path"], args.get("min_size_mb", 100)),
    "organize_downloads": lambda args: file_tools.organize_downloads(args["downloads_path"]),
    "search_web": lambda args: web_tools.search_duckduckgo(args["query"], args.get("max_results", 5)),
    "send_notification":   lambda args: notify.send_notification(args["title"], args["message"]),
    "smart_organize_folder": lambda args: file_organizer.organize_folder(args["path"]),
    "find_duplicate_files":  lambda args: file_organizer.find_duplicate_files(args["path"]),
    "approve_pending_file":  lambda args: file_organizer.approve_pending(args["target_dir"], args["pending_json_path"]),

    # ── 채용 자동화 ─────────────────────────────────────────────────────────────
    "load_resume_profile":    lambda args: job_tools.load_resume_profile(),
    "save_resume_profile":    lambda args: job_tools.save_resume_profile(args["profile"]),
    "crawl_job_postings":     lambda args: job_tools.crawl_job_postings(
                                  args["keyword"], args.get("site", "all"), args.get("count", 10)
                              ),
    "fetch_job_detail":       lambda args: job_tools.fetch_job_detail(args["url"]),
    "analyze_company_culture":lambda args: job_tools.analyze_company_culture(args["company_name"]),
    "save_cover_letter":      lambda args: job_tools.save_cover_letter(
                                  args["company"], args["job_title"], args["content"]
                              ),
    "list_cover_letters":     lambda args: job_tools.list_cover_letters(),
    "get_job_briefing":       lambda args: job_tools.get_job_briefing(
                                  args["keywords"], args.get("count_per_keyword", 5)
                              ),
    "validate_cover_letter":  lambda args: job_tools.validate_cover_letter(args["cover_letter_text"]),
    "open_job_posting":       lambda args: job_tools.open_job_posting(args["url"]),

    # ── 오피스 자동화 ────────────────────────────────────────────────────────────
    "create_pptx":     lambda args: office_tools.create_pptx(
                           args["title"], args["slides"],
                           args.get("output_path", ""), args.get("theme", "default"),
                           args.get("open_after", True)
                       ),
    "create_excel":    lambda args: office_tools.create_excel(
                           args["title"], args["sheets"],
                           args.get("output_path", ""), args.get("open_after", True)
                       ),
    "create_document": lambda args: office_tools.create_document(
                           args["title"], args["sections"],
                           args.get("output_path", ""), args.get("open_after", True)
                       ),

    # ── 이미지 캐릭터 분류 ───────────────────────────────────────────────────────
    "analyze_image_character":      lambda args: image_organizer.analyze_image_character(args["image_path"]),
    "preview_image_organization":   lambda args: image_organizer.preview_image_organization(args["folder_path"]),
    "organize_images_by_character": lambda args: image_organizer.organize_images_by_character(
                                        args["folder_path"], args.get("confirm", False)
                                    ),
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

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
절대 원칙 — 어떤 상황에서도 반드시 지킨다
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[1. 사실 원칙 — 없는 내용은 절대 만들어내지 않는다]
- 자소서·문서·보고서 작성 시 resume_profile.json 에 존재하지 않는
  경험·자격증·수상·역할·수치를 절대 지어내지 않는다.
- 프로필에 근거 없는 내용이 생성됐을 경우 반드시 해당 문장 앞에
  ⚠️ 표시를 붙이고 사용자에게 "프로필에 없는 내용입니다. 삭제할까요?"라고 묻는다.
- Excel·PPT 생성 시 사용자가 직접 제공한 수치·데이터만 사용한다.
  빈 칸을 임의 숫자로 채우거나 없는 항목을 추가하지 않는다.

[2. 확인 원칙 — 실행 전 반드시 보여주고 물어본다]
- 파일 이동·삭제·덮어쓰기·폴더 생성 등 되돌리기 어려운 작업은
  실행 전 아래 형식으로 요약하고 사용자 확인을 기다린다:
    실행 예정: [작업 내용]
    대상:      [파일/폴더 경로]
    진행할까요? (예/아니오)
- 이미지 정리는 반드시 preview_image_organization 을 먼저 실행해
  결과를 보여준 뒤, 사용자가 "진행해" 라고 해야만 실제 이동을 실행한다.

[3. 범위 원칙 — 요청받은 것만 한다]
- 사용자가 지시하지 않은 추가 작업(파일 삭제, 폴더 생성, 설정 변경 등)을
  임의로 수행하지 않는다.
- "~어때?", "~할까?" 같은 단순 질문은 실행 없이 설명만 한다.
- 요청 범위가 불명확하면 실행 전에 "어디까지 할까요?"라고 먼저 확인한다.

[4. 불확실 원칙 — 모르면 추측하지 않고 확인한다]
- 경로·파일명·데이터·회사명 등이 불확실하면 추측해서 실행하지 않는다.
  반드시 사용자에게 "○○이 맞나요?"라고 먼저 확인한다.
- 도구 실행 결과가 비어 있거나 예상과 다르면 즉시 사용자에게 알리고
  다음 행동을 묻는다. 스스로 재시도를 반복하지 않는다.

[5. 경로 원칙 — 실제 경로만 사용한다]
- 파일·폴더 경로는 위에 명시된 실제 PC 경로 또는 사용자가 직접 알려준
  경로만 사용한다. 경로를 임의로 추측하거나 만들어내지 않는다.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
기능별 원칙
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[오피스 자동화]
- PPT·Excel·문서 작성 요청 시 사용자가 전달한 내용을 바탕으로 구조를 설계해 도구를 호출한다.
- PPT: 표지 슬라이드 + 본문 슬라이드로 구성하며 불릿 내용은 핵심만 간결하게 담는다.
- Excel: 사용자가 제공한 데이터만 입력하고, 요청한 수식만 추가한다.
- 문서: 제목·소제목 계층(레벨 1~3)과 본문을 체계적으로 구성한다.
- 파일 생성 완료 후 저장 경로를 사용자에게 알린다.

[채용 자동화 및 자소서]
- 자소서 작성 순서: load_resume_profile → 채용공고 크롤링 → 회사 인재상 분석 → 작성.
  이 순서를 반드시 지킨다. 프로필을 먼저 확인하지 않고 자소서를 쓰지 않는다.
- 사람이 쓴 것처럼 자연스럽게 작성한다:
  * 짧은 문장과 긴 문장을 자연스럽게 섞는다.
  * "도전", "열정", "성장", "기여" 같은 단골 AI 표현을 남발하지 않는다.
  * 뉴질랜드 연수, 인형극 봉사, 사회복지 실습 등 실제 에피소드를 구체적으로 녹여낸다.
  * 회사 인재상 키워드는 자연스럽게 한두 번만 연결한다.
- 작성 완료 후 반드시 validate_cover_letter 를 호출해 팩트체크를 수행한다.
  경고가 있으면 해당 문장에 ⚠️ 표시 후 "이 내용이 맞나요?"라고 사용자에게 확인한다.
  사용자가 확인한 뒤에만 save_cover_letter 로 저장한다.

[일반]
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
