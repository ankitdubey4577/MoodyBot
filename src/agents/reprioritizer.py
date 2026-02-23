from datetime import datetime, timedelta, timezone

def reprioritize(task, sentiment):
    score = 0
    reason = []

    # Deadline pressure
    if task.deadline:
        try:
            dl = datetime.fromisoformat(task.deadline)
            hours_left = (dl - datetime.now(timezone.utc)).total_seconds() / 3600
            if hours_left < 24:
                score += 3
                reason.append("deadline soon")
        except (ValueError, AttributeError, TypeError):
            pass

    # Mood-based adjustment
    mood = sentiment.get("suggested_mood")
    if mood in ("tired", "anxious", "overwhelmed"):
        if task.user_priority == "high":
            score += 1
            reason.append("keep important only")
        else:
            score -= 1
            reason.append("low effort preferred")

    if mood in ("focused", "motivated"):
        if task.user_priority == "high":
            score += 2
            reason.append("deep work window")

    # Final priority
    if score >= 3:
        return "high", ", ".join(reason)
    if score <= -1:
        return "low", ", ".join(reason)

    return task.user_priority, "unchanged"
