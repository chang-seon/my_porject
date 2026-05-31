import pytest
from pydantic import ValidationError
from job_agent.shared.schemas import (
    JobPosting,
    Persona,
    Education,
    TargetJob,
    ContentAsset,
    Skill,
    StyleMarker,
    AntiPattern,
    Trait,
    Value,
    Constraint,
    CareerStage,
    LearningSignal,
    SignalLayer,
    EventLog,
)


class TestJobPosting:
    def test_round_trip(self):
        data = {
            "source": "사람인",
            "url": "https://example.com/job/1",
            "title": "AI 엔지니어",
            "company": "(주)테스트",
            "skills_required": ["Python", "PyTorch"],
            "posted_date": "2026-05-30",
            "year": 2026,
            "month": 5,
            "day": 30,
        }
        job = JobPosting(**data)
        assert job.model_dump()["title"] == "AI 엔지니어"

    def test_extra_field_forbidden(self):
        with pytest.raises(ValidationError):
            JobPosting(source="사람인", url="https://x.com", title="AI", company="A", unknown_field="X")

    def test_optional_defaults(self):
        job = JobPosting(source="워크넷", url="https://x.com", title="개발자", company="B")
        assert job.location is None
        assert job.skills_required == []


class TestPersona:
    def _make_persona(self):
        return Persona(
            user_id="user_001",
            name="어창선",
            birth="1997-01-01",
            education=[Education(school="한국대", major="AI", degree="학사", graduated="2022-02-28")],
            target_jobs=[TargetJob(industry="IT", job_role="AI 엔지니어", priority=1)],
            content_assets=[ContentAsset(
                title="RAG 프로젝트",
                description="RAG 시스템 구축",
                context="인턴 기간 중 수행",
                tags=["RAG", "Python"],
            )],
            skills=[Skill(skill_type="기술", name="Python", ai_relevance=0.9)],
            style_markers=[StyleMarker(
                marker_name="구체적 수치",
                description="수치로 성과를 표현",
                examples=["정확도 92% 달성"],
                weight=1.2,
            )],
            anti_patterns=[AntiPattern(
                pattern_name="GPT 투명체",
                description="분석했습니다 등 AI 투명 표현",
                examples=["분석했습니다", "살펴보았습니다"],
            )],
            traits=[Trait(trait_type="강점", trait="문제 분해력", evidence="인턴 프로젝트")],
            values=[Value(value_text="기술로 사람을 돕는다")],
            constraints=[Constraint(constraint_type="위치", value="서울 마곡", is_hard=True)],
            career_history=[CareerStage(stage="신입", changed_date="2026-01-01")],
        )

    def test_round_trip(self):
        p = self._make_persona()
        dumped = p.model_dump()
        restored = Persona(**dumped)
        assert restored.name == "어창선"

    def test_extra_field_forbidden(self):
        with pytest.raises(ValidationError):
            Persona(user_id="u1", name="테스트", unknown="X")

    def test_user_id_required(self):
        with pytest.raises(ValidationError):
            Persona(name="테스트")


class TestLearningSignal:
    def test_round_trip(self):
        signal = LearningSignal(
            user_id="user_001",
            layer=SignalLayer.B,
            signal_type="자소서_승인",
            payload={"draft_id": "d001", "score": 0.85},
            source_module="validator",
            timestamp="2026-05-30T12:00:00",
            year=2026,
            month=5,
            day=30,
        )
        assert signal.layer == SignalLayer.B
        assert signal.model_dump()["layer"] == "B"

    def test_all_layers(self):
        for layer in SignalLayer:
            s = LearningSignal(user_id="u1", layer=layer, signal_type="test")
            assert s.layer == layer

    def test_extra_field_forbidden(self):
        with pytest.raises(ValidationError):
            LearningSignal(user_id="u1", layer=SignalLayer.A, signal_type="t", bad_field=1)


class TestEventLog:
    def test_round_trip(self):
        log = EventLog(
            user_id="user_001",
            event_type="persona_updated",
            event_data={"section": "skills", "added": "Python"},
            timestamp="2026-05-30T09:00:00",
            year=2026,
            month=5,
            day=30,
        )
        assert log.event_type == "persona_updated"

    def test_extra_field_forbidden(self):
        with pytest.raises(ValidationError):
            EventLog(user_id="u1", event_type="test", surprise="!")
