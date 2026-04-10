"""전역 설정 로더 - .env 파일에서 환경변수를 읽어 전역 상수로 제공한다."""

import os
from pathlib import Path
from dotenv import load_dotenv

# 프로젝트 루트에서 .env 파일 로드
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# Anthropic 설정
ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
AGENT_MODEL: str = os.getenv("AGENT_MODEL", "claude-sonnet-4-6")
AGENT_MAX_TOKENS: int = int(os.getenv("AGENT_MAX_TOKENS", "4096"))

# 프로젝트 경로
MEMORY_DIR: Path = BASE_DIR / "memory"
LOG_DIR: Path = BASE_DIR / "logs"

# 로그
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

# 스케줄러
SCHEDULER_INTERVAL: int = int(os.getenv("SCHEDULER_INTERVAL", "60"))

# 알림
ENABLE_NOTIFICATIONS: bool = os.getenv("ENABLE_NOTIFICATIONS", "true").lower() == "true"

# ── 사용자 PC 경로 (자동 감지) ────────────────────────────────────────────────
HOME_DIR:      Path = Path.home()
DESKTOP_DIR:   Path = HOME_DIR / "Desktop"
DOWNLOADS_DIR: Path = HOME_DIR / "Downloads"
DOCUMENTS_DIR: Path = HOME_DIR / "Documents"
PICTURES_DIR:  Path = HOME_DIR / "Pictures"
MUSIC_DIR:     Path = HOME_DIR / "Music"
VIDEOS_DIR:    Path = HOME_DIR / "Videos"
USERNAME:      str  = os.getenv("USERNAME") or os.getenv("USER") or HOME_DIR.name


def validate():
    """필수 설정 값 검증 - API 키 누락 시 즉시 오류를 발생시킨다."""
    if not ANTHROPIC_API_KEY:
        raise EnvironmentError(
            "ANTHROPIC_API_KEY 가 설정되지 않았습니다. "
            ".env 파일을 확인하거나 환경변수를 설정해 주세요."
        )
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
