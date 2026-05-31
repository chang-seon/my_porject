from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, ConfigDict


class Education(BaseModel):
    model_config = ConfigDict(extra="forbid")
    school: str
    major: Optional[str] = None
    degree: Optional[str] = None          # 학사, 석사, 박사 등
    graduated: Optional[str] = None       # ISO8601


class TargetJob(BaseModel):
    model_config = ConfigDict(extra="forbid")
    industry: str
    job_role: str
    priority: int = 1                     # 1=최우선


class ContentAsset(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str
    description: str
    context: str                          # 맥락 필수
    tags: list[str] = []
    is_killer: bool = False
    ai_relevance: float = 0.0             # 0.0~1.0
    usage_count: int = 0


class Skill(BaseModel):
    model_config = ConfigDict(extra="forbid")
    skill_type: str                       # 기술, 자격증, 어학 등
    name: str
    acquired_date: Optional[str] = None   # ISO8601
    ai_relevance: float = 0.0
    status: str = "보유"                  # 보유, 학습중, 만료


class StyleMarker(BaseModel):
    model_config = ConfigDict(extra="forbid")
    marker_name: str
    description: str
    examples: list[str] = []
    weight: float = 1.0


class AntiPattern(BaseModel):
    model_config = ConfigDict(extra="forbid")
    pattern_name: str
    description: str
    examples: list[str] = []


class Trait(BaseModel):
    model_config = ConfigDict(extra="forbid")
    trait_type: str                       # 강점, 약점
    trait: str
    evidence: Optional[str] = None
    self_aware: bool = True


class Value(BaseModel):
    model_config = ConfigDict(extra="forbid")
    value_text: str
    source: Optional[str] = None


class Constraint(BaseModel):
    model_config = ConfigDict(extra="forbid")
    constraint_type: str                  # 위치, 연봉, 근무형태 등
    value: str
    is_hard: bool = True                  # True=절대 조건
    threshold_dynamic: Optional[str] = None   # 동적기준값 키 (#37)


class CareerStage(BaseModel):
    model_config = ConfigDict(extra="forbid")
    stage: str                            # 신입, 주니어, 경력
    changed_date: Optional[str] = None    # ISO8601


class Persona(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_id: str                          # 격리 컬럼 필수 (#38)

    # 섹션 1 — 신원
    name: str
    birth: Optional[str] = None           # ISO8601
    address: Optional[str] = None
    education: list[Education] = []
    disability: Optional[str] = None
    career_stage: Optional[str] = None    # 신입, 주니어, 경력

    # 섹션 2 — 목표 직무
    target_jobs: list[TargetJob] = []

    # 섹션 3 — 콘텐츠 자산
    content_assets: list[ContentAsset] = []

    # 섹션 4 — 스킬·자격
    skills: list[Skill] = []

    # 섹션 5 — 문체 카드
    style_markers: list[StyleMarker] = []

    # 섹션 6 — 안티패턴
    anti_patterns: list[AntiPattern] = []

    # 섹션 7 — 성격
    traits: list[Trait] = []

    # 섹션 8 — 가치관
    values: list[Value] = []

    # 섹션 9 — 제약
    constraints: list[Constraint] = []

    # 섹션 11 — 커리어 단계 이력
    career_history: list[CareerStage] = []
