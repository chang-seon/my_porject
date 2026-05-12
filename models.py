from __future__ import annotations
from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field


class StepStatus(str, Enum):
    PENDING              = "pending"
    IN_PROGRESS          = "in_progress"
    PASSED               = "passed"
    MAX_RETRIES_EXCEEDED = "max_retries_exceeded"


class Feedback(BaseModel):
    reviewer:  str
    content:   str
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class DiffRecord(BaseModel):
    attempt:      int
    previous:     str
    current:      str
    diff_summary: str
    timestamp:    str = Field(default_factory=lambda: datetime.now().isoformat())


class ReviewResult(BaseModel):
    attempt:          int
    score:            float
    logic_feedback:   Feedback
    tone_feedback:    Feedback
    rubric_summary:   str
    rejection_reason: str
    passed:           bool


class State(BaseModel):
    task:             str
    raw_data:         str
    plan:             str   = ""
    draft:            str   = ""
    rejection_reason: str   = ""
    current_score:    float = 0.0
    attempt:          int   = 0
    max_attempts:     int   = 3
    pass_threshold:   float = 8.0
    status:           StepStatus        = StepStatus.PENDING
    feedbacks:        list[Feedback]    = Field(default_factory=list)
    diff_records:     list[DiffRecord]  = Field(default_factory=list)
    review_results:   list[ReviewResult]= Field(default_factory=list)
    final_output:     str               = ""
