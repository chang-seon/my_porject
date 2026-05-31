import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
from job_agent.features.persona.internal.extractor import (
    extract_text_from_file, extract_texts_from_files
)
from job_agent.features.persona.internal.llm_extract import extract_persona_from_text


class TestExtractTextFromFile:
    def test_txt_extraction(self, tmp_path):
        f = tmp_path / "resume.txt"
        f.write_text("이름: 어창선\n학교: 한국대", encoding="utf-8")
        result = extract_text_from_file(f)
        assert result["결과"] == "성공"
        assert "어창선" in result["text"]

    def test_empty_file_returns_failure(self, tmp_path):
        f = tmp_path / "empty.txt"
        f.write_text("", encoding="utf-8")
        result = extract_text_from_file(f)
        assert result["결과"] == "실패"
        assert "빈 파일" in result["이유"]

    def test_unsupported_format_returns_failure(self, tmp_path):
        f = tmp_path / "photo.jpg"
        f.write_bytes(b"fake image data")
        result = extract_text_from_file(f)
        assert result["결과"] == "실패"
        assert "지원하지 않는 형식" in result["이유"]

    def test_nonexistent_file_returns_failure(self, tmp_path):
        result = extract_text_from_file(tmp_path / "없는파일.txt")
        assert result["결과"] == "실패"
        assert "파일 없음" in result["이유"]


class TestExtractTextsFromFiles:
    def test_multiple_files_combined(self, tmp_path):
        f1 = tmp_path / "a.txt"
        f2 = tmp_path / "b.txt"
        f1.write_text("파일A 내용", encoding="utf-8")
        f2.write_text("파일B 내용", encoding="utf-8")
        result = extract_texts_from_files([f1, f2])
        assert result["결과"] == "성공"
        assert "파일A 내용" in result["combined_text"]
        assert "파일B 내용" in result["combined_text"]
        assert result["file_count"] == 2

    def test_all_failed_returns_failure(self, tmp_path):
        result = extract_texts_from_files([tmp_path / "없음.txt"])
        assert result["결과"] == "실패"

    def test_partial_success_continues(self, tmp_path):
        good = tmp_path / "good.txt"
        good.write_text("좋은 파일", encoding="utf-8")
        result = extract_texts_from_files([good, tmp_path / "없음.txt"])
        assert result["결과"] == "성공"
        assert len(result["errors"]) == 1


class TestLlmExtract:
    def test_extract_persona_success(self):
        import json
        mock_router = MagicMock()
        mock_router.generate.return_value = json.dumps({
            "name": "어창선", "birth": "1997-01-01",
            "career_stage": "신입",
            "education": [{"school": "한국대", "major": "AI", "degree": "학사", "graduated": "2022-02-28"}],
            "target_jobs": [{"industry": "IT", "job_role": "AI엔지니어", "priority": 1}],
            "content_assets": [], "skills": [], "style_markers": [],
            "anti_patterns": [], "traits": [], "values": [], "constraints": [], "career_history": []
        })
        result = extract_persona_from_text("샘플 텍스트", "user_001", router=mock_router)
        assert result["결과"] == "성공"
        assert result["persona"]["name"] == "어창선"

    def test_extract_persona_json_error(self):
        mock_router = MagicMock()
        mock_router.generate.return_value = "JSON이 아닌 텍스트"
        result = extract_persona_from_text("샘플", "user_001", router=mock_router)
        assert result["결과"] == "실패"
        assert "JSON" in result["이유"]
