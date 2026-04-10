"""파일 도구 - 파일 탐색·이동·삭제·정리 기능을 제공한다."""

import os
import shutil
from pathlib import Path
from datetime import datetime


def list_directory(path: str, pattern: str = "*") -> dict:
    """지정 경로의 파일·폴더 목록을 반환한다."""
    base = Path(path)
    if not base.exists():
        return {"결과": "실패", "이유": f"경로가 존재하지 않습니다: {path}"}

    items = []
    for item in base.glob(pattern):
        stat = item.stat()
        items.append({
            "이름": item.name,
            "종류": "폴더" if item.is_dir() else "파일",
            "크기(KB)": round(stat.st_size / 1024, 2),
            "수정일시": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M"),
        })

    return {"경로": path, "항목 수": len(items), "목록": items}


def find_large_files(path: str, min_size_mb: float = 100) -> dict:
    """지정 경로에서 특정 크기 이상의 파일을 재귀 탐색해 반환한다."""
    base = Path(path)
    min_bytes = min_size_mb * 1e6
    large_files = []

    for f in base.rglob("*"):
        try:
            if f.is_file() and f.stat().st_size >= min_bytes:
                large_files.append({
                    "경로": str(f),
                    "크기(MB)": round(f.stat().st_size / 1e6, 2),
                })
        except (PermissionError, OSError):
            pass

    large_files.sort(key=lambda x: x["크기(MB)"], reverse=True)
    return {"기준(MB)": min_size_mb, "발견된 파일 수": len(large_files), "목록": large_files}


def move_file(src: str, dst: str) -> dict:
    """파일 또는 폴더를 src 에서 dst 로 이동한다."""
    try:
        shutil.move(src, dst)
        return {"결과": "성공", "원본": src, "대상": dst}
    except Exception as e:
        return {"결과": "실패", "이유": str(e)}


def delete_file(path: str, confirm: bool = False) -> dict:
    """파일 또는 빈 폴더를 삭제한다. confirm=True 일 때만 실제 삭제한다."""
    if not confirm:
        return {"결과": "취소됨", "이유": "confirm=True 로 호출해야 삭제가 실행됩니다."}

    target = Path(path)
    if not target.exists():
        return {"결과": "실패", "이유": f"경로가 존재하지 않습니다: {path}"}

    try:
        if target.is_dir():
            shutil.rmtree(target)
        else:
            target.unlink()
        return {"결과": "성공", "삭제된 경로": path}
    except Exception as e:
        return {"결과": "실패", "이유": str(e)}


def organize_downloads(downloads_path: str) -> dict:
    """다운로드 폴더를 확장자별 하위 폴더로 정리한다."""
    ext_map = {
        "이미지": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg"],
        "동영상": [".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv"],
        "문서": [".pdf", ".docx", ".doc", ".xlsx", ".xls", ".pptx", ".txt", ".hwp"],
        "압축파일": [".zip", ".rar", ".7z", ".tar", ".gz"],
        "코드": [".py", ".js", ".ts", ".html", ".css", ".java", ".c", ".cpp"],
        "기타": [],
    }

    base = Path(downloads_path)
    moved = []

    for f in base.iterdir():
        if not f.is_file():
            continue
        ext = f.suffix.lower()
        target_folder = "기타"
        for folder, exts in ext_map.items():
            if ext in exts:
                target_folder = folder
                break

        dest_dir = base / target_folder
        dest_dir.mkdir(exist_ok=True)
        dest = dest_dir / f.name

        try:
            shutil.move(str(f), str(dest))
            moved.append({"파일": f.name, "이동 폴더": target_folder})
        except Exception as e:
            moved.append({"파일": f.name, "오류": str(e)})

    return {"정리된 파일 수": len(moved), "내역": moved}
