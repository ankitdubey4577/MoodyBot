from langgraph.graph import StateGraph, END
from src.agents.mood_agent import detect_mood
from src.agents.mode_agent import detect_mode
from src.agents.task_nlp_agent import extract_task
from src.agents.priority_agent import boost_priority
from src.agents.personal_booster_agent import suggest_boosters

class MoodyBotGraph:
    def __init__(self):
        self.graph = self.build()

    def build(self):
        g = StateGraph(dict)

        g.add_node("analyze", self.analyze)
        g.set_entry_point("analyze")
        g.add_edge("analyze", END)

        return g.compile()

    def analyze(self, state):
        """
        Analyze user input and determine mode, mood, and tasks.
        """
        # Validate input exists
        if "input" not in state:
            raise ValueError("State must contain 'input' key")

        text = state["input"]

        mode = detect_mode(text)
        mood_data = detect_mood(text)

        if mode == "personal":
            return {
                "mode": mode,
                "mood": mood_data["mood"],
                "tasks": suggest_boosters(mood_data["mood"]),
                "agent_path": []
            }

        task = extract_task(text)
        ai_priority, reason = boost_priority(mood_data["mood"], task["user_priority"])

        task["ai_priority"] = ai_priority
        task["effective_priority"] = ai_priority

        return {
            "mode": mode,
            "mood": mood_data["mood"],
            "tasks": [task],
            "agent_path": []
        }

    async def run(self, text: str):
        return await self.graph.ainvoke({"input": text})
