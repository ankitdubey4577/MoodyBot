"""
Advanced State Management for Multi-Agent System
"""
from typing import TypedDict, List, Dict, Any, Optional
from datetime import datetime

class AgentMessage(TypedDict):
    """Message from an agent"""
    agent: str
    content: str
    timestamp: str
    metadata: Optional[Dict[str, Any]]

class TaskData(TypedDict):
    """Task information"""
    id: Optional[int]
    title: str
    description: Optional[str]
    priority: int
    ai_priority: Optional[int]
    effective_priority: Optional[int]
    estimated_time: Optional[float]
    completion_probability: Optional[float]
    category: Optional[str]
    deadline: Optional[str]

class MoodData(TypedDict):
    """Mood analysis information"""
    label: str
    confidence: float
    sentiment_score: float
    emotional_state: str
    burnout_risk: Optional[float]
    energy_level: Optional[int]

class ContextData(TypedDict):
    """Retrieved context from RAG"""
    relevant_tasks: List[Dict[str, Any]]
    relevant_notes: List[Dict[str, Any]]
    similarity_scores: List[float]

class AnalyticsData(TypedDict):
    """Analytics and insights"""
    productivity_score: Optional[float]
    completion_rate: Optional[float]
    average_task_time: Optional[float]
    burnout_warning: Optional[bool]
    recommendations: List[str]

class AgentState(TypedDict):
    """
    Complete state for the multi-agent system
    Passed between all agents in the graph
    """
    # Input
    input: str
    user_id: Optional[int]

    # Conversation History
    conversation_history: List[AgentMessage]

    # Agent Outputs
    mode: Optional[str]  # 'work' or 'personal'
    mood: Optional[MoodData]
    tasks: List[TaskData]
    context: Optional[ContextData]
    analytics: Optional[AnalyticsData]

    # Agent Coordination
    current_agent: Optional[str]
    agent_path: List[str]
    next_action: Optional[str]

    # Final Output
    response: Optional[str]
    recommendations: List[str]

    # Metadata
    timestamp: str
    session_id: Optional[str]
