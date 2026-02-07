from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

_analyzer = SentimentIntensityAnalyzer()

def analyze_sentiment(text: str) -> dict:
    """
    Returns:
      - compound: [-1..1]
      - label: negative/neutral/positive
      - arousal_hint: calm/activated
      - suggested_mood: tired/anxious/stuck/energetic/overwhelmed/neutral (heuristic)
    """
    scores = _analyzer.polarity_scores(text)
    c = scores["compound"]

    if c >= 0.25:
        label = "positive"
    elif c <= -0.25:
        label = "negative"
    else:
        label = "neutral"

    # simple arousal hint
    activated = (scores["pos"] + scores["neg"]) > 0.6
    arousal_hint = "activated" if activated else "calm"

    # heuristic mood inference (cheap + reliable)
    t = text.lower()
    if "tired" in t or "sleep" in t or "exhaust" in t:
        mood = "tired"
    elif "anxious" in t or "panic" in t or "worried" in t:
        mood = "anxious"
    elif "stuck" in t or "blocked" in t or "confused" in t:
        mood = "stuck"
    elif "overwhelm" in t or "too much" in t:
        mood = "overwhelmed"
    elif label == "positive" and "energy" in t:
        mood = "energetic"
    else:
        mood = "neutral"

    return {
        "compound": c,
        "label": label,
        "arousal_hint": arousal_hint,
        "suggested_mood": mood,
        "raw": scores
    }
