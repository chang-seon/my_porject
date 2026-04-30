"""
GeminiEngine: 단일 Gemini 무료 API로 다중 에이전트를 구현하는 핵심 엔진.

━━━ 바톤 터치 통신 원리 ━━━
  Shared Memory   : 모든 에이전트의 발화를 global_chat_history에 순서대로 누적
  Context Injection: 다음 에이전트 호출 시 이전 발화 전체를 프롬프트에 포함
  Multi-Persona   : system_instruction 동적 교체로 하나의 모델이 여러 인격으로 동작
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
from __future__ import annotations

import asyncio
import logging
import os
import random
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from google import genai  # type: ignore  # 신규 SDK (google-genai)
from google.genai import types  # type: ignore

logger = logging.getLogger(__name__)

# 이 API 키에서 실제로 작동하는 최고 성능 무료 모델
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

# ─── 페르소나 정의 ─────────────────────────────────────────────────────
# 각 페르소나는 system_instruction으로 주입되어 모델의 '인격'을 결정한다.
PERSONAS: dict[str, str] = {
    "디렉터": (
        "당신은 다중 AI 에이전트 팀의 총괄 사령부 보좌관입니다.\n"
        "팀원들의 역할을 조율하고, 창선 사령관의 미션을 팀에 하달하며,\n"
        "최종 결과물의 방향을 결정합니다.\n"
        "항상 간결하고 권위 있는 한국어로 보고하십시오."
    ),
    "기획자": (
        "당신은 전략적 사고를 가진 수석 기획자입니다.\n"
        "주어진 미션을 분석하고 누가 무엇을 어떻게 할지 구체적인 실행 계획을 수립합니다.\n"
        "논리적이고 체계적인 구조화가 특기입니다.\n"
        "한국어로 답변하십시오."
    ),
    "작가": (
        "당신은 창의적인 전문 작가입니다.\n"
        "기획 내용을 바탕으로 완성도 높고 설득력 있는 결과물을 작성합니다.\n"
        "독자의 공감을 이끌어내는 문체가 특기입니다.\n"
        "한국어로 답변하십시오."
    ),
    "검토관": (
        "당신은 엄격한 품질 검토관입니다.\n"
        "결과물을 냉정하게 검토하고 반드시 아래 형식으로 판정하십시오:\n"
        "  PASS: 합격 이유 한 줄\n"
        "  REJECT: 구체적 개선 사항 (이 경우 반드시 'REJECT:' 접두사 사용)\n"
        "모호한 판정은 금지입니다. 한국어로 답변하십시오."
    ),
}


# ─── 데이터 모델 ──────────────────────────────────────────────────────

@dataclass
class ChatMessage:
    """전역 채팅 이력의 단위 메시지 — 바톤 터치의 기본 단위"""
    agent: str       # 발화자 이름 (예: "기획자", "창선님")
    content: str     # 발화 내용
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class AgentResponse:
    """에이전트 호출 결과 컨테이너"""
    agent: str
    content: str
    success: bool
    error: str | None = None


# ─── 핵심 엔진 ───────────────────────────────────────────────────────

class GeminiEngine:
    """
    단일 Gemini API 인스턴스로 여러 에이전트를 구동하는 핵심 엔진.

    가장 중요한 특징: 이 클래스의 global_chat_history가
    모든 에이전트 사이에서 공유되는 '회의록'이다.
    """

    def __init__(self, api_key: str) -> None:
        """
        입력: api_key — Google AI Studio API 키
        신규 SDK: google.genai.Client를 사용 (google.generativeai deprecated)
        """
        self._client = genai.Client(api_key=api_key)
        # 모든 에이전트가 공유하는 전역 채팅 이력 (바톤 터치의 핵심)
        self.global_chat_history: list[ChatMessage] = []
        self._model_name = GEMINI_MODEL
        logger.info(f"GeminiEngine 초기화 완료 (모델: {self._model_name})")

    # ─── 이력 관리 ─────────────────────────────────────────────────

    def add_user_input(self, content: str) -> None:
        """
        창선님의 입력을 전역 이력에 최우선으로 추가.
        이후 호출되는 모든 에이전트가 이 입력을 컨텍스트로 받는다.
        """
        self.global_chat_history.append(
            ChatMessage(agent="창선님(사령관)", content=content)
        )
        logger.info(f"사령관 입력 이력 추가: {content[:50]}...")

    def reset_session(self) -> None:
        """새 세션 시작 시 채팅 이력을 초기화한다."""
        self.global_chat_history.clear()
        logger.info("세션 이력 초기화 완료")

    def get_history_summary(self, max_entries: int = 20) -> str:
        """
        채팅 이력을 읽기 쉬운 텍스트로 변환.
        max_entries: 최대 포함할 최근 메시지 수 (프롬프트 길이 제한 대응)
        """
        if not self.global_chat_history:
            return "(이력 없음)"
        recent = self.global_chat_history[-max_entries:]
        return "\n".join(f"[{m.agent}]: {m.content}" for m in recent)

    # ─── 컨텍스트 프롬프트 조립 ────────────────────────────────────

    def _build_context_prompt(
        self,
        task: str,
        extra_context: str = "",
    ) -> str:
        """
        바톤 터치 핵심 메서드: 이전 발화 이력 + 현재 업무를 하나의 프롬프트로 조립.

        입력:
            task          — 현재 에이전트에게 내릴 구체적 지시
            extra_context — 추가로 주입할 외부 컨텍스트 (예: 전략 노트)
        출력: 완성된 프롬프트 문자열

        왜 이 방식인가?
          Gemini API는 요청마다 독립적이라 이전 대화를 기억하지 못한다.
          따라서 매 호출마다 전체 이력을 직접 주입해야
          에이전트들이 서로의 발화를 인지하고 '이어받을' 수 있다.
        """
        parts: list[str] = []

        if extra_context:
            parts.append(f"[참고 전략 노트]\n{extra_context}")

        if self.global_chat_history:
            # 최근 15개 메시지만 포함하여 프롬프트 길이 제한
            history_text = self.get_history_summary(max_entries=15)
            parts.append(f"[지금까지의 회의 내용 — 바톤 이어받기]\n{history_text}")

        parts.append(f"[현재 업무]\n{task}")
        return "\n\n".join(parts)

    # ─── 에이전트 호출 ────────────────────────────────────────────

    async def call_agent(
        self,
        agent_name: str,
        task: str,
        persona_key: str = "기획자",
        extra_context: str = "",
        inject_history: bool = True,
    ) -> AgentResponse:
        """
        지정된 페르소나로 Gemini를 호출하고 결과를 전역 이력에 추가.

        입력:
            agent_name    — 이력에 기록될 에이전트 표시 이름
            task          — 수행할 업무
            persona_key   — PERSONAS 딕셔너리의 키 (인격 전환 핵심)
            extra_context — 추가 컨텍스트 (전략 노트 등)
            inject_history— True이면 전체 이력을 프롬프트에 포함

        Anti-Ban: 인간 활동 패턴 모사를 위한 무작위 딜레이 삽입
        """
        # Anti-Ban 딜레이: 무료 API Rate Limit 회피 + 인간 패턴 모사
        delay = random.uniform(2, 5)
        logger.info(f"[{agent_name}] Anti-Ban 딜레이 {delay:.1f}초...")
        await asyncio.sleep(delay)

        system_instruction = PERSONAS.get(persona_key, PERSONAS["기획자"])
        prompt = (
            self._build_context_prompt(task, extra_context)
            if inject_history
            else task
        )

        logger.info(
            f"[{agent_name}] Gemini 호출 "
            f"(페르소나: {persona_key}, 프롬프트: {len(prompt)}자)"
        )

        try:
            # system_instruction을 동적으로 설정 — 인격 전환의 핵심
            # 신규 SDK: GenerateContentConfig으로 system_instruction 전달
            config = types.GenerateContentConfig(
                system_instruction=system_instruction,
            )

            # 블로킹 API를 비동기 이벤트 루프에서 실행
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self._client.models.generate_content(
                    model=self._model_name,
                    contents=prompt,
                    config=config,
                ),
            )

            content: str = response.text.strip()

            # 이 에이전트의 발화를 전역 이력에 추가 — 다음 에이전트가 이어받는다
            self.global_chat_history.append(
                ChatMessage(agent=agent_name, content=content)
            )

            logger.info(f"[{agent_name}] 응답 완료 ({len(content)}자)")
            return AgentResponse(agent=agent_name, content=content, success=True)

        except Exception as exc:
            logger.error(f"[{agent_name}] 호출 오류: {exc}")
            return AgentResponse(
                agent=agent_name, content="", success=False, error=str(exc)
            )
