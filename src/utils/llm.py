from langchain_ollama import OllamaLLM as LangchainOllama
from langchain.prompts import PromptTemplate
import os

class OllamaClient:
    def __init__(self):
        self.model = LangchainOllama(
            model=os.getenv("OLLAMA_MODEL", "llama3"),
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        )
    
    def get_mood_analyzer(self):
        prompt = PromptTemplate.from_template("""
        Analyze this developer statement for emotional blockers.

        Categories: fatigue, stuck, anxiety, procrastination, overwhelm, distraction, positive

        Statement: {input}

        Respond with JSON:
        {{
          "primary_mood": "category",
          "confidence": 0.85,
          "reasoning": "explanation"
        }}
        """)
        return prompt | self.model

    def get_scheduler(self):
        prompt = PromptTemplate.from_template("""
        Based on mood: {mood} and task: {task}

        Recommend optimal time slot and tactic from:
        - power_break (15min)
        - rubber_duck_debug (15min)
        - pomodoro_start (25min)

        Return JSON:
        {{
          "scheduled_time": "09:30-11:30",
          "tactic": "rubber_duck_debug",
          "success_prob": 0.94
        }}
        """)
        return prompt | self.model
