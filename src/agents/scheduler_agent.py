"""
Scheduler Agent - Optimizes task scheduling based on mood, energy, and patterns
"""
from typing import Dict, Any, List
from datetime import datetime, timezone, timedelta
import logging

logger = logging.getLogger(__name__)

class SchedulerAgent:
    """
    Intelligent task scheduler that considers:
    - Current mood and energy level
    - Task complexity and priority
    - Optimal work patterns
    - Available time slots
    """

    def __init__(self):
        self.name = "SchedulerAgent"

    def estimate_task_duration(self, task: Dict[str, Any]) -> float:
        """
        Estimate task duration based on description and priority.

        Args:
            task: Task data

        Returns:
            Estimated hours
        """
        # Simple heuristic (will be replaced with ML model)
        title = task.get("title", "")
        description = task.get("description", "")
        priority = task.get("effective_priority", 3)

        # Base estimate on text length
        text_length = len(title) + len(description)

        if text_length < 50:
            base_hours = 0.5
        elif text_length < 100:
            base_hours = 1.0
        elif text_length < 200:
            base_hours = 2.0
        else:
            base_hours = 4.0

        # Adjust for priority (high priority might have more complexity)
        if priority >= 8:
            base_hours *= 1.3
        elif priority <= 3:
            base_hours *= 0.8

        return round(base_hours, 1)

    def get_optimal_time_slot(self, task: Dict[str, Any], mood_data: Dict[str, Any]) -> str:
        """
        Determine optimal time slot for task based on mood and energy.

        Args:
            task: Task data
            mood_data: Current mood analysis

        Returns:
            Recommended time slot
        """
        energy_level = mood_data.get("energy_level", 5)
        priority = task.get("effective_priority", 5)
        estimated_hours = task.get("estimated_time", 1.0)

        # High energy + high priority = morning
        if energy_level >= 7 and priority >= 7:
            return "Morning (9-12 AM) - Peak focus time"

        # Medium energy = afternoon
        elif energy_level >= 4:
            if estimated_hours >= 2:
                return "Afternoon (1-4 PM) - Deep work session"
            else:
                return "Afternoon (2-5 PM) - Quick tasks"

        # Low energy = evening (lighter tasks)
        else:
            return "Evening (5-7 PM) - Light tasks only"

    def schedule_tasks(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Schedule tasks optimally based on mood, priority, and patterns.

        Args:
            state: Current agent state

        Returns:
            Updated state with scheduled tasks
        """
        try:
            tasks = state.get("tasks", [])
            mood_data = state.get("mood", {})

            if not tasks:
                logger.info("No tasks to schedule")
                return state

            # Schedule each task
            scheduled_tasks = []
            for task in tasks:
                # Estimate duration
                if not task.get("estimated_time"):
                    task["estimated_time"] = self.estimate_task_duration(task)

                # Determine optimal slot
                task["recommended_time_slot"] = self.get_optimal_time_slot(task, mood_data)

                # Add scheduling metadata
                task["scheduled_by"] = self.name
                task["scheduled_at"] = datetime.now(timezone.utc).isoformat()

                scheduled_tasks.append(task)

            # Sort by priority and optimal slot
            scheduled_tasks.sort(
                key=lambda t: (
                    -t.get("effective_priority", 0),
                    t.get("estimated_time", 0)
                )
            )

            # Update state
            state["tasks"] = scheduled_tasks
            state["current_agent"] = self.name

            # Add to agent path
            if "agent_path" not in state:
                state["agent_path"] = []
            if self.name not in state["agent_path"]:
                state["agent_path"].append(self.name)

            logger.info(f"Scheduler: Scheduled {len(scheduled_tasks)} tasks")

            return state

        except Exception as e:
            logger.error(f"Scheduler error: {e}")
            return state

    def generate_schedule_recommendations(self, state: Dict[str, Any]) -> List[str]:
        """
        Generate schedule optimization recommendations.

        Args:
            state: Current state

        Returns:
            List of recommendations
        """
        recommendations = []
        tasks = state.get("tasks", [])
        mood_data = state.get("mood", {})

        if not tasks:
            return ["No tasks to schedule. Add some tasks to get started!"]

        # Check total estimated time
        total_hours = sum(t.get("estimated_time", 0) for t in tasks)

        if total_hours > 8:
            recommendations.append(
                f"⚠️ You have {total_hours:.1f} hours of work scheduled. "
                f"Consider breaking tasks into smaller chunks or delegating."
            )

        # Check energy level
        energy = mood_data.get("energy_level", 5)
        if energy < 4:
            recommendations.append(
                "🔋 Low energy detected. Schedule breaks every 60 minutes and "
                "focus on lighter tasks first."
            )
        elif energy >= 7:
            recommendations.append(
                "⚡ High energy! Great time for complex tasks. "
                "Tackle your most challenging work now."
            )

        # Priority distribution
        high_priority = sum(1 for t in tasks if t.get("effective_priority", 0) >= 7)
        if high_priority > 3:
            recommendations.append(
                f"🎯 You have {high_priority} high-priority tasks. "
                f"Focus on 1-2 at a time to avoid overwhelm."
            )

        return recommendations
