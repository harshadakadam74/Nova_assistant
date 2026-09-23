[app]
title = Nova
package.name = nova
package.domain = org.novaassistant
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,db
version = 1.0
requirements = python3,kivy,speechrecognition,pyttsx3,requests,plyer,pyjnius,pyaudio
orientation = portrait
fullscreen = 0

android.permissions = RECORD_AUDIO,INTERNET,MODIFY_AUDIO_SETTINGS,WRITE_SETTINGS,VIBRATE

[buildozer]
log_level = 2
warn_on_root = 1
