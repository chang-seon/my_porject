"""에이전트 기억 관리 - 대화 기록과 완료 작업을 JSON 파일로 영속 저장한다."""

import json
from pathlib import Path
from datetime import datetime
from config.settings import MEMORY_DIR


class AgentMemory:
    """대화 이력과 작업 기록을 JSON 파일로 관리한다."""

    def __init__(self, session_id: str = "default"):
        self.session_id = session_id
        self.conversation_file = MEMORY_DIR / f"{session_id}_conversation.json"
        self.tasks_file = MEMORY_DIR / f"{session_id}_tasks.json"
        self._conversation: list[dict] = self._load(self.conversation_file)
        self._tasks: list[dict] = self._load(self.tasks_file)

    # ── 내부 헬퍼 ──────────────────────────────────────────────────────────────

    def _load(self, path: Path) -> list:
        if path.exists():
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                return []
        return []

    def _save(self, path: Path, data: list):
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    # ── 대화 이력 ──────────────────────────────────────────────────────────────

    def add_message(self, role: str, content: str):
        """대화 메시지를 이력에 추가하고 즉시 저장한다."""
        self._conversation.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
        })
        self._save(self.conversation_file, self._conversation)

    def get_messages(self, last_n: int = 20) -> list[dict]:
        """Anthropic API 형식에 맞는 최근 N개 메시지를 반환한다."""
        messages = self._conversation[-last_n:]
        return [{"role": m["role"], "content": m["content"]} for m in messages]

    def clear_conversation(self):
        """대화 이력을 초기화한다."""
        self._conversation = []
        self._save(self.conversation_file, self._conversation)

    # ── 작업 기록 ──────────────────────────────────────────────────────────────

    def log_task(self, task: str, result: dict):
        """완료된 작업을 기록한다."""
        self._tasks.append({
            "task": task,
            "result": result,
            "timestamp": datetime.now().isoformat(),
        })
        self._save(self.tasks_file, self._tasks)

    def get_recent_tasks(self, n: int = 10) -> list[dict]:
        """최근 N개 작업 기록을 반환한다."""
        return self._tasks[-n:]
