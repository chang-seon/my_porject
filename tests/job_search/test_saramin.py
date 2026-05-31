"""DAY 17 — 사람인 API 클라이언트 + 정규화 테스트 (네트워크 없이 mock 사용)."""
import pytest
from unittest.mock import patch, MagicMock
import json

from job_agent.features.job_search.internal.sources.saramin import SaraminSource
from job_agent.features.job_search.internal.normalizer import (
    normalize_saramin,
    normalize_worknet,
    normalize_joballio,
    normalize_gemini,
    deduplicate,
    _parse_ymd,
)


# ──────────────────────────────────────────
# fixtures
# ──────────────────────────────────────────

SARAMIN_RAW_ITEM = {
    "id": "12345",
    "posting-date": "2026-05-31",
    "expiration-date": "2026-06-30",
    "position": {
        "title": "AI 엔지니어",
        "location": {"#text": "서울 마곡"},
        "job-type": {"#text": "정규직"},
        "job-code": {"#text": "Python, PyTorch"},
    },
    "company": {"detail": {"name": "테스트컴퍼니"}},
    "url": {"#text": "https://saramin.co.kr/job/12345"},
    "salary": {"#text": "회사내규"},
}

SARAMIN_API_RESPONSE = {
    "jobs": {
        "job": [SARAMIN_RAW_ITEM]
    }
}

WORKNET_RAW_ITEM = {
    "JO_SN": "WN001",
    "JO_NM": "데이터 분석가",
    "CMPNY_NM": "워크넷컴퍼니",
    "WORK_REGION_NM": "서울",
    "OCCUPATION_NM": "데이터분석",
    "EMPLMT_STLE_NM": "정규직",
    "SALARY_COND_NM": "3000만원",
    "REGIST_DT": "2026-05-30",
    "DEADLINE_DT": "2026-06-20",
    "REQUIRED_CAREER": "Python, SQL",
    "WANTEDMAIN_URL": "https://www.work.go.kr/job/WN001",
}

JOBALLIO_RAW_ITEM = {
    "recruit_no": "JA001",
    "title": "백엔드 개발자",
    "company_nm": "잡알리오컴퍼니",
    "work_place": "경기 성남",
    "occupation": "백엔드",
    "emp_type": "정규직",
    "salary": "협의",
    "req_skill": "Java, Spring",
    "reg_date": "2026-05-28",
    "end_date": "2026-06-28",
    "url": "https://joballio.com/job/JA001",
}

GEMINI_RAW_ITEM = {
    "job_id": "GM001",
    "source": "링크드인",
    "url": "https://linkedin.com/jobs/GM001",
    "title": "머신러닝 엔지니어",
    "company": "외국계기업",
    "location": "서울",
    "job_role": "ML엔지니어",
    "employment_type": "정규직",
    "salary": "협의",
    "skills_required": "Python, TensorFlow",
    "posted_date": "2026-05-29",
    "deadline": None,
}


# ──────────────────────────────────────────
# SaraminSource 단위 테스트
# ──────────────────────────────────────────

class TestSaraminSource:
    def test_api_key_missing_returns_failure(self):
        src = SaraminSource(api_key="")
        result = src.search({"job_role": "AI 엔지니어"})
        assert result["결과"] == "실패"
        assert "SARAMIN_API_KEY" in result["이유"]

    def test_search_success(self):
        src = SaraminSource(api_key="test-key")
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(SARAMIN_API_RESPONSE).encode("utf-8")
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_resp):
            result = src.search({"job_role": "AI 엔지니어", "location": "마곡"})

        assert result["결과"] == "성공"
        assert result["total"] == 1
        assert result["source"] == "사람인"
        assert len(result["raw_items"]) == 1

    def test_search_empty_response(self):
        src = SaraminSource(api_key="test-key")
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({"jobs": {}}).encode("utf-8")
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_resp):
            result = src.search({"job_role": "없는직무"})

        assert result["결과"] == "성공"
        assert result["total"] == 0

    def test_network_error_returns_failure(self):
        src = SaraminSource(api_key="test-key")
        with patch("urllib.request.urlopen", side_effect=Exception("연결 거부")):
            with patch("time.sleep"):
                result = src.search({"job_role": "AI"})
        assert result["결과"] == "실패"

    def test_location_mapping_magok(self):
        from job_agent.features.job_search.internal.sources.saramin import SaraminSource
        assert SaraminSource._map_location("마곡") == "101000"

    def test_employment_mapping(self):
        assert SaraminSource._map_employment("정규직") == "1"
        assert SaraminSource._map_employment("인턴") == "3"


# ──────────────────────────────────────────
# normalizer 단위 테스트
# ──────────────────────────────────────────

class TestNormalizeSaramin:
    def test_basic_fields(self):
        result = normalize_saramin(SARAMIN_RAW_ITEM)
        assert result["job_id"] == "12345"
        assert result["source"] == "사람인"
        assert result["title"] == "AI 엔지니어"
        assert result["company"] == "테스트컴퍼니"
        assert result["year"] == 2026
        assert result["month"] == 5
        assert result["day"] == 31

    def test_skills_parsed(self):
        result = normalize_saramin(SARAMIN_RAW_ITEM)
        assert "Python" in result["skills_required"]
        assert "PyTorch" in result["skills_required"]

    def test_empty_raw_does_not_crash(self):
        result = normalize_saramin({})
        assert "job_id" in result


class TestNormalizeWorknet:
    def test_basic_fields(self):
        result = normalize_worknet(WORKNET_RAW_ITEM)
        assert result["job_id"] == "WN001"
        assert result["source"] == "워크넷"
        assert result["company"] == "워크넷컴퍼니"
        assert result["year"] == 2026


class TestNormalizeJoballio:
    def test_basic_fields(self):
        result = normalize_joballio(JOBALLIO_RAW_ITEM)
        assert result["job_id"] == "JA001"
        assert result["source"] == "잡알리오"
        assert "Java" in result["skills_required"]


class TestNormalizeGemini:
    def test_skills_string_to_list(self):
        result = normalize_gemini(GEMINI_RAW_ITEM)
        assert isinstance(result["skills_required"], list)
        assert "Python" in result["skills_required"]


# ──────────────────────────────────────────
# deduplicate 테스트
# ──────────────────────────────────────────

class TestDeduplicate:
    def test_removes_duplicate_url(self):
        postings = [
            {"url": "https://example.com/job/1", "title": "A"},
            {"url": "https://example.com/job/1", "title": "A duplicate"},
            {"url": "https://example.com/job/2", "title": "B"},
        ]
        result = deduplicate(postings)
        assert len(result) == 2

    def test_empty_url_kept(self):
        postings = [
            {"url": "", "title": "no-url-1"},
            {"url": "", "title": "no-url-2"},
        ]
        result = deduplicate(postings)
        assert len(result) == 2


# ──────────────────────────────────────────
# _parse_ymd 테스트
# ──────────────────────────────────────────

class TestParseYmd:
    def test_standard_format(self):
        assert _parse_ymd("2026-05-31") == (2026, 5, 31)

    def test_slash_format(self):
        assert _parse_ymd("2026/05/31") == (2026, 5, 31)

    def test_compact_format(self):
        assert _parse_ymd("20260531") == (2026, 5, 31)

    def test_empty_string(self):
        assert _parse_ymd("") == (None, None, None)

    def test_invalid_string(self):
        assert _parse_ymd("not-a-date") == (None, None, None)
