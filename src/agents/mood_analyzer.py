from langchain_core.tools import tool
from src.utils.llm import OllamaClient
from src.models.schemas import MoodAnalysis, AgentStep
import json
import re
from datetime import datetime, timezone

llm = OllamaClient()

class MoodAnalyzer:
    """Wrapper class for mood analysis functionality"""

    def __init__(self):
        self.name = "MoodAnalyzer"

    def analyze(self, text: str) -> dict:
        """Analyze mood from text"""
        return analyze_mood(text)

@tool
def analyze_mood(text: str) -> dict:
    """
    Analyze developer mood from natural language input.
    Returns a dict compatible with LangGraph state.
    """
    chain = llm.get_mood_analyzer()
    

    try:
        response = chain.invoke({"input": text})

        # Handle LangChain message or string
        content = response.content if hasattr(response, "content") else str(response)

        # Extract JSON safely (non-greedy)
        match = re.search(r'\{.*?\}', content, re.DOTALL)
        if not match:
            raise ValueError("No JSON found in LLM response")

        parsed = json.loads(match.group())

        mood = MoodAnalysis(
            label=parsed.get("primary_mood", "neutral"),
            confidence=min(max(parsed.get("confidence", 0.7), 0.0), 1.0),
            reasoning=parsed.get("reasoning", "No reasoning provided")
        )

    except Exception as e:
        # Safe fallback (graph must continue)
        mood = MoodAnalysis(
            label="neutral",
            confidence=0.6,
            reasoning=f"Fallback due to parsing error: {str(e)}"
        )

    return {
        "mood": mood.model_dump(),
        "agent_step": AgentStep(
            agent="MoodAnalyzer",
            action="Classify emotional blockers",
            output=f"{mood.label} ({mood.confidence:.2f})",
            timestamp=datetime.now(timezone.utc).isoformat()
        ).model_dump()
    }
