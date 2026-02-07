BOOSTERS = {
    "sad": ["Listen to music", "Call a friend"],
    "tired": ["Short nap", "Hydrate + stretch"],
    "anxious": ["5 min breathing", "Walk outside"]
}

def suggest_boosters(mood: str):
    return BOOSTERS.get(mood, ["Do something kind for yourself"])
