"""잡알리오 채용정보 API 클라이언트.

환경변수: JOBALLIO_API_KEY
"""
from __future__ import annotations

import json
import os
import time
import urllib.parse
import urllib.request

from job_agent.features.job_search.internal.sources.base import JobSource

_BASE_URL = "https://www.joballio.com/api/job/list"
_MAX_RETRIES = 3
_BACKOFF_BASE = 2.0


class JoballioSource(JobSource):
    source_name = "잡알리오"

    def __init__(self, api_key: str | None = None):
        self._api_key = api_key or os.getenv("JOBALLIO_API_KEY", "")

    def search(self, query: dict) -> dict:
        """잡알리오 API로 공고를 검색한다."""
        try:
            if not self._api_key:
                return self._make_error("JOBALLIO_API_KEY 환경변수 미설정")

            params = self._build_params(query)
            url = f"{_BASE_URL}?{urllib.parse.urlencode(params)}"
            raw_items = self._fetch_with_retry(url)
            return {"결과": "성공", "raw_items": raw_items, "total": len(raw_items), "source": self.source_name}
        except Exception as e:
            return self._make_error(str(e))

    def _build_params(self, query: dict) -> dict:
        params: dict = {
            "serviceKey": self._api_key,
            "pageNo": 1,
            "numOfRows": min(int(query.get("count", 20)), 100),
            "resultType": "JSON",
        }
        if query.get("job_role"):
            params["keyword"] = query["job_role"]
        if query.get("location"):
            params["workRegion"] = query["location"]
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
        raise RuntimeError(f"잡알리오 API 호출 실패 ({_MAX_RETRIES}회): {last_error}")

    def _parse_response(self, data: dict) -> list[dict]:
        items = data.get("response", {}).get("body", {}).get("items", {}).get("item", [])
        if isinstance(items, dict):
            items = [items]
        return items if isinstance(items, list) else []
