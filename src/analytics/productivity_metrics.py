"""
Productivity Metrics Calculator
Computes comprehensive productivity metrics from task and mood data
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta, timezone
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

class ProductivityMetrics:
    """
    Calculates comprehensive productivity metrics.

    Metrics:
    - Tasks completed per day/week/month
    - Average completion time
    - Completion rate
    - Focus time vs break time
    - Productivity score
    - Efficiency metrics
    """

    def __init__(self):
        self.name = "ProductivityMetrics"

    def calculate_daily_metrics(self, tasks: List[Dict[str, Any]],
                                date: datetime = None) -> Dict[str, Any]:
        """
        Calculate productivity metrics for a specific day.

        Args:
            tasks: List of tasks
            date: Target date (default: today)

        Returns:
            Dictionary of daily metrics
        """
        if date is None:
            date = datetime.now(timezone.utc)

        # Filter tasks for the day
        day_tasks = self._filter_tasks_by_date(tasks, date, date)

        # Calculate metrics
        total_tasks = len(day_tasks)
        completed_tasks = sum(1 for t in day_tasks if t.get('status') == 'completed')
        pending_tasks = sum(1 for t in day_tasks if t.get('status') == 'pending')

        completion_rate = (completed_tasks / total_tasks) if total_tasks > 0 else 0

        # Time metrics
        total_time_spent = sum(t.get('time_taken', 0) for t in day_tasks if t.get('time_taken'))
        avg_time_per_task = (total_time_spent / completed_tasks) if completed_tasks > 0 else 0

        # Priority distribution
        high_priority_completed = sum(
            1 for t in day_tasks
            if t.get('status') == 'completed' and t.get('priority', 0) >= 7
        )

        # Productivity score (0-100)
        productivity_score = self._calculate_productivity_score(
            completion_rate=completion_rate,
            completed_tasks=completed_tasks,
            high_priority_completed=high_priority_completed,
            avg_time=avg_time_per_task
        )

        return {
            'date': date.strftime('%Y-%m-%d'),
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'pending_tasks': pending_tasks,
            'completion_rate': completion_rate,
            'total_time_spent_minutes': total_time_spent,
            'avg_time_per_task_minutes': avg_time_per_task,
            'high_priority_completed': high_priority_completed,
            'productivity_score': productivity_score
        }

    def calculate_weekly_metrics(self, tasks: List[Dict[str, Any]],
                                 week_start: datetime = None) -> Dict[str, Any]:
        """
        Calculate productivity metrics for a week.

        Args:
            tasks: List of tasks
            week_start: Start of week (default: this Monday)

        Returns:
            Dictionary of weekly metrics
        """
        if week_start is None:
            today = datetime.now(timezone.utc)
            week_start = today - timedelta(days=today.weekday())

        week_end = week_start + timedelta(days=6)

        # Filter tasks for the week
        week_tasks = self._filter_tasks_by_date(tasks, week_start, week_end)

        # Daily breakdown
        daily_metrics = []
        for i in range(7):
            day = week_start + timedelta(days=i)
            day_metrics = self.calculate_daily_metrics(tasks, day)
            daily_metrics.append(day_metrics)

        # Weekly aggregates
        total_completed = sum(d['completed_tasks'] for d in daily_metrics)
        total_tasks = sum(d['total_tasks'] for d in daily_metrics)
        avg_completion_rate = sum(d['completion_rate'] for d in daily_metrics) / 7
        total_time = sum(d['total_time_spent_minutes'] for d in daily_metrics)
        avg_productivity = sum(d['productivity_score'] for d in daily_metrics) / 7

        # Work pattern
        working_days = sum(1 for d in daily_metrics if d['total_tasks'] > 0)
        most_productive_day = max(daily_metrics, key=lambda d: d['productivity_score'])

        return {
            'week_start': week_start.strftime('%Y-%m-%d'),
            'week_end': week_end.strftime('%Y-%m-%d'),
            'total_tasks': total_tasks,
            'total_completed': total_completed,
            'avg_completion_rate': avg_completion_rate,
            'total_time_hours': total_time / 60,
            'avg_productivity_score': avg_productivity,
            'working_days': working_days,
            'most_productive_day': most_productive_day['date'],
            'daily_breakdown': daily_metrics
        }

    def calculate_focus_metrics(self, tasks: List[Dict[str, Any]],
                               mood_history: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Calculate focus and concentration metrics.

        Args:
            tasks: List of tasks
            mood_history: List of mood records

        Returns:
            Dictionary of focus metrics
        """
        # Deep work time (high priority, long duration tasks)
        deep_work_tasks = [
            t for t in tasks
            if t.get('priority', 0) >= 7 and t.get('time_taken', 0) >= 60
        ]
        deep_work_hours = sum(t.get('time_taken', 0) for t in deep_work_tasks) / 60

        # Quick tasks (< 30 min)
        quick_tasks = [t for t in tasks if t.get('time_taken', 0) < 30]
        quick_task_count = len(quick_tasks)

        # Focus sessions (tasks completed in focused mood)
        if mood_history:
            focused_sessions = sum(
                1 for m in mood_history
                if m.get('mood_label', '').lower() in ['focused', 'motivated']
            )
        else:
            focused_sessions = 0

        # Interruption estimate (based on task switching)
        task_switches = len(tasks) - 1 if len(tasks) > 1 else 0
        interruption_score = min(100, task_switches * 5)  # 5 points per switch

        # Focus score (0-100)
        focus_score = self._calculate_focus_score(
            deep_work_hours=deep_work_hours,
            interruptions=task_switches,
            focused_sessions=focused_sessions
        )

        return {
            'deep_work_hours': round(deep_work_hours, 2),
            'deep_work_tasks': len(deep_work_tasks),
            'quick_tasks': quick_task_count,
            'focused_sessions': focused_sessions,
            'interruption_score': interruption_score,
            'focus_score': focus_score
        }

    def calculate_efficiency_metrics(self, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate efficiency and time utilization metrics.

        Args:
            tasks: List of tasks

        Returns:
            Dictionary of efficiency metrics
        """
        completed_tasks = [t for t in tasks if t.get('status') == 'completed']

        if not completed_tasks:
            return {
                'avg_estimated_vs_actual': 0,
                'estimation_accuracy': 0,
                'overestimated_tasks': 0,
                'underestimated_tasks': 0,
                'efficiency_score': 0
            }

        # Compare estimated vs actual time
        comparisons = []
        for task in completed_tasks:
            estimated = task.get('estimated_time', 0) * 60  # Convert to minutes
            actual = task.get('time_taken', 0)

            if estimated > 0 and actual > 0:
                ratio = actual / estimated
                comparisons.append({
                    'task_id': task.get('id'),
                    'estimated': estimated,
                    'actual': actual,
                    'ratio': ratio,
                    'overestimated': ratio < 0.8,
                    'underestimated': ratio > 1.2
                })

        if not comparisons:
            return {
                'avg_estimated_vs_actual': 0,
                'estimation_accuracy': 0,
                'overestimated_tasks': 0,
                'underestimated_tasks': 0,
                'efficiency_score': 0
            }

        avg_ratio = sum(c['ratio'] for c in comparisons) / len(comparisons)
        overestimated = sum(1 for c in comparisons if c['overestimated'])
        underestimated = sum(1 for c in comparisons if c['underestimated'])

        # Accuracy (how close estimates are to actuals)
        accuracy = 100 - (abs(1 - avg_ratio) * 100)
        accuracy = max(0, min(100, accuracy))

        # Efficiency score (completing faster than estimated is good)
        efficiency_score = 100 if avg_ratio < 1 else (100 / avg_ratio)

        return {
            'avg_estimated_vs_actual': avg_ratio,
            'estimation_accuracy': accuracy,
            'overestimated_tasks': overestimated,
            'underestimated_tasks': underestimated,
            'efficiency_score': efficiency_score,
            'tasks_analyzed': len(comparisons)
        }

    def get_comprehensive_report(self, tasks: List[Dict[str, Any]],
                                mood_history: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate comprehensive productivity report.

        Args:
            tasks: List of all tasks
            mood_history: List of mood records

        Returns:
            Complete productivity report
        """
        # Calculate all metrics
        daily_metrics = self.calculate_daily_metrics(tasks)
        weekly_metrics = self.calculate_weekly_metrics(tasks)
        focus_metrics = self.calculate_focus_metrics(tasks, mood_history)
        efficiency_metrics = self.calculate_efficiency_metrics(tasks)

        # Overall summary
        total_tasks = len(tasks)
        completed_tasks = len([t for t in tasks if t.get('status') == 'completed'])
        overall_completion_rate = (completed_tasks / total_tasks) if total_tasks > 0 else 0

        return {
            'summary': {
                'total_tasks': total_tasks,
                'completed_tasks': completed_tasks,
                'overall_completion_rate': overall_completion_rate,
                'report_generated_at': datetime.now(timezone.utc).isoformat()
            },
            'today': daily_metrics,
            'this_week': weekly_metrics,
            'focus': focus_metrics,
            'efficiency': efficiency_metrics
        }

    # Helper methods

    def _filter_tasks_by_date(self, tasks: List[Dict[str, Any]],
                             start_date: datetime,
                             end_date: datetime) -> List[Dict[str, Any]]:
        """Filter tasks within date range."""
        filtered = []
        for task in tasks:
            created_at = task.get('created_at')
            if created_at:
                if isinstance(created_at, str):
                    try:
                        created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    except Exception:
                        continue

                if start_date.date() <= created_at.date() <= end_date.date():
                    filtered.append(task)

        return filtered

    def _calculate_productivity_score(self, completion_rate: float,
                                     completed_tasks: int,
                                     high_priority_completed: int,
                                     avg_time: float) -> float:
        """Calculate overall productivity score (0-100)."""
        # Completion rate (40%)
        completion_score = completion_rate * 40

        # Task volume (30%)
        volume_score = min(30, completed_tasks * 3)

        # High priority focus (20%)
        priority_score = min(20, high_priority_completed * 5)

        # Time efficiency (10%)
        # Lower average time is better (assuming quality maintained)
        time_score = 10 if avg_time < 60 else (10 * (60 / max(avg_time, 1)))

        total_score = completion_score + volume_score + priority_score + time_score
        return round(min(100, total_score), 2)

    def _calculate_focus_score(self, deep_work_hours: float,
                              interruptions: int,
                              focused_sessions: int) -> float:
        """Calculate focus score (0-100)."""
        # Deep work time (50%)
        deep_work_score = min(50, deep_work_hours * 10)

        # Low interruptions (30%)
        interruption_score = max(0, 30 - (interruptions * 2))

        # Focused sessions (20%)
        focus_session_score = min(20, focused_sessions * 4)

        total_score = deep_work_score + interruption_score + focus_session_score
        return round(min(100, total_score), 2)
