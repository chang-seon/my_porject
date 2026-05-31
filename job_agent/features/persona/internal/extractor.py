from __future__ import annotations
from pathlib import Path

SUPPORTED = {".txt", ".docx", ".pdf"}


def extract_text_from_file(filepath: Path) -> dict:
    """단일 파일에서 텍스트를 추출한다. docx/pdf/txt 지원."""
    try:
        if not filepath.exists():
            return {"결과": "실패", "이유": f"파일 없음: {filepath}"}
        suffix = filepath.suffix.lower()
        if suffix == ".txt":
            text = filepath.read_text(encoding="utf-8")
        elif suffix == ".docx":
            from docx import Document
            doc = Document(str(filepath))
            text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
        elif suffix == ".pdf":
            from pypdf import PdfReader
            reader = PdfReader(str(filepath))
            pages = [page.extract_text() or "" for page in reader.pages]
            text = "\n".join(pages)
        else:
            return {"결과": "실패", "이유": f"지원하지 않는 형식: {suffix} (지원: {SUPPORTED})"}
        if not text.strip():
            return {"결과": "실패", "이유": f"텍스트 없음 (빈 파일): {filepath.name}"}
        return {"결과": "성공", "text": text.strip(), "filename": filepath.name}
    except Exception as e:
        return {"결과": "실패", "이유": str(e)}


def extract_texts_from_files(files: list[Path]) -> dict:
    """여러 파일에서 텍스트를 추출해 하나로 합친다."""
    try:
        texts, errors = [], []
        for f in files:
            result = extract_text_from_file(Path(f))
            if result["결과"] == "성공":
                texts.append(f"=== {result['filename']} ===\n{result['text']}")
            else:
                errors.append(f"{Path(f).name}: {result['이유']}")
        if not texts:
            return {"결과": "실패", "이유": "추출된 텍스트 없음", "errors": errors}
        return {"결과": "성공", "combined_text": "\n\n".join(texts), "errors": errors, "file_count": len(texts)}
    except Exception as e:
        return {"결과": "실패", "이유": str(e)}
