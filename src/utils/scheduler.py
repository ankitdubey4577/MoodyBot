from typing import Dict, Any

class MoodScheduler:
    """
    Deterministic fallback scheduler for MoodyBot.
    Used when LLM scheduling is disabled or fails.
    """

    def schedule_task(self, task_name: str, mood: Dict[str, Any]) -> Dict[str, Any]:
        """
        Schedule a task based on mood analysis.
        Returns scheduling recommendation with time slot, tactic, and success probability.
        """
        mood_label = mood.get("label", "stuck")

        slots = {
            "fatigue": {
                "scheduled_time": "14:00-16:00",
                "tactic": "power_break",
                "success_prob": 0.94
            },
            "stuck": {
                "scheduled_time": "09:30-11:30",
                "tactic": "rubber_duck_debug",
                "success_prob": 0.94
            },
            "positive": {
                "scheduled_time": "09:00-11:00",
                "tactic": "momentum_build",
                "success_prob": 0.96
            }
        }

        slot = slots.get(mood_label, slots["stuck"])

        return {
            "scheduled_time": slot["scheduled_time"],
            "tactic": slot["tactic"],
            "success_prob": slot["success_prob"],
            "source": "rule_engine"
        }
