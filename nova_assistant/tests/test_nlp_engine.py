import unittest

from core.nlp_engine import parse_intent


class ParseIntentTests(unittest.TestCase):
    def test_calculation_with_what_is_phrase(self):
        intent, entities = parse_intent("what is 45 times 12")
        self.assertEqual(intent, "calculate")
        self.assertEqual(entities["expr"], "45 * 12")

    def test_weather_question_is_supported(self):
        intent, entities = parse_intent("what is the weather in latur")
        self.assertEqual(intent, "weather_query")
        self.assertEqual(entities["city"], "latur")

    def test_time_question_is_supported(self):
        intent, entities = parse_intent("what is the time")
        self.assertEqual(intent, "time_query")
        self.assertEqual(entities, {})

    def test_task_and_schedule_commands_are_supported(self):
        self.assertEqual(parse_intent("add a task to study")[0], "add_task")
        self.assertEqual(parse_intent("mark task study done")[0], "complete_task")
        intent, entities = parse_intent("schedule study group on tomorrow at 3 PM")
        self.assertEqual(intent, "add_schedule_event")
        self.assertEqual(entities, {
            "title": "study group",
            "date": "tomorrow",
            "time": "3 pm",
        })

    def test_preferences_file_search_and_pomodoro_are_supported(self):
        self.assertEqual(
            parse_intent("remember that I prefer concise answers")[0],
            "remember_preference",
        )
        self.assertEqual(parse_intent("search files for report")[0], "file_search")
        self.assertEqual(parse_intent("start a pomodoro")[0], "pomodoro")


if __name__ == "__main__":
    unittest.main()
