from pydantic import BaseModel
from typing import List

class AgentStep(BaseModel):
    agent: str
    action: str
    output: str

class BotResponse(BaseModel):
    mode: str
    mood: str
    tasks: List[dict]
    agent_path: List[AgentStep]
