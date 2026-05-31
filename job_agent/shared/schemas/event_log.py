from __future__ import annotations
from typing import Any, Optional
from pydantic import BaseModel, ConfigDict


class EventLog(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_id: str                          # 격리 컬럼 (#38)
    event_type: str                       # persona_updated, job_fetched, signal_recorded 등
    event_data: dict[str, Any] = {}

    # 타임스탬프 (ISO8601 + 계층 인덱스 #37)
    timestamp: Optional[str] = None
    year: Optional[int] = None
    month: Optional[int] = None
    day: Optional[int] = None
