from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import Optional

# Try to use dateparser if available
try:
    import dateparser
except Exception:
    dateparser = None


IST_TZ_HINTS = ["ist", "india", "indian time"]


def _looks_like_ist(text: str) -> bool:
    t = text.lower()
    return any(k in t for k in IST_TZ_HINTS)


def parse_natural_datetime(text: str) -> Optional[str]:
    """
    Parse natural language datetime into ISO string.

    Examples supported:
    - "3:50 PM IST"
    - "tomorrow at 9"
    - "in 30 minutes"
    - "next monday morning"
    - "today 6pm"

    Returns:
        ISO formatted datetime string OR None if parsing fails
    """

    if not text or not text.strip():
        return None

    text = text.strip()
    now = datetime.now()

    # -----------------------------
    # 1️⃣ Preferred: dateparser
    # -----------------------------
    if dateparser:
        settings = {
            "RETURN_AS_TIMEZONE_AWARE": False,
            "PREFER_DATES_FROM": "future",
            "RELATIVE_BASE": now,
        }

        if _looks_like_ist(text):
            settings["TIMEZONE"] = "Asia/Kolkata"

        dt = dateparser.parse(text, settings=settings)
        if dt:
            return dt.isoformat()

    # -----------------------------
    # 2️⃣ Fallback rules (no deps)
    # -----------------------------

    t = text.lower()

    # "in X minutes"
    m = re.search(r"in\s+(\d+)\s+minute", t)
    if m:
        return (now + timedelta(minutes=int(m.group(1)))).isoformat()

    # "in X hours"
    m = re.search(r"in\s+(\d+)\s+hour", t)
    if m:
        return (now + timedelta(hours=int(m.group(1)))).isoformat()

    # "tomorrow"
    if "tomorrow" in t:
        return (now + timedelta(days=1)).replace(hour=9, minute=0, second=0).isoformat()

    # "today evening"
    if "today" in t and "evening" in t:
        return now.replace(hour=18, minute=0, second=0).isoformat()

    # Simple "3pm / 6:30pm"
    m = re.search(r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)", t)
    if m:
        hour = int(m.group(1))
        minute = int(m.group(2) or 0)
        ampm = m.group(3)

        if ampm == "pm" and hour < 12:
            hour += 12
        if ampm == "am" and hour == 12:
            hour = 0

        return now.replace(hour=hour, minute=minute, second=0).isoformat()

    return None
