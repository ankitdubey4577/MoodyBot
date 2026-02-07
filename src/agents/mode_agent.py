def detect_mode(text: str) -> str:
    work_keywords = ["deadline", "office", "client", "deploy", "bug"]
    return "work" if any(k in text.lower() for k in work_keywords) else "personal"
