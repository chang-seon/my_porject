"""
Director: 전략 사령부의 관제탑.

역할:
  1. Phase 0 역할 경매 (Role Auction)
     - 기획자·작가·검토관 페르소나가 각자 "이 미션에서 나는 무엇을 하겠다"고 제안
     - 디렉터가 제안을 종합하여 최종 역할 배정 확정
  2. 경험 축적 (Strategy Note)
     - 매 세션 종료 후 창선님이 선호한 스타일을 strategy_note.json에 저장
     - 다음 실행 시 해당 내용을 컨텍스트로 주입하여 지속 개선
"""
from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from agents.engine import AgentResponse, GeminiEngine

logger = logging.getLogger(__name__)

STRATEGY_NOTE_PATH = Path("memory/strategy_note.json")

# 역할 경매에 참여하는 페르소나 목록
AUCTION_PERSONAS: list[dict[str, str]] = [
    {"key": "기획자", "name": "기획자 요원"},
    {"key": "작가",   "name": "작가 요원"},
    {"key": "검토관", "name": "검토관 요원"},
]


class Director:
    """
    전체 워크플로우를 조율하는 관제탑.
    GeminiEngine을 통해 디렉터 페르소나로 동작하며,
    역할 경매 및 경험 축적을 담당한다.
    """

    def __init__(self, engine: GeminiEngine) -> None:
        """입력: engine — 공유 GeminiEngine 인스턴스"""
        self.engine = engine
        self._strategy_note: dict[str, Any] = self._load_strategy_note()

    # ─── 전략 노트 입출력 ────────────────────────────────────────

    def _load_strategy_note(self) -> dict[str, Any]:
        """
        strategy_note.json 로드.
        파일이 없거나 손상된 경우 빈 구조 반환.
        """
        try:
            if STRATEGY_NOTE_PATH.exists():
                with open(STRATEGY_NOTE_PATH, "r", encoding="utf-8") as f:
                    data: dict[str, Any] = json.load(f)
                logger.info(
                    f"전략 노트 로드: {len(data.get('sessions', []))}개 세션 이력"
                )
                return data
            return {"sessions": [], "style_preferences": [], "last_updated": ""}
        except (json.JSONDecodeError, IOError) as exc:
            logger.error(f"전략 노트 로드 실패: {exc}")
            return {"sessions": [], "style_preferences": [], "last_updated": ""}

    def _save_strategy_note(self) -> None:
        """현재 전략 노트를 strategy_note.json에 저장."""
        try:
            STRATEGY_NOTE_PATH.parent.mkdir(parents=True, exist_ok=True)
            self._strategy_note["last_updated"] = datetime.now().isoformat()
            with open(STRATEGY_NOTE_PATH, "w", encoding="utf-8") as f:
                json.dump(self._strategy_note, f, ensure_ascii=False, indent=2)
            logger.info("전략 노트 저장 완료")
        except IOError as exc:
            logger.error(f"전략 노트 저장 실패: {exc}")

    def get_strategy_context(self) -> str:
        """
        이전 세션에서 학습한 창선님의 선호 스타일을 컨텍스트 텍스트로 반환.
        다음 세션 시작 시 모든 에이전트에게 주입된다.
        """
        prefs = self._strategy_note.get("style_preferences", [])
        if not prefs:
            return ""
        # 최근 5개 선호 사항만 주입 (과거 정보 과부하 방지)
        recent = prefs[-5:]
        lines = ["[창선님 선호 스타일 — 이전 세션에서 학습]"]
        lines.extend(f"  • {p}" for p in recent)
        return "\n".join(lines)

    async def record_session_preference(self, mission: str, final_output: str) -> None:
        """
        세션 종료 후 디렉터가 최종 결과물을 분석하여
        창선님이 선호할 스타일 패턴을 추출하고 저장.

        입력:
            mission      — 이번 세션의 미션 내용
            final_output — 최종 결과물 텍스트
        """
        summarize_task = (
            f"다음 미션과 최종 결과물을 분석하여, "
            f"창선 사령관이 선호하는 글쓰기 스타일·구조·톤을 한 문장으로 요약하라.\n\n"
            f"미션: {mission[:200]}\n\n"
            f"결과물 요약: {final_output[:500]}"
        )

        response = await self.engine.call_agent(
            agent_name="디렉터(학습)",
            task=summarize_task,
            persona_key="디렉터",
            inject_history=False,  # 학습 요약은 현재 이력 없이 독립 분석
        )

        if response.success and response.content:
            self._strategy_note["style_preferences"].append(response.content)
            # 최대 20개 유지 (오래된 것은 자동 삭제)
            self._strategy_note["style_preferences"] = (
                self._strategy_note["style_preferences"][-20:]
            )
            session_record = {
                "timestamp": datetime.now().isoformat(),
                "mission":   mission[:200],
                "preference": response.content,
            }
            self._strategy_note["sessions"].append(session_record)
            self._save_strategy_note()
            logger.info(f"선호 스타일 학습 완료: {response.content[:80]}")

    # ─── Phase 0: 역할 경매 ─────────────────────────────────────

    async def run_role_auction(self, mission: str) -> dict[str, str]:
        """
        Phase 0 역할 경매: 각 페르소나가 미션을 보고 자신의 역할을 제안한다.

        입력: mission — 이번 세션의 미션 내용
        출력: {"기획자": "제안 내용", "작가": "제안 내용", "검토관": "제안 내용",
               "final_plan": "디렉터 확정 계획"}

        왜 역할 경매인가?
          고정된 역할 배정보다 미션에 따라 각 에이전트가
          스스로 최적 역할을 제안하면 더 창의적이고 맥락에 맞는 결과가 나온다.
        """
        logger.info("Phase 0: 역할 경매 시작")
        proposals: dict[str, str] = {}
        strategy_ctx = self.get_strategy_context()

        # 각 페르소나가 독립적으로 역할 제안 (이력 없이 — 편향 방지)
        for persona in AUCTION_PERSONAS:
            auction_task = (
                f"미션: {mission}\n\n"
                "당신의 전문성을 바탕으로 이 미션에서 당신이 구체적으로\n"
                "무엇을 담당할지 2-3문장으로 제안하라.\n"
                "본인 역할의 핵심 가치와 접근 방식을 포함하라."
            )
            response = await self.engine.call_agent(
                agent_name=f"{persona['name']}(경매)",
                task=auction_task,
                persona_key=persona["key"],
                extra_context=strategy_ctx,
                inject_history=False,  # 경매는 독립 판단 — 타 요원 의견 배제
            )
            if response.success:
                proposals[persona["key"]] = response.content
                logger.info(f"[{persona['name']}] 역할 제안 완료")

        # 디렉터가 제안들을 종합하여 최종 계획 확정
        synthesis_task = (
            f"미션: {mission}\n\n"
            "아래 요원들의 역할 제안을 검토하고 최종 작전 계획을 수립하라:\n\n"
            + "\n".join(
                f"[{k} 제안]\n{v}" for k, v in proposals.items()
            )
            + "\n\n최종 계획은 각 요원의 담당 범위와 협업 순서를 명확히 해야 한다."
        )
        final = await self.engine.call_agent(
            agent_name="디렉터",
            task=synthesis_task,
            persona_key="디렉터",
            extra_context=strategy_ctx,
            inject_history=False,
        )

        proposals["final_plan"] = final.content if final.success else "기본 계획 적용"
        logger.info("Phase 0: 역할 경매 및 계획 확정 완료")
        return proposals
