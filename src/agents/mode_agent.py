def detect_mode(text: str) -> str:
    """
    Detect work vs personal mode from user input text.
    Returns 'work' or 'personal'.
    """
    if not text:
        return "personal"

    work_keywords = ["deadline", "office", "client", "deploy", "bug", "meeting", "project", "sprint"]
    return "work" if any(k in text.lower() for k in work_keywords) else "personal"
