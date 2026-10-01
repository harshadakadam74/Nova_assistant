import unittest
from unittest.mock import patch

from features.device_control import handle_device_command


class DeviceCommandTests(unittest.TestCase):
    def test_wake_word_noise_around_google_opens_google(self):
        with patch("features.device_control.webbrowser.open", return_value=True) as browser, \
             patch("features.device_control.subprocess.Popen") as launch:
            reply = handle_device_command("google hey jara open")

        self.assertEqual(reply, "Opening google")
        browser.assert_called_once_with("https://www.google.com")
        launch.assert_not_called()

    def test_unknown_app_never_falls_through_to_windows_shell(self):
        with patch("features.device_control.subprocess.Popen") as launch:
            reply = handle_device_command("open google hey jara open")

        self.assertIn("don't recognize", reply)
        launch.assert_not_called()

    def test_known_browser_alias_opens_default_browser(self):
        with patch("features.device_control.webbrowser.open", return_value=True) as browser:
            reply = handle_device_command("open the browser")

        self.assertEqual(reply, "Opening your default browser.")
        browser.assert_called_once_with("about:blank")


if __name__ == "__main__":
    unittest.main()