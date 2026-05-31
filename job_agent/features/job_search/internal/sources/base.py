from __future__ import annotations

from abc import ABC, abstractmethod


class JobSource(ABC):
    """공고 소스 추상 기반 클래스."""

    source_name: str = ""

    @abstractmethod
    def search(self, query: dict) -> dict:
        """공고를 검색하여 원본 데이터 리스트를 반환한다.

        query 키: job_role, location, employment_type, count(최대 건수)
        반환: {"결과": "성공", "raw_items": list[dict], "total": int}
              {"결과": "실패", "이유": str}
        """

    def _make_error(self, reason: str) -> dict:
        return {"결과": "실패", "이유": reason, "source": self.source_name}
