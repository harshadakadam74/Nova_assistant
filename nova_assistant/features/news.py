"""Fetch a small set of world-news summaries from a public RSS feed."""
import html
import re
import xml.etree.ElementTree as ET

import requests

RSS_URL = "https://feeds.bbci.co.uk/news/world/rss.xml"


def get_headlines(session=None, limit=3):
    session = session or requests
    try:
        response = session.get(RSS_URL, timeout=8)
        response.raise_for_status()
        feed = ET.fromstring(response.content)
    except (requests.RequestException, ET.ParseError, AttributeError, OSError):
        return None

    summaries = []
    for item in feed.findall("./channel/item")[:max(1, min(limit, 5))]:
        title = item.findtext("title", default="").strip()
        description = item.findtext("description", default="").strip()
        description = html.unescape(re.sub(r"<[^>]*>", "", description))
        if title:
            summaries.append(f"{title}: {description}" if description else title)
    return "News: " + "; ".join(summaries) if summaries else None