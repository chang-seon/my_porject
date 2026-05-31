"""DAY 18 — 워크넷·잡알리오·Gemini 소스 + 통합 aggregator 테스트."""
import pytest
from unittest.mock import patch, MagicMock
import json

from job_agent.features.job_search.internal.sources.worknet import WorknetSource
from job_agent.features.job_search.internal.sources.joballio import JoballioSource
from job_agent.features.job_search.internal.sources.gemini_web import GeminiWebSource
from job_agent.features.job_search.internal.aggregator import fetch_all


# ──────────────────────────────────────────────
# WorknetSource
# ──────────────────────────────────────────────

WORKNET_RESPONSE = {
    "wantedRoot": {
        "wanted": [
            {
                "JO_SN": "WN001",
                "JO_NM": "데이터 분석가",
                "CMPNY_NM": "워크넷컴퍼니",
                "WORK_REGION_NM": "서울",
                "REGIST_DT": "2026-05-30",
                "WANTEDMAIN_URL": "https://www.work.go.kr/job/WN001",
            }
        ]
    }
}

JOBALLIO_RESPONSE = {
    "response": {
        "body": {
            "items": {
                "item": [
                    {
                        "recruit_no": "JA001",
                        "title": "백엔드 개발자",
                        "company_nm": "잡알리오컴퍼니",
                        "url": "https://joballio.com/job/JA001",
                        "reg_date": "2026-05-28",
                    }
                ]
            }
        }
    }
}


class TestWorknetSource:
    def test_api_key_missing(self):
        src = WorknetSource(api_key="")
        result = src.search({"job_role": "데이터"})
        assert result["결과"] == "실패"
        assert "WORKNET_API_KEY" in result["이유"]

    def test_search_success(self):
        src = WorknetSource(api_key="test-key")
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(WORKNET_RESPONSE).encode("utf-8")
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_resp):
            result = src.search({"job_role": "데이터 분석가"})

        assert result["결과"] == "성공"
        assert result["total"] == 1

    def test_location_mapping(self):
        assert WorknetSource._map_location("마곡") == "11000000"
        assert WorknetSource._map_location("경기") == "41000000"


class TestJoballioSource:
    def test_api_key_missing(self):
        src = JoballioSource(api_key="")
        result = src.search({"job_role": "개발자"})
        assert result["결과"] == "실패"
        assert "JOBALLIO_API_KEY" in result["이유"]

    def test_search_success(self):
        src = JoballioSource(api_key="test-key")
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(JOBALLIO_RESPONSE).encode("utf-8")
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_resp):
            result = src.search({"job_role": "백엔드"})

        assert result["결과"] == "성공"
        assert result["total"] == 1


class TestGeminiWebSource:
    def test_api_key_missing(self):
        src = GeminiWebSource(api_key="")
        result = src.search({"job_role": "AI"})
        assert result["결과"] == "실패"
        assert "GOOGLE_AI_API_KEY" in result["이유"]

    def test_search_with_mock_gemini(self):
        src = GeminiWebSource(api_key="test-key")
        fake_json = json.dumps([
            {
                "job_id": "GM001",
                "source": "링크드인",
                "url": "https://linkedin.com/jobs/1",
                "title": "AI 엔지니어",
                "company": "테스트",
                "location": "서울",
                "job_role": "AI",
                "employment_type": "정규직",
                "salary": None,
                "skills_required": ["Python"],
                "posted_date": "2026-05-31",
                "deadline": None,
            }
        ])

        mock_response = MagicMock()
        mock_response.text = fake_json

        with patch("google.genai.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.models.generate_content.return_value = mock_response
            mock_client_cls.return_value = mock_client

            result = src.search({"job_role": "AI 엔지니어", "count": 5})

        assert result["결과"] == "성공"
        assert result["total"] == 1

    def test_invalid_json_returns_empty(self):
        src = GeminiWebSource(api_key="test-key")
        mock_response = MagicMock()
        mock_response.text = "이것은 JSON이 아닙니다"

        with patch("google.genai.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.models.generate_content.return_value = mock_response
            mock_client_cls.return_value = mock_client

            result = src.search({"job_role": "AI"})

        assert result["결과"] == "성공"
        assert result["total"] == 0


# ──────────────────────────────────────────────
# fetch_all aggregator
# ──────────────────────────────────────────────

class TestFetchAll:
    def test_all_sources_fail_returns_success_with_errors(self):
        """모든 소스 API 키 미설정 → 성공 반환 + errors 목록"""
        result = fetch_all({"job_role": "AI 엔지니어"})
        assert result["결과"] == "성공"
        assert result["total"] == 0
        assert len(result["errors"]) > 0

    def test_single_source_specified(self):
        """sources 지정 시 해당 소스만 호출"""
        with patch(
            "job_agent.features.job_search.internal.aggregator.SaraminSource"
        ) as mock_cls:
            mock_src = MagicMock()
            mock_src.search.return_value = {
                "결과": "성공",
                "raw_items": [{"id": "1", "position": {"title": "AI"}, "company": {"detail": {"name": "ABC"}}, "url": "https://x.com/1"}],
                "total": 1,
                "source": "사람인",
            }
            mock_cls.return_value = mock_src

            result = fetch_all({"job_role": "AI", "sources": ["사람인"]})

        assert result["결과"] == "성공"

    def test_unknown_source_in_errors(self):
        result = fetch_all({"job_role": "AI", "sources": ["없는소스"]})
        assert result["결과"] == "성공"
        assert any("없는소스" in e for e in result["errors"])

    def test_deduplication_applied(self):
        """동일 URL 공고가 두 소스에서 오면 1건으로 줄어든다."""
        import job_agent.features.job_search.internal.aggregator as agg

        duplicate_item = {
            "job_id": "1",
            "source": "사람인",
            "url": "https://same.url/job/1",
            "title": "중복공고",
            "company": "X",
            "location": None,
            "job_role": None,
            "employment_type": None,
            "salary": None,
            "skills_required": [],
            "raw_text": None,
            "posted_date": None,
            "deadline": None,
            "year": None,
            "month": None,
            "day": None,
        }
        # _NORMALIZERS dict를 직접 패치해야 모듈 로드 시점 참조 문제를 피할 수 있다
        fixed_normalizers = {k: (lambda item: duplicate_item) for k in agg._NORMALIZERS}

        with patch(
            "job_agent.features.job_search.internal.aggregator.SaraminSource"
        ) as s_cls, patch(
            "job_agent.features.job_search.internal.aggregator.WorknetSource"
        ) as w_cls, patch(
            "job_agent.features.job_search.internal.aggregator.JoballioSource"
        ) as j_cls, patch(
            "job_agent.features.job_search.internal.aggregator.GeminiWebSource"
        ) as g_cls, patch.dict(agg._NORMALIZERS, fixed_normalizers):
            for cls in [s_cls, w_cls, j_cls, g_cls]:
                mock_src = MagicMock()
                mock_src.search.return_value = {
                    "결과": "성공",
                    "raw_items": [{}],
                    "total": 1,
                    "source": "테스트",
                }
                cls.return_value = mock_src

            result = fetch_all({"job_role": "AI"})

        assert result["total"] == 1
