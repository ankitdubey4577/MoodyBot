from pydantic import BaseModel, Field
from typing import List, Dict, Any
from datetime import datetime, timezone

# -----------------------------
# Core Analysis Models
# -----------------------------

class MoodAnalysis(BaseModel):
    label: str = Field(..., description="Primary detected mood")
    confidence: float = Field(..., ge=0.0, le=1.0)
    reasoning: str

class TaskRecommendation(BaseModel):
    name: str
    category: str
    priority: str
    scheduled_time: str
    tactic: str

# -----------------------------
# Agent Execution Trace
# -----------------------------

class AgentStep(BaseModel):
    agent: str
    action: str
    output: str
    timestamp: str  # ISO formatted string

    @staticmethod
    def now(agent: str, action: str, output: str):
        return AgentStep(
            agent=agent,
            action=action,
            output=output,
            timestamp=datetime.now(timezone.utc).isoformat()
        )

# -----------------------------
# LangGraph Result (Internal)
# -----------------------------

class LangGraphResult(BaseModel):
    mood: MoodAnalysis
    recommendation: TaskRecommendation
    agent_path: List[AgentStep]
    success_prob: float = Field(..., ge=0.0, le=1.0)
    raw_state: Dict[str, Any]
