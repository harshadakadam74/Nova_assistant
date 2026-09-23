import webbrowser
import urllib.parse


def search_web(query: str) -> str:
    if not query:
        return "What should I search for?"
    url = "https://www.google.com/search?q=" + urllib.parse.quote(query)
    webbrowser.open(url)
    return f"Here's what I found for {query}."


def open_website(site: str) -> str:
    if not site:
        return "Which website should I open?"
    url = site if site.startswith("http") else f"https://{site}"
    webbrowser.open(url)
    return f"Opening {site}."
