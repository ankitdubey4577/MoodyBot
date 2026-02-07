from src.db.database import SessionLocal
from src.db.models import TaskFeedback
from sqlalchemy import func

def mood_productivity():
    db = SessionLocal()
    rows = db.query(
        TaskFeedback.mood,
        func.avg(TaskFeedback.completed)
    ).group_by(TaskFeedback.mood).all()
    db.close()
    return {mood: rate for mood, rate in rows}
