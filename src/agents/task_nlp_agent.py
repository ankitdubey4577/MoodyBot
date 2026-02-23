import re
from typing import Dict

def extract_task(text: str) -> Dict[str, str]:
    """
    Extract task information from natural language text.
    Always returns a dict with title, scheduled_time, and user_priority.
    """
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
