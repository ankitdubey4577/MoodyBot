import re

def extract_task(text: str) -> dict | None:
    # Very simple NLP extraction example
    match = re.search(r"(call|email|meet|finish|write)\s(.+)", text, re.I)
    if not match:
        return {
            "title": text,
            "scheduled_time": "unscheduled",
            "user_priority": "medium"
        }
    return {
        "title": match.group(0),
        "scheduled_time": "unscheduled",
        "user_priority": "medium"
    }
