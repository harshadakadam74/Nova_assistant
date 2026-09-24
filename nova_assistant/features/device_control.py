"""Desktop and Android device-control helpers for Nova."""
import datetime
import os
import platform
import shutil
import subprocess
import webbrowser
from urllib.parse import quote_plus

import psutil

try:
    import pyautogui
except ImportError:
    pyautogui = None

try:
    import screen_brightness_control as sbc
except ImportError:
    sbc = None

_IS_ANDROID = platform.system() == "Linux" and "ANDROID_ROOT" in os.environ
_pending_power_action = None

WEBSITES = {
    "google": "https://www.google.com",
    "youtube": "https://www.youtube.com",
    "gmail": "https://mail.google.com",
    "github": "https://github.com",
    "instagram": "https://www.instagram.com",
    "facebook": "https://www.facebook.com",
    "whatsapp": "https://web.whatsapp.com",
    "linkedin": "https://www.linkedin.com",
    "chatgpt": "https://chatgpt.com",
    "spotify": "https://open.spotify.com",
}

COMMON_APPS = {
    "camera": "android.intent.action.CAMERA",
    "youtube": "com.google.android.youtube",
    "maps": "com.google.android.apps.maps",
    "gmail": "com.google.android.gm",
    "settings": "android.settings.SETTINGS",
    "whatsapp": "com.whatsapp",
}

WINDOWS_APPS = {
    "notepad": "notepad.exe",
    "calculator": "calc.exe",
    "calc": "calc.exe",
    "paint": "mspaint.exe",
    "cmd": "cmd.exe",
    "command prompt": "cmd.exe",
    "powershell": "powershell.exe",
    "explorer": "explorer.exe",
    "file explorer": "explorer.exe",
    "task manager": "taskmgr.exe",
    "control panel": "control.exe",
    "wordpad": "write.exe",
    "chrome": "chrome.exe",
    "google chrome": "chrome.exe",
    "edge": "msedge.exe",
    "microsoft edge": "msedge.exe",
    "spotify": "Spotify.exe",
    "vs code": "Code.exe",
    "vscode": "Code.exe",
    "visual studio code": "Code.exe",
}

APP_PATHS = {
    "chrome": [
        r"%ProgramFiles%\Google\Chrome\Application\chrome.exe",
        r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe",
    ],
    "edge": [
        r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe",
        r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe",
    ],
    "vscode": [r"%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe"],
    "visual studio code": [r"%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe"],
    "spotify": [r"%APPDATA%\Spotify\Spotify.exe"],
    "word": [r"%ProgramFiles%\Microsoft Office\root\Office16\WINWORD.EXE"],
    "excel": [r"%ProgramFiles%\Microsoft Office\root\Office16\EXCEL.EXE"],
    "powerpoint": [r"%ProgramFiles%\Microsoft Office\root\Office16\POWERPNT.EXE"],
}


def open_website(name):
    key = name.lower().strip()
    url = WEBSITES.get(key, name.strip())
    if not url:
        return f"I don't know the website {name}"
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"
    webbrowser.open(url)
    return f"Opening {key}"


def open_application(name):
    name = name.lower().strip()

    if name in WEBSITES:
        return open_website(name)

    for app_name, paths in APP_PATHS.items():
        if app_name == name:
            for path in paths:
                expanded = os.path.expandvars(path)
                if os.path.exists(expanded):
                    try:
                        subprocess.Popen(expanded)
                        return f"Opening {name}"
                    except OSError as error:
                        return f"Could not open {name}: {error}"

    for app_name, executable in WINDOWS_APPS.items():
        if app_name == name:
            resolved = shutil.which(executable) or executable
            try:
                subprocess.Popen(resolved)
                return f"Opening {name}"
            except OSError as error:
                return f"Could not open {name}: {error}"

    candidate = shutil.which(name)
    if candidate:
        try:
            subprocess.Popen(candidate)
            return f"Opening {name}"
        except OSError as error:
            return f"Could not open {name}: {error}"

    try:
        subprocess.Popen(["cmd", "/c", "start", "", name], shell=False)
        return f"Trying to open {name}"
    except OSError as error:
        return f"Could not open {name}: {error}"


def open_windows_app(name):
    return open_application(name)


def open_installed_app(name):
    name = name.lower().strip()
    for app_name, paths in APP_PATHS.items():
        if app_name == name:
            for path in paths:
                expanded = os.path.expandvars(path)
                if os.path.exists(expanded):
                    try:
                        subprocess.Popen(expanded)
                        return f"Opening {name}"
                    except OSError as error:
                        return f"Could not open {name}: {error}"
    return open_application(name)


def open_folder(folder):
    folders = {
        "desktop": os.path.join(os.path.expanduser("~"), "Desktop"),
        "downloads": os.path.join(os.path.expanduser("~"), "Downloads"),
        "documents": os.path.join(os.path.expanduser("~"), "Documents"),
        "pictures": os.path.join(os.path.expanduser("~"), "Pictures"),
        "videos": os.path.join(os.path.expanduser("~"), "Videos"),
        "music": os.path.join(os.path.expanduser("~"), "Music"),
    }
    folder = folder.lower().strip()
    path = folders.get(folder)
    if not path or not os.path.exists(path):
        return None
    try:
        os.startfile(path)
        return f"Opening {folder}"
    except AttributeError:
        subprocess.Popen(["explorer.exe", path])
        return f"Opening {folder}"
    except OSError as error:
        return f"Could not open {folder}: {error}"


def close_application(name):
    process_names = {
        "chrome": "chrome.exe",
        "google chrome": "chrome.exe",
        "edge": "msedge.exe",
        "microsoft edge": "msedge.exe",
        "vscode": "Code.exe",
        "visual studio code": "Code.exe",
        "vs code": "Code.exe",
        "notepad": "notepad.exe",
        "calculator": "CalculatorApp.exe",
        "paint": "mspaint.exe",
        "spotify": "Spotify.exe",
        "cmd": "cmd.exe",
        "command prompt": "cmd.exe",
        "powershell": "powershell.exe",
    }
    process = process_names.get(name.lower().strip())
    if not process:
        return f"I don't know how to close {name}"
    result = subprocess.run(["taskkill", "/IM", process, "/F"], capture_output=True, text=True)
    if result.returncode == 0:
        return f"Closed {name}"
    return f"{name} was not running."


def close_app(name):
    return close_application(name)


def volume_up():
    if pyautogui is None:
        return "Install PyAutoGUI to control volume."
    for _ in range(5):
        pyautogui.press("volumeup")
    return "Volume increased"


def volume_down():
    if pyautogui is None:
        return "Install PyAutoGUI to control volume."
    for _ in range(5):
        pyautogui.press("volumedown")
    return "Volume decreased"


def mute_volume():
    if pyautogui is None:
        return "Install PyAutoGUI to control volume."
    pyautogui.press("volumemute")
    return "Volume muted"


def brightness_change(direction):
    if _IS_ANDROID:
        return f"Brightness turned {direction}."
    if sbc is None:
        return "Install screen-brightness-control to change brightness."
    try:
        current = sbc.get_brightness()[0]
        new_value = min(current + 10, 100) if direction == "up" else max(current - 10, 0)
        sbc.set_brightness(new_value)
        return f"Brightness {new_value} percent"
    except Exception as error:
        return f"Could not change brightness: {error}"


def take_screenshot():
    if pyautogui is None:
        return "Install PyAutoGUI to take screenshots."
    try:
        folder = os.path.join(os.path.expanduser("~"), "Pictures", "Nova Screenshots")
        os.makedirs(folder, exist_ok=True)
        path = os.path.join(folder, datetime.datetime.now().strftime("Nova_%Y%m%d_%H%M%S.png"))
        pyautogui.screenshot().save(path)
        return f"Screenshot saved to {path}"
    except Exception as error:
        return f"Screenshot failed: {error}"


def lock_computer():
    try:
        subprocess.run(["rundll32.exe", "user32.dll,LockWorkStation"], check=False)
        return "Computer locked"
    except OSError as error:
        return f"Could not lock computer: {error}"


def request_power_action(action):
    global _pending_power_action
    _pending_power_action = action
    return f"Please say confirm {action} to continue, or cancel."


def confirm_power_action():
    global _pending_power_action
    if _pending_power_action not in {"shutdown", "restart"}:
        return "There is no pending shutdown or restart."
    action = _pending_power_action
    _pending_power_action = None
    subprocess.run(["shutdown", "/s" if action == "shutdown" else "/r", "/t", "30"], check=False)
    return f"Computer will {action} in 30 seconds."


def cancel_shutdown():
    global _pending_power_action
    _pending_power_action = None
    subprocess.run(["shutdown", "/a"], check=False)
    return "Shutdown cancelled"


def open_settings(kind=None):
    targets = {
        None: "ms-settings:",
        "wifi": "ms-settings:network-wifi",
        "wi-fi": "ms-settings:network-wifi",
        "bluetooth": "ms-settings:bluetooth",
        "display": "ms-settings:display",
        "sound": "ms-settings:sound",
        "network": "ms-settings:network",
    }
    target = targets.get(kind)
    if target is None:
        target = "ms-settings:"
    try:
        os.startfile(target)
    except AttributeError:
        subprocess.Popen(["cmd", "/c", "start", "", target], shell=False)
    label = "Wi-Fi" if kind in {"wifi", "wi-fi"} else (kind.capitalize() if kind else "Windows")
    return f"Opening {label} settings"


def open_recycle_bin():
    try:
        subprocess.Popen(["explorer.exe", "shell:RecycleBinFolder"])
        return "Opening Recycle Bin"
    except OSError as error:
        return f"Could not open Recycle Bin: {error}"


def google_search(query):
    query = query.strip()
    if not query:
        return "What should I search for?"
    webbrowser.open(f"https://www.google.com/search?q={quote_plus(query)}")
    return f"Searching Google for {query}"


def youtube_search(query):
    query = query.strip()
    if not query:
        return "What should I search on YouTube?"
    webbrowser.open(f"https://www.youtube.com/results?search_query={quote_plus(query)}")
    return f"Searching YouTube for {query}"


def show_desktop():
    if pyautogui is None:
        return "Install PyAutoGUI to show the desktop."
    pyautogui.hotkey("win", "d")
    return "Showing desktop"


def open_run():
    if pyautogui is None:
        return "Install PyAutoGUI to open Run."
    pyautogui.hotkey("win", "r")
    return "Opening Run"


def system_info():
    cpu = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("C:\\")
    return (
        f"CPU usage {cpu} percent. "
        f"Memory usage {memory.percent} percent. "
        f"Disk usage {disk.percent} percent."
    )


def current_time():
    return datetime.datetime.now().strftime("The time is %I:%M %p")


def current_date():
    return datetime.datetime.now().strftime("Today is %A, %d %B %Y")


def volume_change(direction):
    return volume_up() if direction == "up" else volume_down()


def open_app(command):
    raw = command.lower().strip()
    command = raw.replace("open the ", "open ").replace("open d ", "open ").replace("please ", "")

    if command in {"youtube", "google", "github", "gmail", "instagram", "facebook", "whatsapp", "linkedin", "chatgpt"}:
        return open_website(command)
    if "open wifi" in command or "open wi-fi" in command:
        return open_settings("wifi")
    if "open bluetooth" in command:
        return open_settings("bluetooth")
    if "open display settings" in command:
        return open_settings("display")
    if "open sound settings" in command:
        return open_settings("sound")
    if "open network settings" in command:
        return open_settings("network")
    if "open settings" in command:
        return open_settings()
    if "recycle bin" in command or "open trash" in command:
        return open_recycle_bin()
    if "show desktop" in command or "go to desktop" in command:
        return show_desktop()
    if "open run" in command or "run command" in command:
        return open_run()
    if command.startswith("open "):
        target = command[5:].strip()
        if target in WEBSITES:
            return open_website(target)
        return open_installed_app(target) if target in APP_PATHS else open_windows_app(target)
    if command.startswith("close "):
        return close_application(command[6:].strip())
    if "volume up" in command or "increase volume" in command:
        return volume_up()
    if "volume down" in command or "decrease volume" in command:
        return volume_down()
    if "mute" in command:
        return mute_volume()
    if "brightness up" in command or "increase brightness" in command:
        return brightness_change("up")
    if "brightness down" in command or "decrease brightness" in command:
        return brightness_change("down")
    if "screenshot" in command or "capture screen" in command or "take screenshot" in command:
        return take_screenshot()
    if "lock computer" in command or "lock pc" in command or "lock my computer" in command:
        return lock_computer()
    if "cancel shutdown" in command or "cancel shut down" in command:
        return cancel_shutdown()
    if "confirm shutdown" in command or "confirm restart" in command:
        return confirm_power_action()
    if "shutdown" in command or "shut down" in command:
        return request_power_action("shutdown")
    if "restart" in command or "reboot" in command:
        return request_power_action("restart")
    if command.startswith("search google for "):
        return google_search(command[18:])
    if command.startswith("google "):
        return google_search(command[7:])
    if command.startswith("search youtube for "):
        return youtube_search(command[20:])
    if command.startswith("play "):
        return youtube_search(command[5:])
    if command in {"time", "current time"} or "what time" in command:
        return current_time()
    if command in {"date", "current date"} or "what date" in command or "today's date" in command:
        return current_date()
    if "system info" in command or "system information" in command or "computer status" in command:
        return system_info()
    return ""


def handle_device_command(command):
    command = command.lower().strip()

    replacements = {
        "open d youtube": "open youtube",
        "open the youtube": "open youtube",
        "open the google": "open google",
        "open d google": "open google",
        "open the chrome": "open chrome",
        "open d chrome": "open chrome",
        "open the edge": "open edge",
        "open d edge": "open edge",
    }
    for old, new in replacements.items():
        if command == old:
            command = new

    if command.startswith("open "):
        target = command[5:].strip()
        if target in WEBSITES or target in APP_PATHS or target in WINDOWS_APPS:
            return open_application(target)
        return open_folder(target) or open_application(target)

    if command.startswith("close "):
        return close_application(command[6:].strip())

    if "volume up" in command or "increase volume" in command:
        return volume_up()
    if "volume down" in command or "decrease volume" in command:
        return volume_down()
    if "mute volume" in command or command == "mute":
        return mute_volume()
    if "brightness up" in command or "increase brightness" in command:
        return brightness_change("up")
    if "brightness down" in command or "decrease brightness" in command:
        return brightness_change("down")
    if "take screenshot" in command or "screenshot" == command or "capture screen" in command:
        return take_screenshot()
    if command in {"lock computer", "lock pc", "lock my computer"}:
        return lock_computer()
    if command in {"shutdown computer", "shutdown pc", "shut down computer", "shut down pc"}:
        return request_power_action("shutdown")
    if command in {"restart computer", "restart pc", "reboot computer"}:
        return request_power_action("restart")
    if command in {"cancel shutdown", "cancel restart"}:
        return cancel_shutdown()
    if command in {"settings", "open settings", "windows settings"}:
        return open_settings()
    if "open wifi" in command or "wifi settings" in command:
        return open_settings("wifi")
    if "open bluetooth" in command or "bluetooth settings" in command:
        return open_settings("bluetooth")
    if "display settings" in command:
        return open_settings("display")
    if "sound settings" in command:
        return open_settings("sound")
    if "network settings" in command:
        return open_settings("network")
    if "recycle bin" in command:
        return open_recycle_bin()
    if command.startswith("search google for "):
        return google_search(command.replace("search google for ", "", 1))
    if command.startswith("search youtube for "):
        return youtube_search(command.replace("search youtube for ", "", 1))
    if command.startswith("play "):
        return youtube_search(command[5:].strip())
    if command in {"copy", "paste", "cut", "select all", "save", "undo", "redo", "new tab", "close tab", "refresh", "alt tab"}:
        if pyautogui is None:
            return "Install PyAutoGUI for keyboard shortcuts."
        actions = {
            "copy": ["ctrl", "c"],
            "paste": ["ctrl", "v"],
            "cut": ["ctrl", "x"],
            "select all": ["ctrl", "a"],
            "save": ["ctrl", "s"],
            "undo": ["ctrl", "z"],
            "redo": ["ctrl", "y"],
            "new tab": ["ctrl", "t"],
            "close tab": ["ctrl", "w"],
            "refresh": ["ctrl", "r"],
            "alt tab": ["alt", "tab"],
        }
        pyautogui.hotkey(*actions[command])
        return command.capitalize()
    if command in {"show desktop", "go to desktop", "desktop"}:
        return show_desktop()
    if command in {"open run", "run command"}:
        return open_run()
    if "system information" in command or "system info" in command or "computer status" in command:
        return system_info()
    if "what time" in command or command == "time":
        return current_time()
    if "what date" in command or command == "date":
        return current_date()
    return ""
