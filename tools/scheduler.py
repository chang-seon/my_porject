"""스케줄러 도구 - 작업 예약 및 반복 실행 관리 기능을 제공한다."""

import schedule
import time
import threading
from datetime import datetime
from typing import Callable

_jobs: list[dict] = []


def add_job(func: Callable, interval_seconds: int, label: str = "") -> dict:
    """주기적으로 실행할 작업을 등록한다."""
    job = schedule.every(interval_seconds).seconds.do(func)
    entry = {
        "label": label or func.__name__,
        "interval_seconds": interval_seconds,
        "등록시각": datetime.now().isoformat(),
        "job": job,
    }
    _jobs.append(entry)
    return {"결과": "성공", "작업": label, "주기(초)": interval_seconds}


def remove_job(label: str) -> dict:
    """등록된 작업을 레이블로 찾아 제거한다."""
    for entry in _jobs:
        if entry["label"] == label:
            schedule.cancel_job(entry["job"])
            _jobs.remove(entry)
            return {"결과": "성공", "제거된 작업": label}
    return {"결과": "실패", "이유": f"레이블 '{label}' 에 해당하는 작업이 없습니다."}


def list_jobs() -> dict:
    """현재 등록된 모든 작업 목록을 반환한다."""
    return {
        "작업 수": len(_jobs),
        "목록": [{"label": j["label"], "주기(초)": j["interval_seconds"]} for j in _jobs],
    }


def run_scheduler(blocking: bool = False):
    """스케줄러를 실행한다. blocking=False 이면 백그라운드 스레드로 실행한다."""
    if blocking:
        while True:
            schedule.run_pending()
            time.sleep(1)
    else:
        def _loop():
            while True:
                schedule.run_pending()
                time.sleep(1)

        thread = threading.Thread(target=_loop, daemon=True)
        thread.start()
        return thread
