# MoodyBot 3.0

AI-powered productivity coach with mood-aware task management.

## Features

- **Mood Analysis**: Detects emotional blockers and suggests appropriate tasks
- **Smart Scheduling**: Auto-schedules tasks based on mood and calendar
- **Multi-Mode**: Work and Personal mode support
- **LangGraph Integration**: Multi-agent workflow orchestration
- **Gamification**: XP, levels, and streak tracking
- **Analytics**: Mood-productivity correlation insights

## Tech Stack

- **Backend**: FastAPI + SQLAlchemy + SQLite
- **Frontend**: Streamlit
- **AI/LLM**: Ollama (Llama3) via LangChain
- **Orchestration**: LangGraph
- **NLP**: spaCy + VADER Sentiment

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Initialize database:
```bash
python init_db.py
```

3. Start backend API:
```bash
uvicorn api.main:app --reload
```

4. Start Streamlit UI:
```bash
streamlit run main.py
# or
streamlit run app/streamlit_app.py
```

## Environment Variables

- `MOODYBOT_API_URL`: Backend API URL (default: http://localhost:8000)
- `OLLAMA_MODEL`: Ollama model name (default: llama3)
- `OLLAMA_BASE_URL`: Ollama server URL (default: http://localhost:11434)

## Architecture

```
api/
  main.py           # FastAPI backend
app/
  streamlit_app.py  # Full-featured Streamlit UI
main.py             # Simplified Streamlit UI
src/
  agents/           # LangGraph agents
  db/              # SQLAlchemy models
  graph/           # LangGraph workflow
  llm/             # LLM clients
  models/          # Pydantic schemas
  utils/           # Helper functions
```