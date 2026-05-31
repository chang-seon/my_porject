import pytest
import tempfile
from pathlib import Path

from job_agent.shared.db.connection import init_db
from job_agent.shared.db.repositories.persona_repo import get_persona, upsert_persona
from job_agent.shared.schemas.persona import (
    Persona, Education, TargetJob, ContentAsset, Skill,
    StyleMarker, AntiPattern, Trait, Value, Constraint, CareerStage,
)


@pytest.fixture
def tmp_db(tmp_path):
    db_path = tmp_path / "test_agent.db"
    init_db(db_path)
    return db_path


def _make_full_persona() -> Persona:
    return Persona(
        user_id="user_test_001",
        name="어창선",
        birth="1997-01-01",
        address="서울 마곡",
        career_stage="신입",
        education=[Education(school="한국대", major="AI", degree="학사", graduated="2022-02-28")],
        target_jobs=[TargetJob(industry="IT", job_role="AI 엔지니어", priority=1)],
        content_assets=[ContentAsset(
            title="RAG 프로젝트", description="RAG 구축",
            context="인턴 기간", tags=["RAG", "Python"], is_killer=True, ai_relevance=0.9,
        )],
        skills=[Skill(skill_type="기술", name="Python", ai_relevance=0.9, status="보유")],
        style_markers=[StyleMarker(
            marker_name="구체적 수치", description="수치 표현",
            examples=["정확도 92% 달성"], weight=1.2,
        )],
        anti_patterns=[AntiPattern(
            pattern_name="GPT 투명체", description="AI 투명 표현",
            examples=["분석했습니다"],
        )],
        traits=[Trait(trait_type="강점", trait="문제 분해력", evidence="인턴 프로젝트")],
        values=[Value(value_text="기술로 사람을 돕는다")],
        constraints=[Constraint(constraint_type="위치", value="서울 마곡", is_hard=True)],
        career_history=[CareerStage(stage="신입", changed_date="2026-01-01")],
    )


class TestDbRoundtrip:
    def test_upsert_and_get(self, tmp_db):
        persona = _make_full_persona()
        result = upsert_persona(persona, db_path=tmp_db)
        assert result["결과"] == "성공"

        loaded = get_persona("user_test_001", db_path=tmp_db)
        assert loaded is not None
        assert loaded.name == "어창선"
        assert loaded.birth == "1997-01-01"
        assert len(loaded.education) == 1
        assert loaded.education[0].school == "한국대"
        assert len(loaded.target_jobs) == 1
        assert loaded.target_jobs[0].job_role == "AI 엔지니어"
        assert len(loaded.content_assets) == 1
        assert loaded.content_assets[0].tags == ["RAG", "Python"]
        assert loaded.content_assets[0].is_killer is True
        assert len(loaded.skills) == 1
        assert len(loaded.style_markers) == 1
        assert loaded.style_markers[0].examples == ["정확도 92% 달성"]
        assert len(loaded.anti_patterns) == 1
        assert len(loaded.traits) == 1
        assert len(loaded.values) == 1
        assert len(loaded.constraints) == 1
        assert loaded.constraints[0].is_hard is True
        assert len(loaded.career_history) == 1

    def test_upsert_updates_existing(self, tmp_db):
        persona = _make_full_persona()
        upsert_persona(persona, db_path=tmp_db)

        updated = _make_full_persona()
        updated.name = "어창선_업데이트"
        updated.skills = []
        upsert_persona(updated, db_path=tmp_db)

        loaded = get_persona("user_test_001", db_path=tmp_db)
        assert loaded.name == "어창선_업데이트"
        assert len(loaded.skills) == 0

    def test_get_nonexistent_returns_none(self, tmp_db):
        result = get_persona("없는_유저", db_path=tmp_db)
        assert result is None


class TestMigrationIdempotent:
    def test_double_init(self, tmp_path):
        db_path = tmp_path / "idempotent.db"
        init_db(db_path)
        init_db(db_path)  # 두 번 실행해도 오류 없어야 함
        assert db_path.exists()
