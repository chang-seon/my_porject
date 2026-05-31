"""사람인 채용정보 Open API 클라이언트.

API 문서: https://oapi.saramin.co.kr/guide/
환경변수: SARAMIN_API_KEY
"""
from __future__ import annotations

import os
import time
import urllib.parse
import urllib.request
import json

from job_agent.features.job_search.internal.sources.base import JobSource

_BASE_URL = "https://oapi.saramin.co.kr/job-search"
_MAX_RETRIES = 3
_BACKOFF_BASE = 2.0  # 지수 backoff 초 단위


class SaraminSource(JobSource):
    source_name = "사람인"

    def __init__(self, api_key: str | None = None):
        self._api_key = api_key or os.getenv("SARAMIN_API_KEY", "")

    def search(self, query: dict) -> dict:
        """사람인 API로 공고를 검색한다.

        query 키:
          job_role (str): 직무 키워드
          location (str, optional): 근무지 (기본: 서울)
          employment_type (str, optional): 고용형태
          count (int, optional): 최대 건수 (기본: 20, 최대: 110)
        """
        try:
            if not self._api_key:
                return self._make_error("SARAMIN_API_KEY 환경변수 미설정")

            params = self._build_params(query)
            url = f"{_BASE_URL}?{urllib.parse.urlencode(params)}"
            raw_items = self._fetch_with_retry(url)
            return {"결과": "성공", "raw_items": raw_items, "total": len(raw_items), "source": self.source_name}
        except Exception as e:
            return self._make_error(str(e))

    def _build_params(self, query: dict) -> dict:
        params: dict = {
            "access-key": self._api_key,
            "count": min(int(query.get("count", 20)), 110),
            "fields": "expiration-date,posted-date,job-mid-code,job-code,position,company,url",
        }

        keywords = []
        if query.get("job_role"):
            keywords.append(query["job_role"])
        if keywords:
            params["keywords"] = " ".join(keywords)

        location = query.get("location", "")
        if location:
            params["loc_mcd"] = self._map_location(location)

        employment = query.get("employment_type", "")
        if employment:
            params["job_type"] = self._map_employment(employment)

        return params

    def _fetch_with_retry(self, url: str) -> list[dict]:
        last_error: Exception | None = None
        for attempt in range(_MAX_RETRIES):
            try:
                req = urllib.request.Request(url, headers={"Accept": "application/json"})
                with urllib.request.urlopen(req, timeout=10) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                return self._parse_response(data)
            except Exception as e:
                last_error = e
                if attempt < _MAX_RETRIES - 1:
                    time.sleep(_BACKOFF_BASE ** attempt)
        raise RuntimeError(f"사람인 API 호출 실패 ({_MAX_RETRIES}회): {last_error}")

    def _parse_response(self, data: dict) -> list[dict]:
        jobs = data.get("jobs", {})
        if not jobs:
            return []
        job_list = jobs.get("job", [])
        if isinstance(job_list, dict):
            job_list = [job_list]
        return job_list

    @staticmethod
    def _map_location(location: str) -> str:
        """지역명 → 사람인 loc_mcd 코드."""
        mapping = {
            "서울": "101000",
            "경기": "102000",
            "인천": "103000",
            "부산": "106000",
            "대구": "104000",
            "마곡": "101000",  # 마곡은 서울로 매핑
        }
        for key, code in mapping.items():
            if key in location:
                return code
        return "101000"  # 기본: 서울

    @staticmethod
    def _map_employment(employment_type: str) -> str:
        """고용형태 → 사람인 job_type 코드."""
        mapping = {
            "정규직": "1",
            "계약직": "2",
            "인턴": "3",
            "아르바이트": "4",
            "파견직": "5",
        }
        for key, code in mapping.items():
            if key in employment_type:
                return code
        return "1"
