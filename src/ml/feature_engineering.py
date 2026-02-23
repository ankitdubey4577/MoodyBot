"""
Feature Engineering for ML Models
Extracts and transforms features from tasks, mood, and user behavior
"""
from typing import Dict, Any, List
from datetime import datetime, timezone
import re
import logging

logger = logging.getLogger(__name__)

class FeatureEngine:
    """
    Extracts features from raw data for ML model training and prediction.
    """

    # Common action verbs indicating task complexity
    COMPLEX_VERBS = {
        'implement', 'develop', 'build', 'design', 'architect', 'refactor',
        'analyze', 'investigate', 'research', 'plan', 'create', 'integrate'
    }

    SIMPLE_VERBS = {
        'review', 'check', 'update', 'fix', 'merge', 'deploy', 'test',
        'call', 'email', 'message', 'send', 'reply'
    }

    URGENT_KEYWORDS = {
        'urgent', 'asap', 'immediately', 'critical', 'emergency', 'hotfix',
        'deadline', 'today', 'now', 'quick', 'fast'
    }

    def __init__(self):
        self.name = "FeatureEngine"

    def extract_task_features(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract features from a task.

        Args:
            task: Task dictionary

        Returns:
            Feature dictionary
        """
        title = task.get('title', '')
        description = task.get('description', '')
        priority = task.get('priority', 5)

        # Text-based features
        title_length = len(title)
        description_length = len(description)
        total_text_length = title_length + description_length

        # Word counts
        title_words = len(title.split())
        description_words = len(description.split())
        total_words = title_words + description_words

        # Complexity indicators
        has_complex_verb = any(verb in title.lower() for verb in self.COMPLEX_VERBS)
        has_simple_verb = any(verb in title.lower() for verb in self.SIMPLE_VERBS)

        complexity_score = 0
        if has_complex_verb:
            complexity_score += 2
        if has_simple_verb:
            complexity_score += 1
        if total_words > 15:
            complexity_score += 1
        if description_length > 200:
            complexity_score += 1

        # Urgency indicators
        has_urgent_keyword = any(keyword in title.lower() or keyword in description.lower()
                                  for keyword in self.URGENT_KEYWORDS)
        urgency_score = 2 if has_urgent_keyword else 0

        # Technical indicators
        has_code_reference = bool(re.search(r'(function|class|api|database|server|deploy)',
                                            title.lower() + ' ' + description.lower()))

        # Time-related features
        has_deadline = 'deadline' in title.lower() or 'deadline' in description.lower()
        has_time_estimate = bool(re.search(r'\d+\s*(hour|hr|min|day)',
                                           title.lower() + ' ' + description.lower()))

        return {
            # Text features
            'title_length': title_length,
            'description_length': description_length,
            'total_text_length': total_text_length,
            'title_words': title_words,
            'description_words': description_words,
            'total_words': total_words,

            # Complexity features
            'has_complex_verb': int(has_complex_verb),
            'has_simple_verb': int(has_simple_verb),
            'complexity_score': complexity_score,

            # Urgency features
            'has_urgent_keyword': int(has_urgent_keyword),
            'urgency_score': urgency_score,

            # Technical features
            'has_code_reference': int(has_code_reference),
            'has_deadline': int(has_deadline),
            'has_time_estimate': int(has_time_estimate),

            # Priority
            'priority': priority
        }

    def extract_mood_features(self, mood_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract features from mood data.

        Args:
            mood_data: Mood dictionary

        Returns:
            Feature dictionary
        """
        mood_label = mood_data.get('label', 'neutral')
        energy_level = mood_data.get('energy_level', 5)
        sentiment_score = mood_data.get('sentiment_score', 0)
        confidence = mood_data.get('confidence', 0.5)

        # Mood categories (one-hot encoding)
        mood_positive = int(mood_label in ['happy', 'excited', 'motivated', 'content'])
        mood_negative = int(mood_label in ['sad', 'anxious', 'stressed', 'overwhelmed'])
        mood_neutral = int(mood_label in ['neutral', 'calm', 'tired', 'bored'])

        # Energy categories
        energy_high = int(energy_level >= 7)
        energy_medium = int(3 <= energy_level < 7)
        energy_low = int(energy_level < 3)

        # Sentiment categories
        sentiment_positive = int(sentiment_score > 0.2)
        sentiment_negative = int(sentiment_score < -0.2)
        sentiment_neutral = int(-0.2 <= sentiment_score <= 0.2)

        return {
            'energy_level': energy_level,
            'sentiment_score': sentiment_score,
            'mood_confidence': confidence,

            # Mood categories
            'mood_positive': mood_positive,
            'mood_negative': mood_negative,
            'mood_neutral': mood_neutral,

            # Energy categories
            'energy_high': energy_high,
            'energy_medium': energy_medium,
            'energy_low': energy_low,

            # Sentiment categories
            'sentiment_positive': sentiment_positive,
            'sentiment_negative': sentiment_negative,
            'sentiment_neutral': sentiment_neutral
        }

    def extract_temporal_features(self, timestamp: datetime = None) -> Dict[str, Any]:
        """
        Extract time-based features.

        Args:
            timestamp: Timestamp (default: now)

        Returns:
            Feature dictionary
        """
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)

        hour = timestamp.hour
        day_of_week = timestamp.weekday()  # 0=Monday, 6=Sunday
        day_of_month = timestamp.day
        month = timestamp.month

        # Time of day categories
        is_morning = int(6 <= hour < 12)
        is_afternoon = int(12 <= hour < 18)
        is_evening = int(18 <= hour < 22)
        is_night = int(hour >= 22 or hour < 6)

        # Day categories
        is_weekday = int(day_of_week < 5)
        is_weekend = int(day_of_week >= 5)
        is_monday = int(day_of_week == 0)
        is_friday = int(day_of_week == 4)

        return {
            'hour': hour,
            'day_of_week': day_of_week,
            'day_of_month': day_of_month,
            'month': month,

            # Time categories
            'is_morning': is_morning,
            'is_afternoon': is_afternoon,
            'is_evening': is_evening,
            'is_night': is_night,

            # Day categories
            'is_weekday': is_weekday,
            'is_weekend': is_weekend,
            'is_monday': is_monday,
            'is_friday': is_friday
        }

    def extract_workload_features(self, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Extract workload-related features.

        Args:
            tasks: List of tasks

        Returns:
            Feature dictionary
        """
        if not tasks:
            return {
                'total_tasks': 0,
                'high_priority_tasks': 0,
                'medium_priority_tasks': 0,
                'low_priority_tasks': 0,
                'avg_priority': 0,
                'total_estimated_time': 0,
                'workload_score': 0
            }

        total_tasks = len(tasks)
        priorities = [t.get('priority', 5) for t in tasks]

        high_priority = sum(1 for p in priorities if p >= 7)
        medium_priority = sum(1 for p in priorities if 4 <= p < 7)
        low_priority = sum(1 for p in priorities if p < 4)

        avg_priority = sum(priorities) / len(priorities) if priorities else 0

        # Estimated time
        estimated_times = [t.get('estimated_time', 0) for t in tasks]
        total_estimated_time = sum(estimated_times)

        # Workload score (0-100)
        workload_score = min(100, (total_tasks * 5) + (high_priority * 10) + (total_estimated_time * 2))

        return {
            'total_tasks': total_tasks,
            'high_priority_tasks': high_priority,
            'medium_priority_tasks': medium_priority,
            'low_priority_tasks': low_priority,
            'avg_priority': avg_priority,
            'total_estimated_time': total_estimated_time,
            'workload_score': workload_score
        }

    def combine_features(self,
                        task: Dict[str, Any] = None,
                        mood: Dict[str, Any] = None,
                        tasks_list: List[Dict[str, Any]] = None,
                        timestamp: datetime = None) -> Dict[str, Any]:
        """
        Combine all features into a single feature vector.

        Args:
            task: Task data
            mood: Mood data
            tasks_list: List of all tasks
            timestamp: Timestamp

        Returns:
            Combined feature dictionary
        """
        features = {}

        # Task features
        if task:
            task_features = self.extract_task_features(task)
            features.update(task_features)

        # Mood features
        if mood:
            mood_features = self.extract_mood_features(mood)
            features.update(mood_features)

        # Temporal features
        temporal_features = self.extract_temporal_features(timestamp)
        features.update(temporal_features)

        # Workload features
        if tasks_list:
            workload_features = self.extract_workload_features(tasks_list)
            features.update(workload_features)

        return features

    def get_feature_names(self) -> List[str]:
        """Get list of all possible feature names."""
        return [
            # Task features
            'title_length', 'description_length', 'total_text_length',
            'title_words', 'description_words', 'total_words',
            'has_complex_verb', 'has_simple_verb', 'complexity_score',
            'has_urgent_keyword', 'urgency_score',
            'has_code_reference', 'has_deadline', 'has_time_estimate',
            'priority',

            # Mood features
            'energy_level', 'sentiment_score', 'mood_confidence',
            'mood_positive', 'mood_negative', 'mood_neutral',
            'energy_high', 'energy_medium', 'energy_low',
            'sentiment_positive', 'sentiment_negative', 'sentiment_neutral',

            # Temporal features
            'hour', 'day_of_week', 'day_of_month', 'month',
            'is_morning', 'is_afternoon', 'is_evening', 'is_night',
            'is_weekday', 'is_weekend', 'is_monday', 'is_friday',

            # Workload features
            'total_tasks', 'high_priority_tasks', 'medium_priority_tasks',
            'low_priority_tasks', 'avg_priority', 'total_estimated_time',
            'workload_score'
        ]
