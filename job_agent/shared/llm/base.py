from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Iterator, Optional


class LLMClient(ABC):

    @abstractmethod
    def generate(self, prompt: str, system: Optional[str] = None, **kwargs) -> str:
        """단일 응답 생성"""

    @abstractmethod
    def stream(self, prompt: str, system: Optional[str] = None, **kwargs) -> Iterator[str]:
        """스트리밍 응답 생성"""

    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """토큰 수 계산"""
