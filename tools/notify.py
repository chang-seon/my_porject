"""알림 도구 - 윈도우 토스트 알림 및 콘솔 알림을 전송한다."""

import platform
import subprocess
from datetime import datetime


def send_notification(title: str, message: str) -> dict:
    """데스크톱 알림을 전송한다. Windows/macOS/Linux 모두 지원한다."""
    system = platform.system()
    timestamp = datetime.now().strftime("%H:%M:%S")

    try:
        if system == "Windows":
            # PowerShell 을 이용한 윈도우 토스트 알림
            script = (
                f"[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType=WindowsRuntime] | Out-Null; "
                f"$template = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02); "
                f"$template.GetElementsByTagName('text')[0].AppendChild($template.CreateTextNode('{title}')) | Out-Null; "
                f"$template.GetElementsByTagName('text')[1].AppendChild($template.CreateTextNode('{message}')) | Out-Null; "
                f"$toast = [Windows.UI.Notifications.ToastNotification]::new($template); "
                f"[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier('AgentAI').Show($toast)"
            )
            subprocess.run(["powershell", "-Command", script], capture_output=True)

        elif system == "Darwin":
            subprocess.run(
                ["osascript", "-e", f'display notification "{message}" with title "{title}"'],
                capture_output=True,
            )
        else:
            subprocess.run(["notify-send", title, message], capture_output=True)

        return {"결과": "성공", "제목": title, "내용": message, "시각": timestamp}

    except Exception as e:
        return {"결과": "실패", "이유": str(e)}


def log_alert(level: str, message: str) -> dict:
    """콘솔에 레벨별 알림 메시지를 출력한다."""
    colors = {"INFO": "\033[94m", "WARNING": "\033[93m", "ERROR": "\033[91m"}
    reset = "\033[0m"
    color = colors.get(level.upper(), "")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{color}[{timestamp}] [{level.upper()}] {message}{reset}")
    return {"레벨": level, "메시지": message, "시각": timestamp}
