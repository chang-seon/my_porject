"""
DiscordReporter: 여러 명이 실시간 대화하는 효과를 내는 멀티 페르소나 Webhook 핸들러.

각 에이전트마다 다른 username과 avatar_url을 적용하여
Discord 채널에서 마치 여러 사람이 대화하는 것처럼 보이게 한다.

왜 단일 Webhook URL로 다중 페르소나가 가능한가?
  Discord Webhook은 요청마다 username/avatar_url을 오버라이드할 수 있다.
  따라서 하나의 URL로 여러 봇 캐릭터를 흉내낼 수 있다.
"""
from __future__ import annotations

import logging
from typing import Any

import aiohttp

logger = logging.getLogger(__name__)

# ─── 페르소나별 프로필 정의 ────────────────────────────────────────────
# avatar_url: 무료 공개 아바타 이미지 (DiceBear API — 항상 유효)
PERSONA_PROFILES: dict[str, dict[str, str]] = {
    "디렉터": {
        "username":   "사령부 보좌관",
        "avatar_url": "https://api.dicebear.com/7.x/bottts/svg?seed=director&backgroundColor=9b59b6",
    },
    "기획자": {
        "username":   "수석 기획자",
        "avatar_url": "https://api.dicebear.com/7.x/bottts/svg?seed=planner&backgroundColor=3498db",
    },
    "작가": {
        "username":   "전문 작가",
        "avatar_url": "https://api.dicebear.com/7.x/bottts/svg?seed=writer&backgroundColor=2ecc71",
    },
    "검토관": {
        "username":   "품질 검토관",
        "avatar_url": "https://api.dicebear.com/7.x/bottts/svg?seed=reviewer&backgroundColor=e74c3c",
    },
    "시스템": {
        "username":   "사령부 시스템",
        "avatar_url": "https://api.dicebear.com/7.x/bottts/svg?seed=system&backgroundColor=95a5a6",
    },
}

# ─── Embed 색상 (Discord decimal) ─────────────────────────────────────
COLOR_MAP: dict[str, int] = {
    "디렉터":  0x9B59B6,   # 보라 — 사령부
    "기획자":  0x3498DB,   # 파랑 — 전략
    "작가":    0x2ECC71,   # 초록 — 창작
    "검토관":  0xE74C3C,   # 빨강 — 검토
    "시스템":  0x95A5A6,   # 회색 — 시스템
    "인터럽트": 0xF39C12,  # 주황 — 사령관 개입
    "완료":    0x1ABC9C,   # 청록 — 완료
    "오류":    0x7F8C8D,   # 어두운 회색 — 오류
}


def _get_profile(agent: str) -> dict[str, str]:
    """에이전트 이름에서 페르소나 프로필을 찾는다. 없으면 시스템 기본값 반환."""
    for key in PERSONA_PROFILES:
        if key in agent:
            return PERSONA_PROFILES[key]
    return PERSONA_PROFILES["시스템"]


def _get_color(agent: str) -> int:
    """에이전트 이름에서 Embed 색상을 찾는다."""
    for key in COLOR_MAP:
        if key in agent:
            return COLOR_MAP[key]
    return 0x95A5A6


class DiscordReporter:
    """
    aiohttp 기반 Discord Webhook 멀티 페르소나 핸들러.
    모든 전송 실패는 워크플로우를 중단하지 않고 로그만 남긴다.
    """

    def __init__(self, webhook_url: str) -> None:
        self.webhook_url = webhook_url
        self._session: aiohttp.ClientSession | None = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """aiohttp 세션 지연 초기화 (Lazy Init)."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def close(self) -> None:
        """세션 정리."""
        try:
            if self._session and not self._session.closed:
                await self._session.close()
        except Exception as exc:
            logger.error(f"Discord 세션 종료 오류: {exc}")

    async def _post(self, payload: dict[str, Any]) -> None:
        """
        Webhook에 페이로드를 POST 전송.
        URL이 없으면 콘솔에만 출력하고 반환한다.
        """
        if not self.webhook_url:
            return

        try:
            session = await self._get_session()
            async with session.post(
                self.webhook_url,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status not in (200, 204):
                    body = await resp.text()
                    logger.error(f"Discord 전송 실패 (HTTP {resp.status}): {body[:200]}")
        except Exception as exc:
            logger.error(f"Discord 전송 오류: {exc}")

    def _build_payload(
        self,
        agent: str,
        title: str,
        description: str,
        fields: list[dict[str, Any]] | None = None,
        footer: str = "",
    ) -> dict[str, Any]:
        """
        Rich Embed + 페르소나 프로필을 포함한 Discord Webhook 페이로드 생성.

        username, avatar_url을 에이전트별로 다르게 설정하는 것이
        '여러 명이 대화하는 효과'의 핵심이다.
        """
        profile = _get_profile(agent)
        embed: dict[str, Any] = {
            "title":       title[:256],
            "description": description[:2048] if description else "(내용 없음)",
            "color":       _get_color(agent),
        }
        if fields:
            embed["fields"] = fields[:25]  # Discord 필드 최대 25개 제한
        if footer:
            embed["footer"] = {"text": footer[:2048]}

        return {
            "username":   profile["username"],
            "avatar_url": profile["avatar_url"],
            "embeds":     [embed],
        }

    # ─── 공개 전송 메서드 ─────────────────────────────────────────

    async def send_phase(self, phase: str, mission: str, agent: str) -> None:
        """워크플로우 단계 전환을 알린다."""
        payload = self._build_payload(
            agent=agent,
            title=f">> {phase}",
            description=f"**미션**: {mission[:300]}",
            fields=[{"name": "담당", "value": _get_profile(agent)["username"], "inline": True}],
        )
        await self._post(payload)

    async def send_agent(self, agent: str, phase: str, content: str) -> None:
        """에이전트의 발화 내용을 Rich Embed로 전송한다."""
        payload = self._build_payload(
            agent=agent,
            title=f"[{_get_profile(agent)['username']}] {phase}",
            description=content[:2000],
            footer=f"Agentic AI | {phase}",
        )
        await self._post(payload)

    async def send_interrupt(self, phase: str, user_input: str) -> None:
        """창선님의 인터럽트(골든 타임 개입)를 알린다."""
        payload = self._build_payload(
            agent="인터럽트",
            title=">> 사령관 창선님 긴급 개입",
            description=(
                f"**단계**: {phase}\n"
                f"**지시 내용**: {user_input}\n\n"
                "모든 에이전트 컨텍스트에 즉시 반영됩니다."
            ),
        )
        payload["username"] = "창선 사령관"
        await self._post(payload)

    async def send_final(self, final_output: str) -> None:
        """최종 결과물을 전송한다."""
        payload = self._build_payload(
            agent="완료",
            title=">> 작전 완료 — 최종 결과물",
            description=final_output[:2000],
            footer="품질 검토 PASS",
        )
        payload["username"] = "사령부 보좌관"
        await self._post(payload)

    async def send_error(self, error_msg: str) -> None:
        """오류를 알린다."""
        payload = self._build_payload(
            agent="오류",
            title="[오류] 워크플로우 오류 발생",
            description=error_msg[:1000],
        )
        await self._post(payload)

    async def send_boot_report(self) -> None:
        """
        시스템 구축 완료 보고.
        디렉터 보좌관이 창선님께 준비 완료를 보고한다.
        """
        payload = self._build_payload(
            agent="디렉터",
            title=">> 사령부 구축 완료 — 전력 준비 완료",
            description=(
                "사령관 창선님, 영상에서 보신 그 '무료 멀티 에이전트 시스템'이 "
                "완벽히 이식되었습니다. 추가 비용 없이 요원들을 부려보십시오."
            ),
            fields=[
                {"name": "엔진",      "value": "Gemini 2.5 Flash (무료)",    "inline": True},
                {"name": "에이전트",  "value": "기획자 / 작가 / 검토관",      "inline": True},
                {"name": "통신 방식", "value": "바톤 터치 (Shared Memory)",   "inline": True},
                {"name": "골든 타임", "value": "10초 인터럽트 활성화",         "inline": True},
                {"name": "경험 축적", "value": "strategy_note.json 자동 저장", "inline": True},
                {"name": "비용",      "value": "무료 (Gemini Free Tier)",     "inline": True},
            ],
            footer="Agentic AI v3 — 바톤 터치 멀티에이전트 사령부",
        )
        await self._post(payload)
