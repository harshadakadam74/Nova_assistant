import random
from datetime import datetime

JOKES = [
    "Why did the developer go broke? Because they used up all their cache.",
    "I told my computer I needed a break, and it said 'no problem, I'll go to sleep.'",
    "Why do programmers prefer dark mode? Because light attracts bugs.",
    "I would tell you a UDP joke, but you might not get it.",
]

FACTS = [
    "Honey never spoils — archaeologists have found edible honey in ancient tombs.",
    "A day on Venus is longer than a year on Venus.",
    "Octopuses have three hearts.",
    "Bananas are berries, but strawberries aren't.",
]

GREETINGS = ["Hi there!", "Hello! How can I help?", "Hey, I'm listening."]


def greet() -> str:
    return random.choice(GREETINGS)


def joke() -> str:
    return random.choice(JOKES)


def fact() -> str:
    return random.choice(FACTS)


def current_time() -> str:
    return "It's " + datetime.now().strftime("%I:%M %p") + "."


def current_date() -> str:
    return "Today is " + datetime.now().strftime("%A, %B %d, %Y") + "."


def fallback(raw_text: str) -> str:
    if not raw_text:
        return "Sorry, I didn't catch that."
    return f"I'm not sure how to help with '{raw_text}' yet, but I'm learning."
