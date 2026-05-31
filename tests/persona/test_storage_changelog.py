import pytest
from job_agent.shared.db.connection import init_db
from job_agent.features.persona.internal.storage import save_persona, load_persona
from job_agent.features.persona.internal.changelog import record_change, get_changelog
from job_agent.shared.schemas.persona import Persona, TargetJob, Skill


@pytest.fixture
def tmp_db(tmp_path):
    db_path = tmp_path / "test.db"
    init_db(db_path)
    return db_path


def _make_persona(user_id="u001"):
    return Persona(
        user_id=user_id, name="어창선",
        target_jobs=[TargetJob(industry="IT", job_role="AI엔지니어", priority=1)],
        skills=[Skill(skill_type="기술", name="Python", ai_relevance=0.9)],
    )


class TestStorage:
    def test_save_and_load(self, tmp_db):
        p = _make_persona()
        assert save_persona(p, db_path=tmp_db)["결과"] == "성공"
        result = load_persona("u001", db_path=tmp_db)
        assert result["결과"] == "성공"
        assert result["persona"]["name"] == "어창선"

    def test_load_nonexistent(self, tmp_db):
        result = load_persona("없는유저", db_path=tmp_db)
        assert result["결과"] == "실패"
        assert "없음" in result["이유"]

    def test_save_twice_updates(self, tmp_db):
        p = _make_persona()
        save_persona(p, db_path=tmp_db)
        p.name = "어창선_수정"
        save_persona(p, db_path=tmp_db)
        result = load_persona("u001", db_path=tmp_db)
        assert result["persona"]["name"] == "어창선_수정"


class TestChangelog:
    def test_record_and_get(self, tmp_db):
        result = record_change(
            user_id="u001", section="skills",
            before={"skills": []}, after={"skills": ["Python"]},
            reason="Python 추가", trigger="manual", db_path=tmp_db,
        )
        assert result["결과"] == "성공"
        history = get_changelog("u001", db_path=tmp_db)
        assert history["결과"] == "성공"
        assert len(history["history"]) == 1
        assert history["history"][0]["section"] == "skills"

    def test_filter_by_section(self, tmp_db):
        record_change("u001", "skills", {}, {"a": 1}, db_path=tmp_db)
        record_change("u001", "traits", {}, {"b": 2}, db_path=tmp_db)
        skills_only = get_changelog("u001", section="skills", db_path=tmp_db)
        assert all(r["section"] == "skills" for r in skills_only["history"])
