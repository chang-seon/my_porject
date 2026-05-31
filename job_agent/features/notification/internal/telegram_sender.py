from __future__ import annotations
import json as _json
import os
import urllib.request
from dotenv import load_dotenv

load_dotenv()

_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")


def send_message(text: str, chat_id: str | None = None, parse_mode: str = "HTML") -> dict:
    """텔레그램 메시지를 발송한다."""
    try:
        token = _BOT_TOKEN
        cid = chat_id or _CHAT_ID
        if not token:
            return {"결과": "실패", "이유": "TELEGRAM_BOT_TOKEN 미설정"}
        if not cid:
            return {"결과": "실패", "이유": "TELEGRAM_CHAT_ID 미설정"}
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = _json.dumps({"chat_id": cid, "text": text, "parse_mode": parse_mode}).encode()
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = _json.loads(resp.read())
        msg_id = data.get("result", {}).get("message_id", "")
        return {"결과": "성공", "message_id": str(msg_id)}
    except Exception as e:
        return {"결과": "실패", "이유": str(e)}


def send_from_template(template_name: str, context: dict, chat_id: str | None = None) -> dict:
    """템플릿 파일로 메시지를 렌더링해 발송한다."""
    try:
        from pathlib import Path
        tpl_path = Path(__file__).parent / "templates" / f"{template_name}.txt"
        if not tpl_path.exists():
            return {"결과": "실패", "이유": f"템플릿 없음: {template_name}"}
        template = tpl_path.read_text(encoding="utf-8")
        text = template.format(**context)
        return send_message(text, chat_id=chat_id)
    except KeyError as e:
        return {"결과": "실패", "이유": f"템플릿 변수 누락: {e}"}
    except Exception as e:
        return {"결과": "실패", "이유": str(e)}
