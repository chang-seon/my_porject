"""콘텐츠·구조·문체 3-풀 로드 — 자소서 생성의 사실 기반."""
from __future__ import annotations

from pathlib import Path

from job_agent.shared.db.repositories.persona_repo import get_persona


def load_content_pool(user_id: str, db_path: Path | None = None) -> dict:
    """페르소나 DB에서 3-풀(콘텐츠/구조/문체)을 로드한다.

    반환:
      content_pool: 경험·성과 사실 목록
      style_markers: 문체 카드
      anti_patterns: 안티패턴
      persona_summary: LLM 프롬프트용 요약 텍스트
    """
    try:
        kwargs = {"db_path": db_path} if db_path else {}
        persona = get_persona(user_id, **kwargs)

        if persona is None:
            return {
                "결과": "실패",
                "이유": f"페르소나 없음: user_id={user_id}",
            }

        content_pool = _build_content_pool(persona)
        style_markers = _build_style_markers(persona)
        anti_patterns = _build_anti_patterns(persona)
        persona_summary = _build_persona_summary(persona)

        return {
            "결과": "성공",
            "content_pool": content_pool,
            "style_markers": style_markers,
            "anti_patterns": anti_patterns,
            "persona_summary": persona_summary,
        }
    except Exception as e:
        return {"결과": "실패", "이유": str(e)}


def _build_content_pool(persona) -> list[str]:
    """경험·성과 사실을 텍스트 목록으로 변환한다."""
    pool: list[str] = []

    for edu in (persona.educations or []):
        pool.append(f"학력: {edu.school} {edu.major} ({edu.degree})")

    for skill in (persona.skills or []):
        pool.append(f"스킬: {skill.name} (수준: {skill.level})")

    for asset in (persona.content_assets or []):
        pool.append(f"콘텐츠: {asset.title} — {asset.summary or ''}")

    for career in (persona.career_history or []):
        pool.append(f"경력: {career.company} {career.role} ({career.start_date}~{career.end_date or '현재'})")

    return pool


def _build_style_markers(persona) -> list[str]:
    markers: list[str] = []
    for sm in (persona.style_markers or []):
        markers.append(f"{sm.marker_id}: {sm.description} (예시: {sm.example or '없음'})")
    return markers


def _build_anti_patterns(persona) -> list[str]:
    aps: list[str] = []
    for ap in (persona.anti_patterns or []):
        aps.append(f"{ap.pattern_id}: {ap.description}")
    return aps


def _build_persona_summary(persona) -> str:
    lines: list[str] = []
    if persona.name:
        lines.append(f"이름: {persona.name}")
    for tj in (persona.target_jobs or []):
        lines.append(f"목표직무: {tj.job_role} ({tj.industry})")
    for edu in (persona.educations or []):
        lines.append(f"학력: {edu.school} {edu.major}")
    return "\n".join(lines)
