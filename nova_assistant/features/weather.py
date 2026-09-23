import requests
from config import OPENWEATHER_API_KEY, DEFAULT_CITY


def get_weather(city: str = "") -> str:
    city = city or DEFAULT_CITY
    if not OPENWEATHER_API_KEY:
        return ("I need an OpenWeatherMap API key to check live weather. "
                "Add OPENWEATHER_API_KEY in config.py to enable this.")
    try:
        resp = requests.get(
            "https://api.openweathermap.org/data/2.5/weather",
            params={"q": city, "appid": OPENWEATHER_API_KEY, "units": "metric"},
            timeout=6,
        )
        data = resp.json()
        if resp.status_code != 200:
            return f"I couldn't find weather for {city}."
        desc = data["weather"][0]["description"]
        temp = round(data["main"]["temp"])
        feels = round(data["main"]["feels_like"])
        return f"It's {temp}°C in {city} with {desc}, feels like {feels}°C."
    except requests.RequestException:
        return "I couldn't reach the weather service right now."
