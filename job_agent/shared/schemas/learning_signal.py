from __future__ import annotations
from enum import Enum
from typing import Optional, Any
from pydantic import BaseModel, ConfigDict


class SignalLayer(str, Enum):
    A = "A"   # 일회성 선택지 — 페르소나 보강 시
    B = "B"   # 반복 선택지 (이유 포함) — 알림 응답·자소서 검토 시
    C = "C"   # 자유 입력 — 본인 명시 피드백
    D = "D"   # 자동 감지 — 알림 무시시간·수정 diff
    E = "E"   # 외부 결과 — 합격·탈락


class LearningSignal(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_id: str                              # 격리 컬럼 (#38)
    layer: SignalLayer
    signal_type: str                          # 레이어 내 세부 종류
    payload: dict[str, Any] = {}              # 층별 자유 데이터

    # 컨텍스트
    source_module: Optional[str] = None       # 발생 모듈 (validator, job_search 등)
    reference_id: Optional[str] = None        # 연관 공고·자소서 ID

    # 라벨 (#50 자체AI 학습 대비)
    is_labeled: bool = False
    label: Optional[str] = None
    revision_history: list[str] = []          # 수정 이력

    # 타임스탬프 (ISO8601 + 계층 인덱스 #37)
    timestamp: Optional[str] = None
    year: Optional[int] = None
    month: Optional[int] = None
    day: Optional[int] = None
