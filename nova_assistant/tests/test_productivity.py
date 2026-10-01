import os
import tempfile
import unittest
from unittest.mock import patch

import core.database as database
from features import productivity


class ProductivityTests(unittest.TestCase):
    def setUp(self):
        self.previous_db_path = database.DB_PATH
        self.temp_dir = tempfile.TemporaryDirectory()
        database.DB_PATH = os.path.join(self.temp_dir.name, "test.db")
        database.init_db()

    def tearDown(self):
        database.DB_PATH = self.previous_db_path
        self.temp_dir.cleanup()

    def test_tasks_and_schedule_are_stored_locally(self):
        self.assertIn("Added task", productivity.add_task("review notes"))
        self.assertIn("review notes", productivity.list_tasks())
        self.assertIn("Marked review notes complete", productivity.complete_task("review notes"))
        self.assertNotIn("review notes", productivity.list_tasks())

        self.assertIn(
            "Scheduled study group",
            productivity.add_schedule_event("study group", "tomorrow", "3 PM"),
        )
        self.assertIn("study group", productivity.schedule_for("tomorrow"))

    def test_preferences_are_explicit_and_history_can_be_erased(self):
        self.assertIn("remember", productivity.remember_preference("Prefer concise answers"))
        self.assertIn("concise", productivity.get_preferences())

        productivity.save_conversation("user", "Find the blue notebook")
        self.assertIn("blue notebook", productivity.search_conversation("notebook"))
        productivity.clear_conversation_history()
        self.assertIn("couldn't find", productivity.search_conversation("notebook"))

    def test_daily_briefing_includes_due_items(self):
        from datetime import date

        productivity.add_task("prepare slides", date.today().isoformat())
        productivity.add_schedule_event("team meeting", "today", "10 AM")
        with patch("config.OPENWEATHER_API_KEY", ""), \
             patch("features.news.get_headlines", return_value=None):
            briefing = productivity.daily_briefing()
        self.assertIn("prepare slides", briefing)
        self.assertIn("team meeting", briefing)


if __name__ == "__main__":
    unittest.main()