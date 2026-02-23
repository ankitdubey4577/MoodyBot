from typing import Tuple, Optional

def boost_priority(mood: str, user_priority: str) -> Tuple[str, Optional[str]]:
    """
    Boost task priority based on mood analysis.
    Returns (priority, reason) tuple where reason may be None.
    """
    if mood in ["tired", "anxious"] and user_priority == "low":
        return "high", "Boosted due to low-energy compatible task"
    return user_priority, None

def historical_boost(success_rate: float) -> float:
    if success_rate > 0.7:
        return 1.5
    elif success_rate < 0.3:
        return 0.5
    else:
        return 1.0
