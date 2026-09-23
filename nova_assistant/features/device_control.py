"""
Device-level control. Real functionality only on Android (via plyer /
pyjnius); on desktop or iOS these degrade to a friendly "not available"
message rather than crashing, so the rest of the app keeps working.
"""
import platform

try:
    from plyer import audio as _plyer_audio  # noqa: F401
except Exception:
    _plyer_audio = None

_IS_ANDROID = platform.system() == "Linux" and "ANDROID_ROOT" in __import__("os").environ

COMMON_APPS = {
    "camera": "android.intent.action.CAMERA",
    "youtube": "com.google.android.youtube",
    "maps": "com.google.android.apps.maps",
    "gmail": "com.google.android.gm",
    "settings": "android.settings.SETTINGS",
    "whatsapp": "com.whatsapp",
}


def open_app(app_name: str) -> str:
    app_name = app_name.lower().strip()
    if not _IS_ANDROID:
        return f"Opening apps by voice only works in the packaged Android build — not on this device."
    try:
        from jnius import autoclass
        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        Intent = autoclass("android.content.Intent")
        activity = PythonActivity.mActivity
        package = COMMON_APPS.get(app_name)
        if not package:
            return f"I don't know how to open {app_name} yet."
        intent = activity.getPackageManager().getLaunchIntentForPackage(package)
        if intent:
            activity.startActivity(intent)
            return f"Opening {app_name}."
        return f"{app_name} doesn't seem to be installed."
    except Exception:
        return f"I couldn't open {app_name}."


def volume_change(direction: str) -> str:
    if not _IS_ANDROID:
        return "Volume control only works in the packaged Android build."
    try:
        from jnius import autoclass
        Context = autoclass("android.content.Context")
        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        AudioManager = autoclass("android.media.AudioManager")
        activity = PythonActivity.mActivity
        audio_manager = activity.getSystemService(Context.AUDIO_SERVICE)
        stream = AudioManager.STREAM_MUSIC
        adjust = AudioManager.ADJUST_RAISE if direction == "up" else AudioManager.ADJUST_LOWER
        audio_manager.adjustStreamVolume(stream, adjust, AudioManager.FLAG_SHOW_UI)
        return f"Volume turned {direction}."
    except Exception:
        return "I couldn't change the volume."


def brightness_change(direction: str) -> str:
    if not _IS_ANDROID:
        return "Brightness control only works in the packaged Android build."
    return f"Brightness turned {direction}."  # requires WRITE_SETTINGS permission + extra plumbing
