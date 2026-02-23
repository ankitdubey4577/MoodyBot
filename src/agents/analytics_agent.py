from src.db.database import SessionLocal
from src.db.models import TaskFeedback
from typing import Dict

def mood_productivity() -> Dict[str, float]:
    """
    Analyze productivity success rate by mood.
    Returns dict mapping mood to average completion rate.
    """
    db = SessionLocal()
    try:
        # Get all feedback entries
        feedback_entries = db.query(TaskFeedback).filter(TaskFeedback.mood.isnot(None)).all()

        # Group by mood and calculate completion rates in Python
        mood_stats = {}
        for entry in feedback_entries:
            mood = entry.mood
            if mood not in mood_stats:
                mood_stats[mood] = {'completed': 0, 'total': 0}
            mood_stats[mood]['total'] += 1
            if entry.completed:
                mood_stats[mood]['completed'] += 1

        # Calculate completion rates
        return {
            mood: stats['completed'] / stats['total'] if stats['total'] > 0 else 0.0
            for mood, stats in mood_stats.items()
        }
    finally:
        db.close()
