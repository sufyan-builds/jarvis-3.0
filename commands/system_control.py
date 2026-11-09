"""Windows system commands for Jarvis.

This module is a pure "doer": every method performs one action (open an app,
report CPU usage, lock the PC, ...) and returns a short spoken confirmation.
It does NOT try to understand natural language -- that job belongs to
core/command_handler.py, which decides *when* to call these methods.

Keeping parsing and doing separate means there is only one place (the
command handler) that decides what a sentence means, instead of two
different regex routers disagreeing with each other.
"""

from __future__ import annotations

import ctypes
import datetime
import os
import socket
import subprocess
import webbrowser
from pathlib import Path
import tkinter as tk
import tkinter as tk

import psutil
import pyautogui

try:
    import screen_brightness_control as sbc
except ImportError:
    sbc = None


# Local Windows apps Jarvis knows how to open, and the command used to open
# them. Using `start` / bare executable names lets Windows resolve most of
# these from PATH without needing hardcoded install paths.
APP_COMMANDS = {
    "notepad": ["notepad.exe"],
    "calculator": ["calc.exe"],
    "paint": ["mspaint.exe"],
    "explorer": ["explorer.exe"],
    "file explorer": ["explorer.exe"],
    "terminal": ["wt.exe"],
    "powershell": ["powershell.exe"],
    "cmd": ["cmd.exe"],
    "chrome": ["cmd", "/c", "start", "chrome"],
    "edge": ["cmd", "/c", "start", "msedge"],
    "vscode": ["cmd", "/c", "start", "code"],
    "vs code": ["cmd", "/c", "start", "code"],
    "visual studio code": ["cmd", "/c", "start", "code"],
    "spotify": ["cmd", "/c", "start", "spotify"],
}

# Process names (as seen in Task Manager) used to close an app by name.
APP_PROCESS_NAMES = {
    "notepad": "notepad.exe",
    "calculator": "CalculatorApp.exe",
    "paint": "mspaint.exe",
    "chrome": "chrome.exe",
    "edge": "msedge.exe",
    "vscode": "Code.exe",
    "vs code": "Code.exe",
    "spotify": "Spotify.exe",
}

WEBSITE_COMMANDS = {
    "google": "https://www.google.com",
    "youtube": "https://www.youtube.com",
    "github": "https://www.github.com",
    "stackoverflow": "https://stackoverflow.com",
    "linkedin": "https://www.linkedin.com",
    "gmail": "https://mail.google.com",
    "chatgpt": "https://chat.openai.com",
    "grok": "https://grok.com",
    "groq": "https://console.groq.com",
    "docs": "https://docs.google.com",
    "drive": "https://drive.google.com",
}


class SystemController:
    """Executes local PC commands hands-free."""

    # ---------- Applications ----------

    def open_app(self, name: str) -> str:
        command = APP_COMMANDS.get(name)
        if not command:
            return f"I don't know how to open {name} yet."
        try:
            subprocess.Popen(command, shell=False)
            return f"Opening {name.title()}."
        except Exception as exc:
            return f"I couldn't open {name}: {exc}"

    def close_app(self, name: str) -> str:
        process_name = APP_PROCESS_NAMES.get(name)
        if not process_name:
            return f"I don't know the process name for {name}."
        closed_any = False
        for proc in psutil.process_iter(["name"]):
            if proc.info.get("name", "").lower() == process_name.lower():
                try:
                    proc.terminate()
                    closed_any = True
                except Exception:
                    continue
        return f"Closed {name.title()}." if closed_any else f"{name.title()} does not appear to be running."

    def open_website(self, name: str) -> str:
        url = WEBSITE_COMMANDS.get(name)
        if not url:
            return f"I don't have a shortcut for {name}."
        webbrowser.open_new_tab(url)
        return f"Opening {name.title()}."

    def open_control_panel(self) -> str:
        try:
            subprocess.Popen(["control"], shell=False)
            return "Opening Control Panel."
        except Exception as exc:
            return f"I couldn't open Control Panel: {exc}"

    def open_settings(self) -> str:
        try:
            os.startfile("ms-settings:")
            return "Opening Settings."
        except Exception as exc:
            return f"I couldn't open Settings: {exc}"

    def open_task_manager(self) -> str:
        try:
            subprocess.Popen(["taskmgr"], shell=False)
            return "Opening Task Manager."
        except Exception as exc:
            return f"I couldn't open Task Manager: {exc}"

    def open_device_manager(self) -> str:
        try:
            subprocess.Popen(["devmgmt.msc"], shell=True)
            return "Opening Device Manager."
        except Exception as exc:
            return f"I couldn't open Device Manager: {exc}"

    def open_registry_editor(self) -> str:
        try:
            subprocess.Popen(["regedit"], shell=False)
            return "Opening Registry Editor."
        except Exception as exc:
            return f"I couldn't open Registry Editor: {exc}"

    def open_services(self) -> str:
        try:
            subprocess.Popen(["services.msc"], shell=True)
            return "Opening Services."
        except Exception as exc:
            return f"I couldn't open Services: {exc}"

    def open_cmd(self) -> str:
        try:
            subprocess.Popen(["cmd"], shell=False)
            return "Opening Command Prompt."
        except Exception as exc:
            return f"I couldn't open Command Prompt: {exc}"

    def open_powershell(self) -> str:
        try:
            subprocess.Popen(["powershell"], shell=False)
            return "Opening PowerShell."
        except Exception as exc:
            return f"I couldn't open PowerShell: {exc}"

    def open_terminal(self) -> str:
        try:
            subprocess.Popen(["wt"], shell=False)
            return "Opening Windows Terminal."
        except Exception as exc:
            return f"I couldn't open Windows Terminal: {exc}"

    def switch_window(self) -> str:
        try:
            pyautogui.hotkey("alt", "tab")
            return "Switching windows."
        except Exception as exc:
            return f"I couldn't switch windows: {exc}"

    def show_desktop(self) -> str:
        try:
            pyautogui.hotkey("win", "d")
            return "Showing the desktop."
        except Exception as exc:
            return f"I couldn't show the desktop: {exc}"

    def open_task_view(self) -> str:
        try:
            pyautogui.hotkey("win", "tab")
            return "Opening Task View."
        except Exception as exc:
            return f"I couldn't open Task View: {exc}"

    def screenshot(self) -> str:
        try:
            screenshots_dir = Path.home() / "Pictures" / "Screenshots"
            screenshots_dir.mkdir(parents=True, exist_ok=True)
            filename = datetime.datetime.now().strftime("screenshot_%Y%m%d_%H%M%S.png")
            path = screenshots_dir / filename
            pyautogui.screenshot(str(path))
            return f"Screenshot saved to {path}."
        except Exception as exc:
            return f"I couldn't take a screenshot: {exc}"

    def _clipboard_root(self) -> tk.Tk:
        root = tk.Tk()
        root.withdraw()
        return root

    def start_screen_recording(self) -> str:
        try:
            pyautogui.hotkey("win", "alt", "r")
            return "Starting screen recording."
        except Exception as exc:
            return f"I couldn't start screen recording: {exc}"

    def stop_screen_recording(self) -> str:
        try:
            pyautogui.hotkey("win", "alt", "r")
            return "Stopping screen recording."
        except Exception as exc:
            return f"I couldn't stop screen recording: {exc}"

    def copy_to_clipboard(self, text: str) -> str:
        try:
            root = self._clipboard_root()
            root.clipboard_clear()
            root.clipboard_append(text)
            root.update()
            root.destroy()
            return "Copied text to the clipboard."
        except Exception as exc:
            return f"I couldn't copy to the clipboard: {exc}"

    def read_clipboard(self) -> str:
        try:
            root = self._clipboard_root()
            text = root.clipboard_get().strip()
            root.destroy()
            return text if text else "The clipboard is empty."
        except Exception as exc:
            return f"I couldn't read the clipboard: {exc}"

    def clear_clipboard(self) -> str:
        try:
            root = self._clipboard_root()
            root.clipboard_clear()
            root.update()
            root.destroy()
            return "Clipboard cleared."
        except Exception as exc:
            return f"I couldn't clear the clipboard: {exc}"

    def _clipboard_root(self) -> tk.Tk:
        root = tk.Tk()
        root.withdraw()
        return root

    def start_screen_recording(self) -> str:
        try:
            pyautogui.hotkey("win", "alt", "r")
            return "Starting screen recording."
        except Exception as exc:
            return f"I couldn't start screen recording: {exc}"

    def stop_screen_recording(self) -> str:
        try:
            pyautogui.hotkey("win", "alt", "r")
            return "Stopping screen recording."
        except Exception as exc:
            return f"I couldn't stop screen recording: {exc}"

    def copy_to_clipboard(self, text: str) -> str:
        try:
            root = self._clipboard_root()
            root.clipboard_clear()
            root.clipboard_append(text)
            root.update()
            root.destroy()
            return "Copied text to the clipboard."
        except Exception as exc:
            return f"I couldn't copy to the clipboard: {exc}"

    def read_clipboard(self) -> str:
        try:
            root = self._clipboard_root()
            text = root.clipboard_get().strip()
            root.destroy()
            return text if text else "The clipboard is empty."
        except Exception as exc:
            return f"I couldn't read the clipboard: {exc}"

    def clear_clipboard(self) -> str:
        try:
            root = self._clipboard_root()
            root.clipboard_clear()
            root.update()
            root.destroy()
            return "Clipboard cleared."
        except Exception as exc:
            return f"I couldn't clear the clipboard: {exc}"

    def empty_recycle_bin(self) -> str:
        try:
            shell32 = ctypes.windll.shell32
            shell32.SHEmptyRecycleBinW(None, None, 0x00000007)
            return "Recycle Bin emptied."
        except Exception as exc:
            return f"I couldn't empty the Recycle Bin: {exc}"

    # ---------- Power ----------

    def shutdown(self) -> str:
        os.system("shutdown /s /t 5")
        return "Shutting down the system in 5 seconds."

    def restart(self) -> str:
        os.system("shutdown /r /t 5")
        return "Restarting the system in 5 seconds."

    def sleep(self) -> str:
        os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
        return "Putting the system to sleep."

    def lock(self) -> str:
        try:
            ctypes.windll.user32.LockWorkStation()
            return "Locking the PC."
        except Exception as exc:
            return f"I couldn't lock the PC: {exc}"

    # ---------- Volume / Brightness ----------

    def volume_up(self) -> str:
        pyautogui.press("volumeup", presses=5)
        return "Volume increased."

    def volume_down(self) -> str:
        pyautogui.press("volumedown", presses=5)
        return "Volume decreased."

    def mute(self) -> str:
        pyautogui.press("volumemute")
        return "Audio muted."

    def set_brightness(self, percent: int) -> str:
        if sbc is None:
            return "Brightness control isn't installed. Run: pip install screen-brightness-control"
        try:
            sbc.set_brightness(max(0, min(100, percent)))
            return f"Brightness set to {percent} percent."
        except Exception as exc:
            return f"I couldn't change the brightness: {exc}"

    # ---------- System information ----------

    def current_time(self) -> str:
        return datetime.datetime.now().strftime("%I:%M %p")

    def current_date(self) -> str:
        return f"Today is {datetime.datetime.now().strftime('%A, %B %d, %Y')}."

    def cpu_usage(self) -> str:
        return f"{psutil.cpu_percent(interval=0.5)}"

    def ram_usage(self) -> str:
        return f"{psutil.virtual_memory().percent}"

    def storage_usage(self) -> str:
        usage = psutil.disk_usage(os.sep)
        free_gb = usage.free / (1024 ** 3)
        total_gb = usage.total / (1024 ** 3)
        return f"You have {free_gb:.1f} gigabytes free out of {total_gb:.1f} gigabytes total."

    def battery_percentage(self):
        battery = psutil.sensors_battery()
        if battery is None:
            return None
        return battery.percent

    def ip_address(self) -> str:
        try:
            hostname = socket.gethostname()
            ip = socket.gethostbyname(hostname)
            return f"Your local IP address is {ip}."
        except Exception as exc:
            return f"I couldn't determine the IP address: {exc}"

    def wifi_status(self) -> str:
        try:
            result = subprocess.run(
                ["netsh", "wlan", "show", "interfaces"],
                capture_output=True, text=True, timeout=5,
            )
            output = result.stdout
            if "State" in output and "connected" in output.lower():
                for line in output.splitlines():
                    if "SSID" in line and "BSSID" not in line:
                        return f"Connected to Wi-Fi network: {line.split(':', 1)[1].strip()}."
                return "Wi-Fi is connected."
            return "Wi-Fi is not currently connected."
        except Exception as exc:
            return f"I couldn't check Wi-Fi status: {exc}"

    def running_processes(self, top_n: int = 5) -> str:
        procs = sorted(
            psutil.process_iter(["name", "cpu_percent"]),
            key=lambda p: p.info.get("cpu_percent") or 0,
            reverse=True,
        )[:top_n]
        names = [p.info.get("name", "unknown") for p in procs]
        return "Top running processes: " + ", ".join(names) + "."
