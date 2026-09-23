"""Device controls for Android and Windows desktop development."""
import datetime
import os
import platform
import subprocess
import webbrowser
from urllib.parse import quote_plus

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

COMMON_APPS = {
    "camera": "android.intent.action.CAMERA",
    "youtube": "com.google.android.youtube",
    "maps": "com.google.android.apps.maps",
    "gmail": "com.google.android.gm",
    "settings": "android.settings.SETTINGS",
    "whatsapp": "com.whatsapp",
}

WINDOWS_APPS = {
    "notepad": "notepad.exe", "calculator": "calc.exe", "calc": "calc.exe",
    "paint": "mspaint.exe", "cmd": "cmd.exe", "command prompt": "cmd.exe",
    "powershell": "powershell.exe", "explorer": "explorer.exe",
    "file explorer": "explorer.exe", "task manager": "taskmgr.exe",
    "control panel": "control.exe", "wordpad": "write.exe",
}

APP_PATHS = {
    "chrome": [r"%ProgramFiles%\Google\Chrome\Application\chrome.exe", r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"],
    "edge": [r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe", r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"],
    "vscode": [r"%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe"],
    "visual studio code": [r"%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe"],
    "spotify": [r"%APPDATA%\Spotify\Spotify.exe"],
    "word": [r"%ProgramFiles%\Microsoft Office\root\Office16\WINWORD.EXE"],
    "excel": [r"%ProgramFiles%\Microsoft Office\root\Office16\EXCEL.EXE"],
    "powerpoint": [r"%ProgramFiles%\Microsoft Office\root\Office16\POWERPNT.EXE"],
}


def open_website(name):
    websites = {"youtube": "https://www.youtube.com", "google": "https://www.google.com", "github": "https://github.com", "gmail": "https://mail.google.com", "instagram": "https://www.instagram.com", "facebook": "https://www.facebook.com", "whatsapp": "https://web.whatsapp.com", "linkedin": "https://www.linkedin.com", "chatgpt": "https://chatgpt.com"}
    key = name.lower().strip()
    url = websites.get(key, name.strip())
    if "." not in url and not url.startswith(("http://", "https://")):
        return f"I don't know the website {name}"
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"
    webbrowser.open(url)
    return f"Opening {key}" if key in websites else f"Opening {url}"


def open_windows_app(name):
    name = name.lower().strip()
    executable = WINDOWS_APPS.get(name)
    try:
        if executable:
            subprocess.Popen(executable)
        else:
            subprocess.Popen(["cmd", "/c", "start", "", name], shell=False)
        return f"Opening {name}" if executable else f"Trying to open {name}"
    except OSError as error:
        return f"Could not open {name}: {error}"


def open_installed_app(name):
    for path in APP_PATHS.get(name.lower().strip(), []):
        expanded = os.path.expandvars(path)
        if os.path.exists(expanded):
            try:
                subprocess.Popen(expanded)
                return f"Opening {name}"
            except OSError as error:
                return f"Could not open {name}: {error}"
    return open_windows_app(name)


def close_app(name):
    process_names = {"chrome": "chrome.exe", "edge": "msedge.exe", "vscode": "Code.exe", "visual studio code": "Code.exe", "notepad": "notepad.exe", "calculator": "CalculatorApp.exe", "spotify": "Spotify.exe", "paint": "mspaint.exe", "cmd": "cmd.exe", "powershell": "powershell.exe"}
    process = process_names.get(name.lower().strip())
    if not process:
        return f"I don't know how to close {name}"
    result = subprocess.run(["taskkill", "/IM", process, "/F"], capture_output=True, text=True)
    return f"Closed {name}" if result.returncode == 0 else f"{name} was not running."


def volume_up():
    if not pyautogui:
        return "Install PyAutoGUI to control volume."
    for _ in range(5):
        pyautogui.press("volumeup")
    return "Volume increased"


def volume_down():
    if not pyautogui:
        return "Install PyAutoGUI to control volume."
    for _ in range(5):
        pyautogui.press("volumedown")
    return "Volume decreased"


def mute_volume():
    if not pyautogui:
        return "Install PyAutoGUI to control volume."
    pyautogui.press("volumemute")
    return "Volume muted"


def brightness_change(direction):
    if _IS_ANDROID:
        return f"Brightness turned {direction}."
    if not sbc:
        return "Install screen-brightness-control to change brightness."
    try:
        current = sbc.get_brightness()[0]
        value = min(current + 10, 100) if direction == "up" else max(current - 10, 0)
        sbc.set_brightness(value)
        return f"Brightness {value} percent"
    except Exception as error:
        return f"Could not change brightness: {error}"


def take_screenshot():
    if not pyautogui:
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
    targets = {None: "ms-settings:", "wifi": "ms-settings:network-wifi", "bluetooth": "ms-settings:bluetooth", "display": "ms-settings:display"}
    subprocess.Popen(["cmd", "/c", "start", "", targets.get(kind, "ms-settings:")], shell=False)
    label = "Wi-Fi" if kind == "wifi" else kind.capitalize() if kind else "Windows"
    return f"Opening {label} settings"


def open_recycle_bin():
    subprocess.Popen(["explorer.exe", "shell:RecycleBinFolder"])
    return "Opening Recycle Bin"


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


def system_info():
    return f"System: {platform.system()} {platform.release()}\nComputer: {platform.node()}\nProcessor: {platform.processor()}"


def current_time():
    return datetime.datetime.now().strftime("The current time is %I:%M %p")


def current_date():
    return datetime.datetime.now().strftime("Today is %A, %d %B %Y")


def volume_change(direction):
    return volume_up() if direction == "up" else volume_down()


def open_app(command):
    command = command.lower().strip().replace("open the ", "open ").replace("open d ", "open ").replace("please ", "")
    if command in {"youtube", "google", "github", "gmail", "instagram", "facebook", "whatsapp", "linkedin", "chatgpt"}:
        return open_website(command)
    if "open wifi" in command or "open wi-fi" in command:
        return open_settings("wifi")
    if "open bluetooth" in command:
        return open_settings("bluetooth")
    if "open display settings" in command:
        return open_settings("display")
    if "open settings" in command:
        return open_settings()
    if "recycle bin" in command or "open trash" in command:
        return open_recycle_bin()
    if command.startswith("open "):
        target = command[5:].strip()
        if target in {"youtube", "google", "github", "gmail", "instagram", "facebook", "whatsapp", "linkedin", "chatgpt"}:
            return open_website(target)
        return open_installed_app(target) if target in APP_PATHS else open_windows_app(target)
    if command.startswith("close "):
        return close_app(command[6:])
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
    if "screenshot" in command or "capture screen" in command:
        return take_screenshot()
    if "lock computer" in command or "lock pc" in command:
        return lock_computer()
    if "cancel shutdown" in command or "cancel shut down" in command:
        return cancel_shutdown()
    if "confirm shutdown" in command or "confirm restart" in command:
        return confirm_power_action()
    if "shutdown" in command or "shut down" in command:
        return request_power_action("shutdown")
    if "restart" in command:
        return request_power_action("restart")
    if command.startswith("search google for "):
        return google_search(command[18:])
    if command.startswith("google "):
        return google_search(command[7:])
    if command.startswith("search youtube for "):
        return youtube_search(command[20:])
    if command.startswith("play "):
        return youtube_search(command[5:])
    if command in {"time", "current time"} or "what time is it" in command:
        return current_time()
    if command in {"date", "current date"} or "today's date" in command:
        return current_date()
    if "system info" in command or "system information" in command:
        return system_info()
    return ""
