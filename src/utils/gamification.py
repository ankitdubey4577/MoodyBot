from datetime import datetime, timedelta

LEVEL_XP_THRESHOLDS = [0, 100, 300, 600, 1000, 1500]

def update_streak(last_date_str: str, current_date: datetime) -> int | None:
    if not last_date_str:
        return 1
    last_date = datetime.strptime(last_date_str, "%Y-%m-%d").date()
    today = current_date.date()
    if last_date == today:
        return None  # Already counted today
    elif last_date == today - timedelta(days=1):
        return 1  # Continue streak (increment in caller)
    else:
        return 1  # Streak reset (start over)

def calculate_xp(task_priority: str, completed: bool, mood_boost: bool) -> int:
    base_xp = {
        "low": 10,
        "medium": 20,
        "high": 40
    }.get(task_priority, 10)

    xp = base_xp if completed else 0
    if mood_boost:
        xp += 5
    return xp

def get_level(xp: int) -> int:
    """Calculate user level based on XP thresholds."""
    level = 1
    for i, threshold in enumerate(LEVEL_XP_THRESHOLDS):
        if xp >= threshold:
            level = i + 1
        else:
            break  # Early exit when threshold not met
    return level
