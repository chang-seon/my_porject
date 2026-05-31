import pytest
from unittest.mock import patch, MagicMock
from job_agent.features.notification.internal.telegram_sender import send_message, send_from_template


class TestSendMessage:
    def test_no_token_returns_failure(self):
        with patch("job_agent.features.notification.internal.telegram_sender._BOT_TOKEN", ""):
            result = send_message("테스트")
        assert result["결과"] == "실패"
        assert "BOT_TOKEN" in result["이유"]

    def test_no_chat_id_returns_failure(self):
        with patch("job_agent.features.notification.internal.telegram_sender._BOT_TOKEN", "fake_token"), \
             patch("job_agent.features.notification.internal.telegram_sender._CHAT_ID", ""):
            result = send_message("테스트")
        assert result["결과"] == "실패"
        assert "CHAT_ID" in result["이유"]

    def test_send_success(self):
        mock_cm = MagicMock()
        mock_cm.__enter__.return_value = mock_cm
        mock_cm.__exit__.return_value = False
        mock_cm.read.return_value = b'{"ok": true, "result": {"message_id": 42}}'
        with patch("job_agent.features.notification.internal.telegram_sender._BOT_TOKEN", "fake"), \
             patch("job_agent.features.notification.internal.telegram_sender._CHAT_ID", "12345"), \
             patch("job_agent.features.notification.internal.telegram_sender.urllib.request.urlopen", return_value=mock_cm):
            result = send_message("안녕하세요")
        assert result["결과"] == "성공"
        assert result["message_id"] == "42"

    def test_network_error_returns_failure(self):
        with patch("job_agent.features.notification.internal.telegram_sender._BOT_TOKEN", "fake"), \
             patch("job_agent.features.notification.internal.telegram_sender._CHAT_ID", "12345"), \
             patch("urllib.request.urlopen", side_effect=Exception("연결 실패")):
            result = send_message("테스트")
        assert result["결과"] == "실패"


class TestSendFromTemplate:
    def test_missing_template_returns_failure(self):
        result = send_from_template("없는_템플릿", {})
        assert result["결과"] == "실패"
        assert "템플릿 없음" in result["이유"]

    def test_missing_variable_returns_failure(self):
        result = send_from_template("공고알림", {})
        assert result["결과"] == "실패"
        assert "변수 누락" in result["이유"]

    def test_template_renders_and_sends(self):
        mock_cm = MagicMock()
        mock_cm.__enter__.return_value = mock_cm
        mock_cm.__exit__.return_value = False
        mock_cm.read.return_value = b'{"ok": true, "result": {"message_id": 1}}'
        context = {
            "company": "테스트회사", "job_role": "AI엔지니어",
            "location": "서울", "deadline": "2026-06-30",
            "url": "https://example.com", "match_score": "85",
        }
        with patch("job_agent.features.notification.internal.telegram_sender._BOT_TOKEN", "fake"), \
             patch("job_agent.features.notification.internal.telegram_sender._CHAT_ID", "12345"), \
             patch("job_agent.features.notification.internal.telegram_sender.urllib.request.urlopen", return_value=mock_cm):
            result = send_from_template("공고알림", context)
        assert result["결과"] == "성공"
