from __future__ import annotations
import os
from dotenv import load_dotenv

load_dotenv()

# 자체 개발 커스텀 프록시 엔드포인트
LOCAL_ENDPOINT:      str   = os.getenv("LOCAL_ENDPOINT", "http://localhost:8080/v1/chat/completions")
AGENT_MODEL:         str   = os.getenv("AGENT_MODEL", "claude-sonnet")
AGENT_MAX_TOKENS:    int   = int(os.getenv("AGENT_MAX_TOKENS", "4096"))
PASS_THRESHOLD:      float = float(os.getenv("PASS_THRESHOLD", "8.0"))
MAX_RETRIES:         int   = int(os.getenv("MAX_RETRIES", "3"))
REQUEST_TIMEOUT:     int   = int(os.getenv("REQUEST_TIMEOUT", "120"))
DISCORD_WEBHOOK_URL: str   = os.getenv("DISCORD_WEBHOOK_URL", "")

# AI 세션 키
CLAUDE_SESSION_KEY:     str = os.getenv("CLAUDE_SESSION_KEY", "")
GEMINI_PSID:            str = os.getenv("GEMINI_PSID", "")
GEMINI_PSIDTS:          str = os.getenv("GEMINI_PSIDTS", "")
CHATGPT_SESSION_TOKEN:  str = os.getenv("CHATGPT_SESSION_TOKEN", "")


def validate() -> None:
    if not LOCAL_ENDPOINT:
        raise ValueError("LOCAL_ENDPOINT가 설정되지 않았습니다.")
    if not (0.0 < PASS_THRESHOLD <= 10.0):
        raise ValueError(f"PASS_THRESHOLD는 0 초과 10 이하여야 합니다. (현재: {PASS_THRESHOLD})")
    if MAX_RETRIES < 1:
        raise ValueError(f"MAX_RETRIES는 1 이상이어야 합니다. (현재: {MAX_RETRIES})")
