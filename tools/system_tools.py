"""시스템 도구 - CPU·RAM·디스크 모니터링 및 프로세스 관리 기능을 제공한다."""

import platform
import string
import psutil
from datetime import datetime
from config import settings


def _get_all_disks() -> list:
    """사용 가능한 모든 드라이브의 디스크 정보를 반환한다."""
    disks = []
    if platform.system() == "Windows":
        for letter in string.ascii_uppercase:
            path = f"{letter}:/"
            try:
                usage = psutil.disk_usage(path)
                disks.append({
                    "드라이브":   f"{letter}:",
                    "전체(GB)":  round(usage.total / 1e9, 2),
                    "사용중(GB)": round(usage.used / 1e9, 2),
                    "여유(GB)":  round(usage.free / 1e9, 2),
                    "사용률(%)": usage.percent,
                })
            except (PermissionError, OSError, FileNotFoundError):
                pass
    else:
        usage = psutil.disk_usage("/")
        disks.append({
            "드라이브":   "/",
            "전체(GB)":  round(usage.total / 1e9, 2),
            "사용중(GB)": round(usage.used / 1e9, 2),
            "여유(GB)":  round(usage.free / 1e9, 2),
            "사용률(%)": usage.percent,
        })
    return disks


def get_system_status() -> dict:
    """현재 시스템 상태(CPU·메모리·전체 드라이브)를 반환한다."""
    cpu_percent = psutil.cpu_percent(interval=1)
    mem = psutil.virtual_memory()

    return {
        "timestamp": datetime.now().isoformat(),
        "cpu": {
            "사용률(%)": cpu_percent,
            "코어 수":   psutil.cpu_count(),
        },
        "memory": {
            "전체(GB)":  round(mem.total / 1e9, 2),
            "사용중(GB)": round(mem.used / 1e9, 2),
            "사용률(%)": mem.percent,
        },
        "디스크": _get_all_disks(),
    }


def get_pc_overview() -> dict:
    """PC 전체 개요 — 사용자 정보, 주요 폴더 경로, 드라이브 현황을 반환한다."""
    return {
        "사용자명":    settings.USERNAME,
        "홈 디렉터리": str(settings.HOME_DIR),
        "주요 폴더": {
            "바탕화면": str(settings.DESKTOP_DIR),
            "다운로드": str(settings.DOWNLOADS_DIR),
            "문서":    str(settings.DOCUMENTS_DIR),
            "사진":    str(settings.PICTURES_DIR),
            "음악":    str(settings.MUSIC_DIR),
            "동영상":  str(settings.VIDEOS_DIR),
        },
        "드라이브": _get_all_disks(),
        "운영체제": platform.platform(),
        "Python":  platform.python_version(),
    }


def list_top_processes(n: int = 10) -> dict:
    """CPU 사용량 기준 상위 N개 프로세스 목록을 반환한다."""
    procs = []
    for proc in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]):
        try:
            procs.append(proc.info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    top = sorted(procs, key=lambda p: p.get("cpu_percent") or 0, reverse=True)[:n]
    return {"프로세스 목록": top}


def kill_process(pid: int) -> dict:
    """지정한 PID 의 프로세스를 종료한다. 위험 작업이므로 확인 후 호출한다."""
    try:
        proc = psutil.Process(pid)
        name = proc.name()
        proc.terminate()
        return {"결과": "성공", "pid": pid, "이름": name}
    except psutil.NoSuchProcess:
        return {"결과": "실패", "이유": f"PID {pid} 프로세스를 찾을 수 없습니다."}
    except psutil.AccessDenied:
        return {"결과": "실패", "이유": f"PID {pid} 프로세스 종료 권한이 없습니다."}


def get_network_stats() -> dict:
    """네트워크 I/O 통계를 반환한다."""
    net = psutil.net_io_counters()
    return {
        "송신(MB)": round(net.bytes_sent / 1e6, 2),
        "수신(MB)": round(net.bytes_recv / 1e6, 2),
    }
