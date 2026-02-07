from src.llm.ollama import FreeLLM
import json

llm = FreeLLM()

def detect_mood(text: str) -> dict:
    prompt = f"""
    Detect mood from text.
    Return JSON:
    {{
      "mood": "...",
      "confidence": 0.0
    }}
    Text: {text}
    """
    try:
        return json.loads(llm.ask(prompt))
    except:
        return {"mood": "neutral", "confidence": 0.6}
