from __future__ import annotations
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from job_agent.shared.schemas.persona import (
    Persona, Education, TargetJob, ContentAsset, Skill,
    StyleMarker, AntiPattern, Trait, Value, Constraint, CareerStage,
)
from job_agent.shared.db.connection import get_connection, _DEFAULT_DB_PATH


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_persona(user_id: str, db_path: Path = _DEFAULT_DB_PATH) -> Optional[Persona]:
    conn = get_connection(db_path)
    try:
        row = conn.execute(
            "SELECT * FROM personas WHERE user_id = ?", (user_id,)
        ).fetchone()
        if row is None:
            return None

        def fetch(table: str) -> list[sqlite3.Row]:
            return conn.execute(
                f"SELECT * FROM {table} WHERE user_id = ? ORDER BY id", (user_id,)
            ).fetchall()

        educations = [
            Education(school=r["school"], major=r["major"],
                      degree=r["degree"], graduated=r["graduated"])
            for r in fetch("persona_educations")
        ]
        target_jobs = [
            TargetJob(industry=r["industry"], job_role=r["job_role"], priority=r["priority"])
            for r in fetch("persona_target_jobs")
        ]
        content_assets = [
            ContentAsset(
                title=r["title"], description=r["description"], context=r["context"],
                tags=json.loads(r["tags"]), is_killer=bool(r["is_killer"]),
                ai_relevance=r["ai_relevance"], usage_count=r["usage_count"],
            )
            for r in fetch("persona_content_assets")
        ]
        skills = [
            Skill(skill_type=r["skill_type"], name=r["name"], acquired_date=r["acquired_date"],
                  ai_relevance=r["ai_relevance"], status=r["status"])
            for r in fetch("persona_skills")
        ]
        style_markers = [
            StyleMarker(marker_name=r["marker_name"], description=r["description"],
                        examples=json.loads(r["examples"]), weight=r["weight"])
            for r in fetch("persona_style_markers")
        ]
        anti_patterns = [
            AntiPattern(pattern_name=r["pattern_name"], description=r["description"],
                        examples=json.loads(r["examples"]))
            for r in fetch("persona_anti_patterns")
        ]
        traits = [
            Trait(trait_type=r["trait_type"], trait=r["trait"],
                  evidence=r["evidence"], self_aware=bool(r["self_aware"]))
            for r in fetch("persona_traits")
        ]
        values = [
            Value(value_text=r["value_text"], source=r["source"])
            for r in fetch("persona_values")
        ]
        constraints = [
            Constraint(constraint_type=r["constraint_type"], value=r["value"],
                       is_hard=bool(r["is_hard"]), threshold_dynamic=r["threshold_dynamic"])
            for r in fetch("persona_constraints")
        ]
        career_history = [
            CareerStage(stage=r["stage"], changed_date=r["changed_date"])
            for r in fetch("persona_career_history")
        ]

        return Persona(
            user_id=user_id,
            name=row["name"], birth=row["birth"], address=row["address"],
            disability=row["disability"], career_stage=row["career_stage"],
            education=educations, target_jobs=target_jobs,
            content_assets=content_assets, skills=skills,
            style_markers=style_markers, anti_patterns=anti_patterns,
            traits=traits, values=values, constraints=constraints,
            career_history=career_history,
        )
    except Exception as e:
        return None
    finally:
        conn.close()


def upsert_persona(persona: Persona, db_path: Path = _DEFAULT_DB_PATH) -> dict:
    conn = get_connection(db_path)
    try:
        with conn:
            now = _now_iso()
            existing = conn.execute(
                "SELECT id FROM personas WHERE user_id = ?", (persona.user_id,)
            ).fetchone()

            if existing:
                conn.execute(
                    """UPDATE personas SET name=?, birth=?, address=?, disability=?,
                       career_stage=?, updated_at=? WHERE user_id=?""",
                    (persona.name, persona.birth, persona.address, persona.disability,
                     persona.career_stage, now, persona.user_id),
                )
            else:
                conn.execute(
                    """INSERT INTO personas (user_id, name, birth, address, disability,
                       career_stage, created_at, updated_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (persona.user_id, persona.name, persona.birth, persona.address,
                     persona.disability, persona.career_stage, now, now),
                )

            # 자식 테이블 전체 교체
            child_tables = [
                "persona_educations", "persona_target_jobs", "persona_content_assets",
                "persona_skills", "persona_style_markers", "persona_anti_patterns",
                "persona_traits", "persona_values", "persona_constraints",
                "persona_career_history",
            ]
            for t in child_tables:
                conn.execute(f"DELETE FROM {t} WHERE user_id = ?", (persona.user_id,))

            uid = persona.user_id

            for e in persona.education:
                conn.execute(
                    "INSERT INTO persona_educations (user_id,school,major,degree,graduated) VALUES (?,?,?,?,?)",
                    (uid, e.school, e.major, e.degree, e.graduated),
                )
            for j in persona.target_jobs:
                conn.execute(
                    "INSERT INTO persona_target_jobs (user_id,industry,job_role,priority) VALUES (?,?,?,?)",
                    (uid, j.industry, j.job_role, j.priority),
                )
            for c in persona.content_assets:
                conn.execute(
                    "INSERT INTO persona_content_assets (user_id,title,description,context,tags,is_killer,ai_relevance,usage_count) VALUES (?,?,?,?,?,?,?,?)",
                    (uid, c.title, c.description, c.context, json.dumps(c.tags, ensure_ascii=False),
                     int(c.is_killer), c.ai_relevance, c.usage_count),
                )
            for s in persona.skills:
                conn.execute(
                    "INSERT INTO persona_skills (user_id,skill_type,name,acquired_date,ai_relevance,status) VALUES (?,?,?,?,?,?)",
                    (uid, s.skill_type, s.name, s.acquired_date, s.ai_relevance, s.status),
                )
            for m in persona.style_markers:
                conn.execute(
                    "INSERT INTO persona_style_markers (user_id,marker_name,description,examples,weight) VALUES (?,?,?,?,?)",
                    (uid, m.marker_name, m.description, json.dumps(m.examples, ensure_ascii=False), m.weight),
                )
            for a in persona.anti_patterns:
                conn.execute(
                    "INSERT INTO persona_anti_patterns (user_id,pattern_name,description,examples) VALUES (?,?,?,?)",
                    (uid, a.pattern_name, a.description, json.dumps(a.examples, ensure_ascii=False)),
                )
            for t in persona.traits:
                conn.execute(
                    "INSERT INTO persona_traits (user_id,trait_type,trait,evidence,self_aware) VALUES (?,?,?,?,?)",
                    (uid, t.trait_type, t.trait, t.evidence, int(t.self_aware)),
                )
            for v in persona.values:
                conn.execute(
                    "INSERT INTO persona_values (user_id,value_text,source) VALUES (?,?,?)",
                    (uid, v.value_text, v.source),
                )
            for c in persona.constraints:
                conn.execute(
                    "INSERT INTO persona_constraints (user_id,constraint_type,value,is_hard,threshold_dynamic) VALUES (?,?,?,?,?)",
                    (uid, c.constraint_type, c.value, int(c.is_hard), c.threshold_dynamic),
                )
            for ch in persona.career_history:
                conn.execute(
                    "INSERT INTO persona_career_history (user_id,stage,changed_date) VALUES (?,?,?)",
                    (uid, ch.stage, ch.changed_date),
                )

        return {"결과": "성공", "user_id": persona.user_id}
    except Exception as e:
        return {"결과": "실패", "이유": str(e)}
    finally:
        conn.close()
