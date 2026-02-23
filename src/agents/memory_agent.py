"""
Memory Agent - Manages conversation history and long-term memory
"""
from typing import Dict, Any, List
from datetime import datetime, timezone
import json
import logging

logger = logging.getLogger(__name__)

class MemoryAgent:
    """
    Manages short-term conversation memory and long-term user patterns.
    Stores and retrieves conversation context.
    """

    def __init__(self, max_history: int = 20):
        self.name = "MemoryAgent"
        self.max_history = max_history
        self.conversation_store: Dict[str, List[Dict[str, Any]]] = {}

    def add_message(self, session_id: str, agent: str, content: str, metadata: Dict[str, Any] = None) -> None:
        """
        Add a message to conversation history.

        Args:
            session_id: Session identifier
            agent: Agent that generated the message
            content: Message content
            metadata: Additional metadata
        """
        if session_id not in self.conversation_store:
            self.conversation_store[session_id] = []

        message = {
            "agent": agent,
            "content": content,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metadata": metadata or {}
        }

        self.conversation_store[session_id].append(message)

        # Trim history if too long
        if len(self.conversation_store[session_id]) > self.max_history:
            self.conversation_store[session_id] = self.conversation_store[session_id][-self.max_history:]

    def get_conversation_history(self, session_id: str, last_n: int = None) -> List[Dict[str, Any]]:
        """
        Retrieve conversation history for a session.

        Args:
            session_id: Session identifier
            last_n: Number of recent messages to retrieve (default: all)

        Returns:
            List of conversation messages
        """
        if session_id not in self.conversation_store:
            return []

        history = self.conversation_store[session_id]
        if last_n:
            return history[-last_n:]
        return history

    def clear_history(self, session_id: str) -> None:
        """Clear conversation history for a session."""
        if session_id in self.conversation_store:
            del self.conversation_store[session_id]

    def get_context_summary(self, session_id: str, max_messages: int = 5) -> str:
        """
        Generate a summary of recent conversation context.

        Args:
            session_id: Session identifier
            max_messages: Number of recent messages to include

        Returns:
            Summary string
        """
        history = self.get_conversation_history(session_id, last_n=max_messages)

        if not history:
            return "No conversation history available."

        summary_parts = []
        for msg in history:
            agent = msg["agent"]
            content = msg["content"][:100]  # Truncate long messages
            summary_parts.append(f"[{agent}] {content}")

        return "\n".join(summary_parts)

    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process state and manage memory.

        Args:
            state: Current agent state

        Returns:
            Updated state with conversation history
        """
        try:
            session_id = state.get("session_id", "default")
            input_text = state.get("input", "")

            # Add user input to history
            if input_text:
                self.add_message(
                    session_id=session_id,
                    agent="User",
                    content=input_text,
                    metadata={"timestamp": datetime.now(timezone.utc).isoformat()}
                )

            # Retrieve conversation history
            conversation_history = self.get_conversation_history(session_id)

            # Update state
            state["conversation_history"] = conversation_history
            state["current_agent"] = self.name

            # Add to agent path
            if "agent_path" not in state:
                state["agent_path"] = []
            if self.name not in state["agent_path"]:
                state["agent_path"].append(self.name)

            logger.info(f"Memory: Loaded {len(conversation_history)} messages")

            return state

        except Exception as e:
            logger.error(f"Memory agent error: {e}")
            return state

    def store_agent_response(self, state: Dict[str, Any], agent_name: str, response: str) -> None:
        """
        Store an agent's response in memory.

        Args:
            state: Current state
            agent_name: Name of the agent
            response: Response content
        """
        session_id = state.get("session_id", "default")
        self.add_message(
            session_id=session_id,
            agent="agent_name",
            content=response,
            metadata={"state_snapshot": {k: v for k, v in state.items() if k != "conversation_history"}}
        )
