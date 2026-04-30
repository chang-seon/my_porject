"""
Orchestrator: 전체 워크플로우를 비동기로 관장하는 메인 엔진.

실행 순서:
  Phase 0 — 역할 경매 (디렉터 조율)
  Phase 1 — 기획 (기획자 요원)
  Phase 2 — 작성 (작가 요원)
  Phase 3 — 검토 (검토관 요원, REJECT 시 재작성 최대 3회)

10초 골든 타임:
  각 단계 직후 asyncio.wait_for로 10초 대기.
  창선님이 입력하면 즉시 전역 이력에 주입하여 다음 에이전트 계획을 수정한다.
  이것이 'User-in-the-Loop'의 핵심이다.
"""
from __future__ import annotations

import asyncio
import logging
import sys
from typing import Any

from agents.director import Director
from agents.engine import GeminiEngine
from utils.discord import DiscordReporter

logger = logging.getLogger(__name__)

INTERRUPT_TIMEOUT: float = 10.0   # 골든 타임 대기 시간(초)
MAX_REVIEW_RETRIES: int = 3        # REJECT 시 최대 재작성 횟수


class Orchestrator:
    """
    비동기 워크플로우 오케스트레이터.
    GeminiEngine(단일 API)을 공유 자원으로 사용하며
    Director가 전체 흐름을 관제한다.
    """

    def __init__(
        self,
        engine: GeminiEngine,
        director: Director,
        discord: DiscordReporter,
    ) -> None:
        self.engine = engine
        self.director = director
        self.discord = discord

    # ─── 골든 타임 인터럽트 ──────────────────────────────────────

    async def _golden_time(self, context_hint: str = "") -> str | None:
        """
        10초 골든 타임: 에이전트 발화 직후 창선님의 개입을 기다린다.

        입력: context_hint — 현재 단계 힌트 (콘솔 안내 메시지용)
        출력: 창선님 입력 텍스트 또는 None (타임아웃)

        왜 asyncio.wait_for인가?
          블로킹 input()을 run_in_executor로 비동기화하고
          wait_for로 타임아웃을 걸어, 워크플로우가 멈추지 않게 한다.
        """
        hint = f"[{context_hint}] " if context_hint else ""
        print(f"\n{hint}[골든 타임 10초] 지시 사항이 있으면 입력하세요 (없으면 자동 진행): ", end="", flush=True)

        try:
            loop = asyncio.get_event_loop()
            user_input: str = await asyncio.wait_for(
                loop.run_in_executor(None, sys.stdin.readline),
                timeout=INTERRUPT_TIMEOUT,
            )
            stripped = user_input.strip()
            if stripped:
                print(f"\n[사령관 개입] '{stripped}' — 즉시 적용합니다.")
                return stripped
            return None
        except asyncio.TimeoutError:
            print("\n[자동 진행]")
            return None
        except Exception as exc:
            logger.error(f"골든 타임 오류: {exc}")
            return None

    async def _apply_interrupt(self, user_input: str, phase: str) -> None:
        """
        창선님 입력을 전역 이력에 주입하고 Discord에 알린다.
        이후 호출되는 모든 에이전트가 이 지시를 컨텍스트로 받는다.
        """
        self.engine.add_user_input(user_input)
        await self.discord.send_interrupt(phase, user_input)
        logger.info(f"[{phase}] 사령관 인터럽트 적용: {user_input[:60]}")

    # ─── 메인 워크플로우 ─────────────────────────────────────────

    async def run(self, mission: str) -> str:
        """
        전체 워크플로우 실행.

        입력: mission — 창선님이 하달한 미션
        출력: 최종 결과물 텍스트
        """
        logger.info(f"워크플로우 시작: {mission[:60]}")
        self.engine.reset_session()
        strategy_ctx = self.director.get_strategy_context()

        # 미션을 전역 이력에 등록 — 모든 에이전트가 미션을 인지
        self.engine.add_user_input(f"미션: {mission}")

        try:
            # ── Phase 0: 역할 경매 ──────────────────────────────
            await self.discord.send_phase("Phase 0: 역할 경매", mission, "디렉터")
            logger.info("Phase 0: 역할 경매 시작")

            proposals = await self.director.run_role_auction(mission)
            final_plan = proposals.get("final_plan", "")

            await self.discord.send_agent(
                agent="디렉터",
                phase="Phase 0",
                content=f"**역할 경매 완료 — 최종 작전 계획:**\n{final_plan}",
            )

            interrupt = await self._golden_time("Phase 0 완료")
            if interrupt:
                await self._apply_interrupt(interrupt, "Phase 0")

            # ── Phase 1: 기획 ────────────────────────────────────
            await self.discord.send_phase("Phase 1: 기획", mission, "기획자")
            logger.info("Phase 1: 기획 시작")

            plan_resp = await self.engine.call_agent(
                agent_name="기획자",
                task=(
                    f"미션: {mission}\n\n"
                    f"작전 계획:\n{final_plan}\n\n"
                    "위 계획을 바탕으로 구체적인 실행 기획안을 작성하라."
                ),
                persona_key="기획자",
                extra_context=strategy_ctx,
            )
            await self.discord.send_agent("기획자", "Phase 1", plan_resp.content)

            interrupt = await self._golden_time("Phase 1 완료 — 기획 확인")
            if interrupt:
                await self._apply_interrupt(interrupt, "Phase 1")

            # ── Phase 2: 작성 ────────────────────────────────────
            await self.discord.send_phase("Phase 2: 작성", mission, "작가")
            logger.info("Phase 2: 작성 시작")

            write_resp = await self.engine.call_agent(
                agent_name="작가",
                task=(
                    f"미션: {mission}\n\n"
                    "앞선 기획자의 기획안을 바탕으로 완성도 높은 최종 결과물을 작성하라.\n"
                    "기획 내용을 충실히 반영하되, 독자가 공감할 수 있는 문체로 완성하라."
                ),
                persona_key="작가",
                extra_context=strategy_ctx,
            )
            await self.discord.send_agent("작가", "Phase 2", write_resp.content)

            interrupt = await self._golden_time("Phase 2 완료 — 초안 확인")
            if interrupt:
                await self._apply_interrupt(interrupt, "Phase 2")

            # ── Phase 3: 품질 검토 (REJECT 시 재작성 루프) ───────
            await self.discord.send_phase("Phase 3: 품질 검토", mission, "검토관")
            logger.info("Phase 3: 품질 검토 시작")

            current_draft = write_resp.content
            final_output = current_draft

            for attempt in range(1, MAX_REVIEW_RETRIES + 1):
                review_resp = await self.engine.call_agent(
                    agent_name=f"검토관(시도{attempt})",
                    task=(
                        f"아래 결과물을 검토하고 반드시 PASS 또는 REJECT로 판정하라:\n\n"
                        f"{current_draft}"
                    ),
                    persona_key="검토관",
                )
                await self.discord.send_agent(
                    f"검토관", f"Phase 3 (시도 {attempt})", review_resp.content
                )

                if "REJECT" not in review_resp.content.upper():
                    logger.info(f"Phase 3: PASS 판정 ({attempt}회 시도)")
                    final_output = current_draft
                    break

                if attempt >= MAX_REVIEW_RETRIES:
                    logger.warning("최대 재작성 횟수 초과 — 현재 초안으로 확정")
                    break

                # REJECT: 작가에게 재작성 요청
                reject_reason = review_resp.content
                logger.info(f"Phase 3: REJECT — 재작성 요청 ({attempt}회)")
                await self.discord.send_phase(
                    f"Phase 3 재작성 ({attempt}회)", mission, "작가"
                )

                revise_resp = await self.engine.call_agent(
                    agent_name=f"작가(재작성{attempt})",
                    task=(
                        f"검토관의 REJECT 사유를 반영하여 결과물을 수정하라:\n\n"
                        f"[REJECT 사유]\n{reject_reason}\n\n"
                        f"[현재 초안]\n{current_draft}"
                    ),
                    persona_key="작가",
                )
                if revise_resp.success:
                    current_draft = revise_resp.content
                    final_output = current_draft
                    await self.discord.send_agent(
                        "작가", f"Phase 3 재작성 {attempt}", revise_resp.content
                    )

                interrupt = await self._golden_time(f"검토 {attempt}회차")
                if interrupt:
                    await self._apply_interrupt(interrupt, f"Phase 3-{attempt}")

            # ── 최종 보고 및 학습 ────────────────────────────────
            await self.discord.send_final(final_output)

            # 창선님 선호 스타일 학습 (비동기로 백그라운드 처리)
            asyncio.create_task(
                self.director.record_session_preference(mission, final_output)
            )

            logger.info("워크플로우 완료")
            return final_output

        except Exception as exc:
            logger.error(f"워크플로우 오류: {exc}", exc_info=True)
            await self.discord.send_error(str(exc))
            return f"[오류] {exc}"
