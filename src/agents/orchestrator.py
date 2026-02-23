"""
Orchestrator Agent - Coordinates all agents in the multi-agent system
"""
from typing import Dict, Any, List
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

class OrchestratorAgent:
    """
    Master agent that coordinates the workflow of all specialized agents.
    Decides which agents to invoke and in what order based on the input and state.
    """

    def __init__(self):
        self.name = "Orchestrator"

    def decide_workflow(self, state: Dict[str, Any]) -> str:
        """
        Analyze the current state and decide which agent should run next.

        Returns:
            str: Name of the next agent to invoke
        """
        input_text = state.get("input", "").lower()
        current_agent = state.get("current_agent")
        agent_path = state.get("agent_path", [])

        # Initial routing based on input
        if not agent_path:
            # Start with mood analysis
            return "mood_analyzer"

        # If mood is analyzed, check mode
        if "mood_analyzer" in agent_path and "mode_detector" not in agent_path:
            return "mode_detector"

        # If mode is detected, retrieve context (RAG)
        if "mode_detector" in agent_path and "context_retriever" not in agent_path:
            return "context_retriever"

        # Analyze tasks
        if "context_retriever" in agent_path and "task_analyzer" not in agent_path:
            return "task_analyzer"

        # Check for burnout
        if "task_analyzer" in agent_path and "burnout_detector" not in agent_path:
            return "burnout_detector"

        # Prioritize tasks
        if "burnout_detector" in agent_path and "prioritizer" not in agent_path:
            return "prioritizer"

        # Schedule tasks
        if "prioritizer" in agent_path and "scheduler" not in agent_path:
            return "scheduler"

        # Generate recommendations
        if "scheduler" in agent_path and "recommendation_engine" not in agent_path:
            return "recommendation_engine"

        # All agents complete
        return "END"

    def orchestrate(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main orchestration function - decides workflow and updates state.

        Args:
            state: Current agent state

        Returns:
            Updated state with next_action set
        """
        try:
            # Determine next action
            next_action = self.decide_workflow(state)

            # Update state
            state["current_agent"] = self.name
            state["next_action"] = next_action

            # Add to agent path
            if "agent_path" not in state:
                state["agent_path"] = []
            if self.name not in state["agent_path"]:
                state["agent_path"].append(self.name)

            # Log orchestration decision
            logger.info(f"Orchestrator: Next action -> {next_action}")

            return state

        except Exception as e:
            logger.error(f"Orchestrator error: {e}")
            state["next_action"] = "ERROR"
            return state

    def should_continue(self, state: Dict[str, Any]) -> str:
        """
        Routing function for LangGraph conditional edges.

        Args:
            state: Current state

        Returns:
            Name of next node or "END"
        """
        next_action = state.get("next_action", "END")
        return next_action
