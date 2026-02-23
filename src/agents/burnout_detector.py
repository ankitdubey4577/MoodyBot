"""
Burnout Detector Agent - Monitors for signs of burnout and fatigue
"""
from typing import Dict, Any, List
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

class BurnoutDetector:
    """
    Detects early signs of burnout based on:
    - Mood patterns
    - Task completion rates
    - Work hours
    - Energy levels
    - Sentiment trends
    """

    def __init__(self):
        self.name = "BurnoutDetector"
        self.burnout_thresholds = {
            "critical": 0.8,
            "high": 0.6,
            "moderate": 0.4,
            "low": 0.2
        }

    def calculate_burnout_score(self, state: Dict[str, Any]) -> float:
        """
        Calculate burnout risk score (0-1).

        Args:
            state: Current agent state

        Returns:
            Burnout score (0 = no risk, 1 = critical)
        """
        mood_data = state.get("mood") or {}
        tasks = state.get("tasks") or []
        analytics = state.get("analytics") or {}

        # Factor 1: Mood/Energy (40% weight)
        mood_label = mood_data.get("label", "neutral")
        energy_level = mood_data.get("energy_level", 5)

        mood_score = 0
        if mood_label in ["anxious", "overwhelmed", "stressed"]:
            mood_score += 0.3
        if energy_level < 3:
            mood_score += 0.1

        # Factor 2: Task Load (30% weight)
        task_count = len(tasks)
        high_priority_count = sum(1 for t in tasks if t.get("effective_priority", 0) >= 7)

        task_score = 0
        if task_count > 10:
            task_score += 0.15
        if high_priority_count > 5:
            task_score += 0.15

        # Factor 3: Sentiment (20% weight)
        sentiment_score_raw = mood_data.get("sentiment_score", 0)
        sentiment_score = 0
        if sentiment_score_raw < -0.5:
            sentiment_score = 0.2
        elif sentiment_score_raw < -0.2:
            sentiment_score = 0.1

        # Factor 4: Completion Rate (10% weight)
        completion_rate = analytics.get("completion_rate", 0.7)
        completion_score = 0
        if completion_rate < 0.4:
            completion_score = 0.1

        # Total score
        burnout_score = mood_score + task_score + sentiment_score + completion_score
        return min(burnout_score, 1.0)

    def get_burnout_level(self, score: float) -> str:
        """Get burnout risk level from score."""
        if score >= self.burnout_thresholds["critical"]:
            return "CRITICAL"
        elif score >= self.burnout_thresholds["high"]:
            return "HIGH"
        elif score >= self.burnout_thresholds["moderate"]:
            return "MODERATE"
        elif score >= self.burnout_thresholds["low"]:
            return "LOW"
        else:
            return "MINIMAL"

    def generate_burnout_recommendations(self, score: float, level: str) -> List[str]:
        """
        Generate recommendations based on burnout level.

        Args:
            score: Burnout score
            level: Risk level

        Returns:
            List of actionable recommendations
        """
        recommendations = []

        if level == "CRITICAL":
            recommendations.extend([
                "🚨 CRITICAL: High burnout risk detected. Consider taking immediate action.",
                "🛑 Take a break NOW. Step away from work for at least 30 minutes.",
                "📞 Reach out to a manager or colleague for support.",
                "🎯 Delegate or postpone non-urgent tasks.",
                "💤 Ensure you get adequate sleep tonight (7-9 hours)."
            ])

        elif level == "HIGH":
            recommendations.extend([
                "⚠️ HIGH burnout risk. Take preventive measures now.",
                "🌿 Schedule a longer break (15-20 minutes) within the next hour.",
                "📝 Reduce your workload - aim for 50% less today.",
                "🧘 Practice a quick relaxation technique (deep breathing, stretching).",
                "📅 Block time for self-care activities this week."
            ])

        elif level == "MODERATE":
            recommendations.extend([
                "⚡ Moderate stress detected. Be mindful of your limits.",
                "☕ Take regular breaks (5-10 minutes every hour).",
                "🎯 Focus on 2-3 priority tasks, defer others.",
                "🚶 Get some physical movement - walk around for 5 minutes.",
                "💬 Consider talking to someone if you're feeling overwhelmed."
            ])

        elif level == "LOW":
            recommendations.extend([
                "✅ You're managing well! Keep up the good habits.",
                "🎯 Maintain current pace, don't overload yourself.",
                "🌟 Remember to celebrate small wins.",
                "⏰ Continue taking regular breaks."
            ])

        else:  # MINIMAL
            recommendations.extend([
                "🎉 Excellent! No burnout signs detected.",
                "💪 You're in a good mental state for productivity.",
                "🌟 Great work-life balance!"
            ])

        return recommendations

    def detect(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main detection function - analyzes state for burnout signs.

        Args:
            state: Current agent state

        Returns:
            Updated state with burnout analysis
        """
        try:
            # Calculate burnout score
            burnout_score = self.calculate_burnout_score(state)
            burnout_level = self.get_burnout_level(burnout_score)

            # Generate recommendations
            recommendations = self.generate_burnout_recommendations(burnout_score, burnout_level)

            # Update mood data with burnout info
            if "mood" not in state:
                state["mood"] = {}

            state["mood"]["burnout_risk"] = burnout_score
            state["mood"]["burnout_level"] = burnout_level

            # Add recommendations to state
            if "recommendations" not in state:
                state["recommendations"] = []
            state["recommendations"].extend(recommendations)

            # Update agent tracking
            state["current_agent"] = self.name
            if "agent_path" not in state:
                state["agent_path"] = []
            if self.name not in state["agent_path"]:
                state["agent_path"].append(self.name)

            logger.info(f"Burnout: Risk level = {burnout_level} ({burnout_score:.2f})")

            return state

        except Exception as e:
            logger.error(f"Burnout detector error: {e}")
            return state
