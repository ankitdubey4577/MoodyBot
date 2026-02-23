"""
Advanced Multi-Agent Graph using LangGraph
Orchestrates 8+ specialized AI agents for intelligent task management
"""
from langgraph.graph import StateGraph, END
from typing import Dict, Any
from datetime import datetime, timezone
import logging

# Import all agents
from src.agents.orchestrator import OrchestratorAgent
from src.agents.memory_agent import MemoryAgent
from src.agents.context_retriever import ContextRetriever
from src.agents.mood_analyzer import MoodAnalyzer
from src.agents.mode_agent import detect_mode
from src.agents.task_nlp_agent import extract_task
from src.agents.priority_agent import boost_priority
from src.agents.scheduler_agent import SchedulerAgent
from src.agents.burnout_detector import BurnoutDetector
from src.agents.recommendation_engine import RecommendationEngine
from src.graph.state import AgentState

logger = logging.getLogger(__name__)

class AdvancedMoodyBotGraph:
    """
    Advanced multi-agent system with:
    - Orchestrator for workflow management
    - Memory agent for conversation history
    - Context retrieval (RAG - to be enhanced)
    - Mood analysis with burnout detection
    - Task analysis and scheduling
    - Intelligent recommendations
    """

    def __init__(self):
        # Initialize all agents
        self.orchestrator = OrchestratorAgent()
        self.memory_agent = MemoryAgent()
        self.context_retriever = ContextRetriever()
        self.mood_analyzer = MoodAnalyzer()
        self.scheduler = SchedulerAgent()
        self.burnout_detector = BurnoutDetector()
        self.recommendation_engine = RecommendationEngine()

        # Build the graph
        self.graph = self.build()

    def build(self) -> StateGraph:
        """
        Build the multi-agent graph with proper routing.

        Graph flow:
        1. Entry -> Orchestrator (decides workflow)
        2. Memory Agent (loads conversation history)
        3. Mood Analyzer (analyzes emotional state)
        4. Mode Detector (work vs personal)
        5. Context Retriever (RAG - semantic search)
        6. Task Analyzer (extract and analyze tasks)
        7. Burnout Detector (check for burnout signs)
        8. Prioritizer (ML-based priority)
        9. Scheduler (optimal scheduling)
        10. Recommendation Engine (synthesize insights)
        11. END
        """
        # Create graph with state schema
        workflow = StateGraph(dict)

        # Add all agent nodes
        # Note: orchestrator node commented out - using fixed workflow for now
        # workflow.add_node("orchestrator", self.orchestrator_node)
        workflow.add_node("memory_agent", self.memory_node)
        workflow.add_node("mood_analyzer", self.mood_analyzer_node)
        workflow.add_node("mode_detector", self.mode_detector_node)
        workflow.add_node("context_retriever", self.context_retriever_node)
        workflow.add_node("task_analyzer", self.task_analyzer_node)
        workflow.add_node("burnout_detector", self.burnout_detector_node)
        workflow.add_node("prioritizer", self.prioritizer_node)
        workflow.add_node("scheduler", self.scheduler_node)
        workflow.add_node("recommendation_engine", self.recommendation_engine_node)

        # Set entry point
        workflow.set_entry_point("memory_agent")

        # Define workflow edges
        workflow.add_edge("memory_agent", "mood_analyzer")
        workflow.add_edge("mood_analyzer", "mode_detector")
        workflow.add_edge("mode_detector", "context_retriever")
        workflow.add_edge("context_retriever", "task_analyzer")
        workflow.add_edge("task_analyzer", "burnout_detector")
        workflow.add_edge("burnout_detector", "prioritizer")
        workflow.add_edge("prioritizer", "scheduler")
        workflow.add_edge("scheduler", "recommendation_engine")
        workflow.add_edge("recommendation_engine", END)

        return workflow.compile()

    # Node Functions

    def orchestrator_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Orchestrator decides workflow (currently using fixed workflow)."""
        return self.orchestrator.orchestrate(state)

    def memory_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Load and manage conversation memory."""
        return self.memory_agent.process(state)

    def mood_analyzer_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze mood and emotional state."""
        try:
            input_text = state.get("input", "")
            mood_result = self.mood_analyzer.analyze(input_text)

            # Update state with mood data
            state["mood"] = {
                "label": mood_result.get("mood", {}).get("label", "neutral"),
                "confidence": mood_result.get("mood", {}).get("confidence", 0.5),
                "sentiment_score": mood_result.get("mood", {}).get("sentiment_score", 0),
                "emotional_state": mood_result.get("mood", {}).get("label", "neutral"),
                "energy_level": self._estimate_energy_level(mood_result)
            }

            # Add to agent path
            if "agent_path" not in state:
                state["agent_path"] = []
            state["agent_path"].append("MoodAnalyzer")

            return state

        except Exception as e:
            logger.error(f"Mood analyzer node error: {e}")
            state["mood"] = {
                "label": "neutral",
                "confidence": 0.5,
                "sentiment_score": 0,
                "emotional_state": "neutral",
                "energy_level": 5
            }
            return state

    def _estimate_energy_level(self, mood_result: Dict[str, Any]) -> int:
        """Estimate energy level (1-10) from mood analysis."""
        mood_label = mood_result.get("mood", {}).get("label", "neutral")
        sentiment = mood_result.get("mood", {}).get("sentiment_score", 0)

        # High energy moods
        if mood_label in ["excited", "motivated", "happy"]:
            return 8
        # Medium-high energy
        elif mood_label in ["content", "focused"]:
            return 6
        # Medium energy
        elif mood_label in ["neutral", "calm"]:
            return 5
        # Low energy
        elif mood_label in ["tired", "sad", "bored"]:
            return 3
        # Very low energy
        elif mood_label in ["overwhelmed", "anxious", "stressed"]:
            return 2
        else:
            # Use sentiment as backup
            return max(1, min(10, int((sentiment + 1) * 5)))

    def mode_detector_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Detect work vs personal mode."""
        try:
            input_text = state.get("input", "")
            mode = detect_mode(input_text)
            state["mode"] = mode

            # Add to agent path
            if "agent_path" not in state:
                state["agent_path"] = []
            state["agent_path"].append("ModeDetector")

            return state

        except Exception as e:
            logger.error(f"Mode detector node error: {e}")
            state["mode"] = "personal"
            return state

    def context_retriever_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Retrieve relevant context using RAG."""
        return self.context_retriever.retrieve_context(state)

    def task_analyzer_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Extract and analyze tasks from input."""
        try:
            input_text = state.get("input", "")
            mode = state.get("mode", "personal")

            # Extract task
            task_data = extract_task(input_text)

            # Create task list
            if task_data and task_data.get("title"):
                state["tasks"] = [task_data]
            else:
                state["tasks"] = []

            # Add to agent path
            if "agent_path" not in state:
                state["agent_path"] = []
            state["agent_path"].append("TaskAnalyzer")

            return state

        except Exception as e:
            logger.error(f"Task analyzer node error: {e}")
            state["tasks"] = []
            return state

    def burnout_detector_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Detect burnout risk."""
        return self.burnout_detector.detect(state)

    def prioritizer_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Boost task priorities based on mood."""
        try:
            tasks = state.get("tasks", [])
            mood_data = state.get("mood", {})
            mood_label = mood_data.get("label", "neutral")

            # Boost priority for each task
            for task in tasks:
                user_priority = task.get("priority", 5)
                ai_priority, reason = boost_priority(mood_label, user_priority)
                task["ai_priority"] = ai_priority
                task["effective_priority"] = ai_priority

            state["tasks"] = tasks

            # Add to agent path
            if "agent_path" not in state:
                state["agent_path"] = []
            state["agent_path"].append("Prioritizer")

            return state

        except Exception as e:
            logger.error(f"Prioritizer node error: {e}")
            return state

    def scheduler_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Schedule tasks optimally."""
        return self.scheduler.schedule_tasks(state)

    def recommendation_engine_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Generate final recommendations."""
        return self.recommendation_engine.generate(state)

    async def run(self, text: str, session_id: str = "default") -> Dict[str, Any]:
        """
        Run the multi-agent system.

        Args:
            text: User input
            session_id: Session identifier for memory

        Returns:
            Complete state with all agent outputs
        """
        try:
            # Initialize state
            initial_state = {
                "input": text,
                "user_id": None,
                "session_id": session_id,
                "conversation_history": [],
                "mode": None,
                "mood": None,
                "tasks": [],
                "context": None,
                "analytics": None,
                "current_agent": None,
                "agent_path": [],
                "next_action": None,
                "response": None,
                "recommendations": [],
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

            # Run the graph
            result = await self.graph.ainvoke(initial_state)

            logger.info(f"Graph completed. Agent path: {result.get('agent_path', [])}")

            return result

        except Exception as e:
            logger.error(f"Graph execution error: {e}")
            return {
                "error": str(e),
                "response": "I encountered an error processing your request. Please try again."
            }
