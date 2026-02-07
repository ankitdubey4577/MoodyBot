from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime
from .database import Base
# add to src/db/models.py
from sqlalchemy import Column, Integer, String,Float, DateTime
from datetime import datetime
from .database import Base

class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    start_time = Column(String, nullable=False)  # ISO string
    created_at = Column(DateTime, default=datetime.utcnow)

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True)
    title = Column(String)
    mode = Column(String)  # work | personal
    user_priority = Column(String)
    ai_priority = Column(String)
    effective_priority = Column(String)
    scheduled_time = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class MoodHistory(Base):
    __tablename__ = "mood_history"

    id = Column(Integer, primary_key=True)
    mood = Column(String)
    confidence = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)

class TaskFeedback(Base):
    __tablename__ = "task_feedback"

    id = Column(Integer, primary_key=True)
    task_id = Column(Integer)
    mood = Column(String)
    mode = Column(String)
    task_type = Column(String)
    completed = Column(Integer)  # 1 = yes, 0 = no
    time_taken = Column(Integer)  # minutes
    time_of_day = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)

class UserStats(Base):
    __tablename__ = "user_stats"

    id = Column(Integer, primary_key=True)
    current_streak = Column(Integer, default=0)
    last_active_date = Column(String)  # YYYY-MM-DD
    xp = Column(Integer, default=0)
    level = Column(Integer, default=1)

deadline = Column(String, nullable=True)
ai_priority = Column(String, nullable=True)
ai_priority_reason = Column(String, nullable=True)