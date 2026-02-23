"""
Data Collection Utilities for ML Training
Collects and prepares training data from database
"""
from typing import List, Dict, Any, Tuple
from datetime import datetime, timezone
import logging
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

class DataCollector:
    """
    Collects training data from the database for ML models.
    """

    def __init__(self, db_session: Session):
        """
        Initialize data collector.

        Args:
            db_session: Database session
        """
        self.db = db_session

    def collect_task_completion_data(self) -> List[Dict[str, Any]]:
        """
        Collect task completion data for time estimation model.

        Returns:
            List of task completion records
        """
        try:
            from src.db.models import Task, TaskFeedback

            # Get completed tasks with feedback
            results = self.db.query(Task, TaskFeedback).join(
                TaskFeedback, Task.id == TaskFeedback.task_id
            ).filter(
                TaskFeedback.completed == True
            ).all()

            data = []
            for task, feedback in results:
                record = {
                    'task_id': task.id,
                    'title': task.description or '',
                    'description': '',
                    'priority': self._priority_to_int(task.user_priority),
                    'mood': feedback.mood or 'neutral',
                    'mode': feedback.mode or 'work',
                    'time_taken': feedback.time_taken or 60,  # minutes
                    'time_of_day': feedback.time_of_day or 'morning',
                    'created_at': task.created_at,
                    'completed_at': feedback.timestamp
                }
                data.append(record)

            logger.info(f"Collected {len(data)} task completion records")
            return data

        except Exception as e:
            logger.error(f"Error collecting task data: {e}")
            return []

    def collect_priority_change_data(self) -> List[Dict[str, Any]]:
        """
        Collect data about user priority changes for priority prediction model.

        Returns:
            List of priority change records
        """
        try:
            from src.db.models import Task

            tasks = self.db.query(Task).all()

            data = []
            for task in tasks:
                if task.user_priority and task.ai_priority:
                    record = {
                        'task_id': task.id,
                        'title': task.description or '',
                        'user_priority': self._priority_to_int(task.user_priority),
                        'ai_priority': task.ai_priority,
                        'effective_priority': self._priority_to_int(task.effective_priority)
                        if task.effective_priority else task.ai_priority,
                        'mode': task.mode or 'work',
                        'created_at': task.created_at
                    }
                    data.append(record)

            logger.info(f"Collected {len(data)} priority change records")
            return data

        except Exception as e:
            logger.error(f"Error collecting priority data: {e}")
            return []

    def collect_mood_history_data(self) -> List[Dict[str, Any]]:
        """
        Collect mood history for burnout detection model.

        Returns:
            List of mood records
        """
        try:
            from src.db.models import MoodHistory

            moods = self.db.query(MoodHistory).order_by(MoodHistory.timestamp).all()

            data = []
            for mood in moods:
                record = {
                    'mood_id': mood.id,
                    'mood_label': mood.mood_label or 'neutral',
                    'energy_level': mood.energy_level or 5,
                    'sentiment_score': mood.sentiment_score or 0.0,
                    'timestamp': mood.timestamp
                }
                data.append(record)

            logger.info(f"Collected {len(data)} mood records")
            return data

        except Exception as e:
            logger.error(f"Error collecting mood data: {e}")
            return []

    def collect_productivity_metrics(self) -> List[Dict[str, Any]]:
        """
        Collect daily/weekly productivity metrics for forecasting model.

        Returns:
            List of productivity records
        """
        try:
            from src.db.models import Task, TaskFeedback
            from sqlalchemy import func

            # Get daily completion counts
            daily_stats = self.db.query(
                func.date(TaskFeedback.timestamp).label('date'),
                func.count(TaskFeedback.id).label('completed_tasks'),
                func.avg(TaskFeedback.time_taken).label('avg_time')
            ).filter(
                TaskFeedback.completed == True
            ).group_by(
                func.date(TaskFeedback.timestamp)
            ).all()

            data = []
            for stat in daily_stats:
                record = {
                    'date': stat.date,
                    'completed_tasks': stat.completed_tasks,
                    'avg_time': stat.avg_time or 60
                }
                data.append(record)

            logger.info(f"Collected {len(data)} productivity records")
            return data

        except Exception as e:
            logger.error(f"Error collecting productivity data: {e}")
            return []

    def generate_synthetic_training_data(self, num_samples: int = 100) -> Dict[str, List[Dict[str, Any]]]:
        """
        Generate synthetic training data for initial model training.
        Used when real data is insufficient.

        Args:
            num_samples: Number of synthetic samples to generate

        Returns:
            Dictionary with synthetic data for each model
        """
        import random
        import numpy as np

        # Synthetic task completion data
        task_data = []
        for i in range(num_samples):
            complexity = random.choice(['simple', 'medium', 'complex'])

            # Time taken correlates with complexity
            if complexity == 'simple':
                time_taken = random.randint(15, 60)
                title_words = random.randint(3, 6)
            elif complexity == 'medium':
                time_taken = random.randint(60, 180)
                title_words = random.randint(5, 10)
            else:  # complex
                time_taken = random.randint(180, 480)
                title_words = random.randint(8, 15)

            task_data.append({
                'task_id': i,
                'title': ' '.join(['word'] * title_words),
                'description': '',
                'priority': random.randint(1, 10),
                'mood': random.choice(['happy', 'neutral', 'stressed', 'tired']),
                'mode': random.choice(['work', 'personal']),
                'time_taken': time_taken,
                'time_of_day': random.choice(['morning', 'afternoon', 'evening']),
                'complexity': complexity
            })

        # Synthetic priority data
        priority_data = []
        for i in range(num_samples):
            urgency = random.choice(['low', 'medium', 'high'])

            if urgency == 'low':
                priority = random.randint(1, 4)
            elif urgency == 'medium':
                priority = random.randint(4, 7)
            else:
                priority = random.randint(7, 10)

            priority_data.append({
                'task_id': i,
                'title': f'Task {i}',
                'priority': priority,
                'urgency': urgency
            })

        # Synthetic mood/burnout data
        mood_data = []
        for i in range(num_samples):
            # Simulate burnout progression
            burnout_level = random.uniform(0, 1)

            if burnout_level < 0.3:
                mood = random.choice(['happy', 'content', 'neutral'])
                energy = random.randint(6, 10)
            elif burnout_level < 0.6:
                mood = random.choice(['neutral', 'tired', 'stressed'])
                energy = random.randint(4, 7)
            else:
                mood = random.choice(['stressed', 'overwhelmed', 'anxious'])
                energy = random.randint(1, 4)

            mood_data.append({
                'mood_label': mood,
                'energy_level': energy,
                'sentiment_score': np.random.normal(0, 0.5),
                'burnout_level': burnout_level
            })

        logger.info(f"Generated {num_samples} synthetic samples for each model")

        return {
            'task_completion': task_data,
            'priority_changes': priority_data,
            'mood_history': mood_data
        }

    @staticmethod
    def _priority_to_int(priority: str) -> int:
        """Convert priority string to integer."""
        if isinstance(priority, int):
            return priority

        priority_map = {
            'low': 3,
            'medium': 5,
            'high': 8,
            'urgent': 10
        }
        return priority_map.get(str(priority).lower(), 5)
