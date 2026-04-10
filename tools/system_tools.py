"""시스템 도구 - CPU·RAM·디스크 모니터링 및 프로세스 관리 기능을 제공한다."""

import psutil
from datetime import datetime


def get_system_status() -> dict:
    """현재 시스템 상태(CPU·메모리·디스크)를 반환한다."""
    cpu_percent = psutil.cpu_percent(interval=1)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("/")

    return {
        "timestamp": datetime.now().isoformat(),
        "cpu": {
            "사용률(%)": cpu_percent,
            "코어 수": psutil.cpu_count(),
        },
        "memory": {
            "전체(GB)": round(mem.total / 1e9, 2),
            "사용중(GB)": round(mem.used / 1e9, 2),
            "사용률(%)": mem.percent,
        },
        "disk": {
            "전체(GB)": round(disk.total / 1e9, 2),
            "사용중(GB)": round(disk.used / 1e9, 2),
            "여유(GB)": round(disk.free / 1e9, 2),
            "사용률(%)": disk.percent,
        },
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
