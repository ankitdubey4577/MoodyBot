from typing import List, Dict

BOOSTERS: Dict[str, List[str]] = {
    "sad": ["Listen to music", "Call a friend"],
    "tired": ["Short nap", "Hydrate + stretch"],
    "anxious": ["5 min breathing", "Walk outside"],
    "overwhelmed": ["Break task into tiny steps", "Take a 5-minute break"],
    "stuck": ["Change environment", "Talk it through with someone"]
}

def suggest_boosters(mood: str) -> List[str]:
    """
    Suggest mood-specific booster activities.
    Returns list of actionable suggestions.
    """
    return BOOSTERS.get(mood, ["Do something kind for yourself"])
