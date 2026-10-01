import unittest

from features.news import get_headlines


class FakeResponse:
    content = (
        b"<rss><channel><item><title>Sample report</title>"
        b"<description>&lt;b&gt;A short summary&lt;/b&gt;</description>"
        b"</item></channel></rss>"
    )

    def raise_for_status(self):
        return None


class FakeSession:
    def __init__(self):
        self.timeout = None

    def get(self, url, timeout):
        self.timeout = timeout
        return FakeResponse()


class NewsTests(unittest.TestCase):
    def test_headlines_are_summarized_without_html(self):
        session = FakeSession()
        self.assertEqual(
            get_headlines(session),
            "News: Sample report: A short summary",
        )
        self.assertLessEqual(session.timeout, 10)

    def test_feed_errors_return_no_news(self):
        class OfflineSession:
            def get(self, url, timeout):
                raise OSError("offline")

        self.assertIsNone(get_headlines(OfflineSession()))


if __name__ == "__main__":
    unittest.main()