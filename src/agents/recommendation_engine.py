"""
Recommendation Engine - Generates intelligent recommendations based on all agent insights
"""
from typing import Dict, Any, List
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

class RecommendationEngine:
    """
    Synthesizes insights from all agents to generate actionable recommendations.
    Considers mood, tasks, burnout risk, schedule, and patterns.
    """

    def __init__(self):
        self.name = "RecommendationEngine"

    def generate_task_recommendations(self, state: Dict[str, Any]) -> List[str]:
        """Generate task-specific recommendations."""
        recommendations = []
        tasks = state.get("tasks") or []

        if not tasks:
            recommendations.append("📝 No tasks found. Start by adding your most important task.")
            return recommendations

        # Check task count
        if len(tasks) > 10:
            recommendations.append(
                f"📊 You have {len(tasks)} tasks. Consider focusing on top 3 priorities today."
            )

        # Check priorities
        high_priority = [t for t in tasks if t.get("effective_priority", 0) >= 7]
        if high_priority:
            recommendations.append(
                f"🎯 {len(high_priority)} high-priority tasks detected. "
                f"Start with: '{high_priority[0].get('title', 'Unknown')}'"
            )

        # Check estimated times
        total_time = sum(t.get("estimated_time", 0) for t in tasks)
        if total_time > 0:
            recommendations.append(
                f"⏱️ Total estimated time: {total_time:.1f} hours"
            )

        return recommendations

    def generate_mood_recommendations(self, state: Dict[str, Any]) -> List[str]:
        """Generate mood-based recommendations."""
        recommendations = []
        mood_data = state.get("mood") or {}

        mood_label = mood_data.get("label", "neutral")
        energy_level = mood_data.get("energy_level", 5)
        sentiment = mood_data.get("sentiment_score", 0)

        # Energy-based recommendations
        if energy_level >= 8:
            recommendations.append("⚡ High energy! Perfect time for challenging tasks.")
        elif energy_level <= 3:
            recommendations.append("🔋 Low energy detected. Take a break or do lighter tasks.")

        # Mood-based recommendations
        if mood_label in ["anxious", "overwhelmed", "stressed"]:
            recommendations.append(
                "🧘 Feeling stressed? Try a 5-minute breathing exercise before starting work."
            )
        elif mood_label in ["excited", "motivated", "happy"]:
            recommendations.append("🌟 Great mood! Leverage this energy for important work.")

        # Sentiment-based
        if sentiment < -0.5:
            recommendations.append(
                "💚 Negative sentiment detected. Remember to practice self-compassion."
            )

        return recommendations

    def generate_work_life_recommendations(self, state: Dict[str, Any]) -> List[str]:
        """Generate work-life balance recommendations."""
        recommendations = []
        mood_data = state.get("mood") or {}
        tasks = state.get("tasks") or []

        burnout_risk = mood_data.get("burnout_risk", 0)

        # Check work-life balance
        if burnout_risk > 0.5:
            recommendations.append(
                "⚖️ High stress detected. Schedule personal time today - it's essential."
            )

        # General wellness
        recommendations.append("💧 Remember to stay hydrated and take regular breaks.")

        return recommendations

    def generate_productivity_recommendations(self, state: Dict[str, Any]) -> List[str]:
        """Generate productivity optimization recommendations."""
        recommendations = []
        analytics = state.get("analytics") or {}

        completion_rate = analytics.get("completion_rate", 0)

        if completion_rate < 0.5 and completion_rate > 0:
            recommendations.append(
                "📈 Completion rate is low. Try breaking tasks into smaller, achievable steps."
            )
        elif completion_rate >= 0.8:
            recommendations.append("🎉 Excellent completion rate! Keep up the momentum.")

        return recommendations

    def synthesize_final_response(self, state: Dict[str, Any]) -> str:
        """
        Create a comprehensive response based on all agent insights.

        Args:
            state: Complete state with all agent outputs

        Returns:
            Final synthesized response
        """
        mood_data = state.get("mood") or {}
        tasks = state.get("tasks") or []
        recommendations = state.get("recommendations") or []

        response_parts = []

        # Mood summary
        mood_label = mood_data.get("label", "neutral")
        energy_level = mood_data.get("energy_level", 5)
        response_parts.append(f"**Current State:** {mood_label.title()} (Energy: {energy_level}/10)")

        # Task summary
        if tasks:
            response_parts.append(f"\n**Tasks:** {len(tasks)} total")

            # Show top 3 tasks
            top_tasks = sorted(tasks, key=lambda t: -t.get("effective_priority", 0))[:3]
            response_parts.append("\n**Top Priorities:**")
            for i, task in enumerate(top_tasks, 1):
                title = task.get("title", "Unknown")
                priority = task.get("effective_priority", 0)
                time_slot = task.get("recommended_time_slot", "Anytime")
                response_parts.append(f"{i}. {title} (Priority: {priority}/10) - {time_slot}")

        # Burnout warning
        burnout_risk = mood_data.get("burnout_risk", 0)
        burnout_level = mood_data.get("burnout_level", "MINIMAL")
        if burnout_risk > 0.4:
            response_parts.append(f"\n⚠️ **Burnout Risk:** {burnout_level} ({burnout_risk*100:.0f}%)")

        # Recommendations
        if recommendations:
            response_parts.append("\n**Recommendations:**")
            # Show top 5 recommendations
            for rec in recommendations[:5]:
                response_parts.append(f"• {rec}")

        return "\n".join(response_parts)

    def generate(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main recommendation generation function.

        Args:
            state: Current agent state

        Returns:
            Updated state with final recommendations and response
        """
        try:
            # Generate all types of recommendations
            task_recs = self.generate_task_recommendations(state)
            mood_recs = self.generate_mood_recommendations(state)
            worklife_recs = self.generate_work_life_recommendations(state)
            productivity_recs = self.generate_productivity_recommendations(state)

            # Combine all recommendations
            all_recommendations = task_recs + mood_recs + worklife_recs + productivity_recs

            # Add to existing recommendations
            if "recommendations" not in state:
                state["recommendations"] = []
            state["recommendations"].extend(all_recommendations)

            # Generate final response
            final_response = self.synthesize_final_response(state)
            state["response"] = final_response

            # Update agent tracking
            state["current_agent"] = self.name
            if "agent_path" not in state:
                state["agent_path"] = []
            if self.name not in state["agent_path"]:
                state["agent_path"].append(self.name)

            logger.info(f"Recommendations: Generated {len(all_recommendations)} recommendations")

            return state

        except Exception as e:
            logger.error(f"Recommendation engine error: {e}")
            return state
