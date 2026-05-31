from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, ConfigDict


class JobPosting(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # 식별
    job_id: Optional[str] = None
    source: str                          # 사람인, 워크넷, 잡알리오 등
    url: str

    # 공고 내용
    title: str
    company: str
    location: Optional[str] = None
    job_role: Optional[str] = None
    employment_type: Optional[str] = None   # 정규직, 계약직, 인턴 등
    salary: Optional[str] = None
    skills_required: list[str] = []
    raw_text: Optional[str] = None

    # 날짜 (ISO8601 + 계층 인덱스 #37)
    posted_date: Optional[str] = None
    deadline: Optional[str] = None
    year: Optional[int] = None
    month: Optional[int] = None
    day: Optional[int] = None
