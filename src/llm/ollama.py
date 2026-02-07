from langchain.llms import Ollama

class FreeLLM:
    def __init__(self):
        self.llm = Ollama(model="llama3")

    def ask(self, prompt: str) -> str:
        return self.llm.invoke(prompt)
