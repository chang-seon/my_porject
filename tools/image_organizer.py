"""이미지 정리 도구 - Claude Vision으로 캐릭터를 인식해 폴더별로 자동 분류한다."""

import base64
import re
import shutil
import time
from collections import Counter
from pathlib import Path

import anthropic

from config import settings

# ── 상수 ──────────────────────────────────────────────────────────────────────

# Claude Vision이 처리 가능한 형식
SUPPORTED_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}

# 처리 불가 형식 (감지용)
UNSUPPORTED_EXTS = {".bmp", ".tiff", ".tif", ".heic", ".heif", ".avif"}

# 이미지 크기 상한 (Claude API 제한 5MB, 여유분 포함)
MAX_FILE_SIZE_MB = 4.5

# 특수 폴더명
FOLDER_UNKNOWN     = "_미분류"
FOLDER_REAL_PERSON = "_실제인물"
FOLDER_TOO_LARGE   = "_용량초과"
FOLDER_UNSUPPORTED = "_미지원형식"

# API 호출 간격 (초) — 연속 호출 시 과부하 방지
API_CALL_DELAY = 0.4


# ── 내부 유틸 ─────────────────────────────────────────────────────────────────

def _encode_image(path: Path) -> tuple[str, str]:
    """이미지 파일을 base64로 인코딩하고 (data, media_type) 튜플을 반환한다."""
    ext_map = {
        ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
        ".png": "image/png",  ".gif": "image/gif",
        ".webp": "image/webp",
    }
    media_type = ext_map.get(path.suffix.lower(), "image/jpeg")
    with open(path, "rb") as f:
        data = base64.standard_b64encode(f.read()).decode("utf-8")
    return data, media_type


def _try_resize_image(path: Path, max_mb: float = 4.5) -> bytes | None:
    """Pillow가 설치된 경우 이미지를 리사이즈해 용량을 줄인다.
    Pillow 미설치 시 None 반환.
    """
    try:
        from PIL import Image
        import io

        with Image.open(path) as img:
            # RGBA → RGB 변환 (JPEG 저장 시 필요)
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")

            quality = 85
            while quality >= 40:
                buf = io.BytesIO()
                img.save(buf, format="JPEG", quality=quality)
                if buf.tell() / (1024 * 1024) <= max_mb:
                    return buf.getvalue()
                quality -= 15

            # 해상도 축소
            w, h = img.size
            img = img.resize((w // 2, h // 2), Image.LANCZOS)
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=75)
            return buf.getvalue()
    except ImportError:
        return None
    except Exception:
        return None


def _sanitize_folder_name(raw: str) -> str:
    """캐릭터 이름을 폴더명으로 쓸 수 있도록 정제한다."""
    name = raw.strip()
    # 특수 응답 처리
    if not name or "알 수 없" in name or "모르" in name or "없음" in name:
        return FOLDER_UNKNOWN
    if "실제인물" in name or "실제 인물" in name:
        return FOLDER_REAL_PERSON

    # Windows 금지 문자 제거
    name = re.sub(r'[\\/:*?"<>|]', "", name)
    name = name.strip(". ")
    return name if name else FOLDER_UNKNOWN


def _call_vision_api(path: Path) -> str:
    """Claude Vision API를 호출해 캐릭터 이름 문자열을 반환한다."""
    size_mb = path.stat().st_size / (1024 * 1024)

    if size_mb > MAX_FILE_SIZE_MB:
        # Pillow로 리사이즈 시도
        resized = _try_resize_image(path)
        if resized is None:
            raise ValueError(f"파일 크기 {size_mb:.1f}MB — Pillow 미설치로 리사이즈 불가")
        data = base64.standard_b64encode(resized).decode("utf-8")
        media_type = "image/jpeg"
    else:
        data, media_type = _encode_image(path)

    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    response = client.messages.create(
        model=settings.AGENT_MODEL,
        max_tokens=80,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {"type": "base64", "media_type": media_type, "data": data},
                },
                {
                    "type": "text",
                    "text": (
                        "이 이미지에 등장하는 캐릭터 이름을 알려주세요.\n"
                        "규칙:\n"
                        "- 애니메이션·게임·영화·만화 캐릭터라면 정확한 이름만 답하세요.\n"
                        "- 여러 캐릭터가 있으면 가장 주요한 캐릭터 이름 하나만 답하세요.\n"
                        "- 실제 사람(배우·가수·유튜버 등)이면 '실제인물'이라고만 답하세요.\n"
                        "- 캐릭터를 알 수 없으면 '알 수 없음'이라고만 답하세요.\n"
                        "- 이름 외에 다른 말은 절대 붙이지 마세요."
                    ),
                },
            ],
        }],
    )
    return response.content[0].text.strip()


# ── 공개 도구 함수 ────────────────────────────────────────────────────────────

def analyze_image_character(image_path: str) -> dict:
    """단일 이미지를 Claude Vision으로 분석해 캐릭터 이름을 반환한다."""
    try:
        path = Path(image_path)

        if not path.exists():
            return {"결과": "실패", "이유": "파일이 존재하지 않습니다."}

        if path.suffix.lower() in UNSUPPORTED_EXTS:
            return {
                "결과": "미지원",
                "이미지": path.name,
                "이유": f"{path.suffix} 형식은 지원하지 않습니다.",
            }

        if path.suffix.lower() not in SUPPORTED_EXTS:
            return {
                "결과": "미지원",
                "이미지": path.name,
                "이유": f"{path.suffix} 형식은 이미지 파일이 아닙니다.",
            }

        raw_name = _call_vision_api(path)
        folder_name = _sanitize_folder_name(raw_name)

        return {
            "결과": "성공",
            "이미지": path.name,
            "캐릭터": folder_name,
            "원본_응답": raw_name,
        }
    except Exception as e:
        return {"결과": "실패", "이미지": image_path, "이유": str(e)}


def preview_image_organization(folder_path: str) -> dict:
    """이미지를 실제로 이동하지 않고 캐릭터별 분류 결과를 미리 보여준다.
    실제 이동 전에 반드시 이 함수로 먼저 확인하는 것을 권장한다.
    """
    try:
        folder = Path(folder_path)
        if not folder.exists():
            return {"결과": "실패", "이유": "폴더가 존재하지 않습니다."}

        all_files  = [f for f in folder.iterdir() if f.is_file()]
        images     = [f for f in all_files if f.suffix.lower() in SUPPORTED_EXTS]
        unsupported = [f.name for f in all_files if f.suffix.lower() in UNSUPPORTED_EXTS]

        if not images:
            return {
                "결과": "완료",
                "분석_대상": 0,
                "미지원_파일": unsupported,
                "안내": "분석할 이미지 파일이 없습니다.",
            }

        preview: list[dict] = []
        for img in images:
            result = analyze_image_character(str(img))
            preview.append({
                "파일": img.name,
                "예상_폴더": result.get("캐릭터", FOLDER_UNKNOWN),
                "상태": result["결과"],
            })
            time.sleep(API_CALL_DELAY)

        summary = dict(Counter(p["예상_폴더"] for p in preview))

        return {
            "결과": "성공",
            "분석_완료": len(preview),
            "미지원_파일": unsupported,
            "캐릭터별_집계": summary,
            "파일별_예상_분류": preview,
            "다음_단계": "실제 이동하려면 organize_images_by_character(folder_path, confirm=True) 를 호출하세요.",
        }
    except Exception as e:
        return {"결과": "실패", "이유": str(e)}


def organize_images_by_character(folder_path: str, confirm: bool = False) -> dict:
    """이미지를 캐릭터별 하위 폴더로 분류·이동한다.

    Args:
        folder_path: 정리할 이미지 폴더 경로 (USB·외장하드·로컬 모두 가능)
        confirm:     True 여야 실제 이동 실행 (파괴적 작업 안전 가드)
    """
    if not confirm:
        return {
            "결과": "취소됨",
            "이유": (
                "confirm=True 로 호출해야 실제 이동이 실행됩니다. "
                "먼저 preview_image_organization 으로 미리보기를 확인하세요."
            ),
        }

    try:
        folder = Path(folder_path)
        if not folder.exists():
            return {"결과": "실패", "이유": "폴더가 존재하지 않습니다."}

        images = [f for f in folder.iterdir()
                  if f.is_file() and f.suffix.lower() in SUPPORTED_EXTS]

        if not images:
            return {"결과": "완료", "이동_파일_수": 0, "안내": "이동할 이미지 파일이 없습니다."}

        moved:  list[dict] = []
        errors: list[dict] = []

        for img in images:
            result = analyze_image_character(str(img))
            char_folder = result.get("캐릭터", FOLDER_UNKNOWN) if result["결과"] == "성공" else FOLDER_UNKNOWN

            dest_dir = folder / char_folder
            dest_dir.mkdir(parents=True, exist_ok=True)

            # 동일 파일명 충돌 처리
            dest = dest_dir / img.name
            if dest.exists():
                stem, suffix = img.stem, img.suffix
                cnt = 1
                while dest.exists():
                    dest = dest_dir / f"{stem}_{cnt}{suffix}"
                    cnt += 1

            try:
                shutil.move(str(img), str(dest))
                moved.append({
                    "파일": img.name,
                    "이동된_폴더": char_folder,
                    "최종_경로": str(dest),
                })
            except Exception as e:
                errors.append({"파일": img.name, "이유": str(e)})

            time.sleep(API_CALL_DELAY)

        summary = dict(Counter(m["이동된_폴더"] for m in moved))

        return {
            "결과": "성공",
            "이동_완료": len(moved),
            "실패": len(errors),
            "캐릭터별_집계": summary,
            "상세": moved,
            "오류": errors if errors else None,
        }
    except Exception as e:
        return {"결과": "실패", "이유": str(e)}
