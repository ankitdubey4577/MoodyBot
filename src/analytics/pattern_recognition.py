"""
Pattern Recognition Engine
Detects user patterns and work rhythms
"""
from typing import Dict, Any, List, Tuple
from datetime import datetime, timezone
from collections import defaultdict, Counter
import logging

logger = logging.getLogger(__name__)

class PatternRecognition:
    """
    Recognizes patterns in user behavior, productivity, and mood.

    Patterns detected:
    - Most productive time of day
    - Best mood for each task type
    - Work rhythm and optimal breaks
    - Day-of-week patterns
    - Task completion patterns
    """

    def __init__(self):
        self.name = "PatternRecognition"

    def find_productive_hours(self, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Identify most productive hours of the day.

        Args:
            tasks: List of completed tasks with timestamps

        Returns:
            Dictionary with productivity by hour
        """
        hour_stats = defaultdict(lambda: {'completed': 0, 'total_time': 0, 'tasks': []})

        for task in tasks:
            if task.get('status') != 'completed':
                continue

            created_at = task.get('created_at')
            if not created_at:
                continue

            if isinstance(created_at, str):
                try:
                    created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                except Exception:
                    continue

            hour = created_at.hour
            time_taken = task.get('time_taken', 0)

            hour_stats[hour]['completed'] += 1
            hour_stats[hour]['total_time'] += time_taken
            hour_stats[hour]['tasks'].append(task)

        # Calculate productivity score per hour
        hourly_productivity = {}
        for hour, stats in hour_stats.items():
            # Productivity = tasks completed * efficiency
            productivity_score = stats['completed'] * 10

            # Bonus for completing high priority tasks
            high_priority = sum(
                1 for t in stats['tasks']
                if t.get('priority', 0) >= 7
            )
            productivity_score += high_priority * 5

            hourly_productivity[hour] = {
                'hour': hour,
                'tasks_completed': stats['completed'],
                'total_time_minutes': stats['total_time'],
                'high_priority_completed': high_priority,
                'productivity_score': productivity_score
            }

        # Find peak hours
        if hourly_productivity:
            sorted_hours = sorted(
                hourly_productivity.values(),
                key=lambda x: x['productivity_score'],
                reverse=True
            )

            peak_hours = sorted_hours[:3] if len(sorted_hours) >= 3 else sorted_hours

            # Time of day classification
            morning_hours = [h for h in range(6, 12)]
            afternoon_hours = [h for h in range(12, 18)]
            evening_hours = [h for h in range(18, 23)]

            morning_score = sum(
                hourly_productivity.get(h, {}).get('productivity_score', 0)
                for h in morning_hours
            )
            afternoon_score = sum(
                hourly_productivity.get(h, {}).get('productivity_score', 0)
                for h in afternoon_hours
            )
            evening_score = sum(
                hourly_productivity.get(h, {}).get('productivity_score', 0)
                for h in evening_hours
            )

            best_time_of_day = max(
                [('Morning', morning_score), ('Afternoon', afternoon_score), ('Evening', evening_score)],
                key=lambda x: x[1]
            )[0]

            return {
                'hourly_breakdown': hourly_productivity,
                'peak_hours': peak_hours,
                'best_time_of_day': best_time_of_day,
                'morning_score': morning_score,
                'afternoon_score': afternoon_score,
                'evening_score': evening_score
            }

        return {
            'hourly_breakdown': {},
            'peak_hours': [],
            'best_time_of_day': 'Unknown',
            'morning_score': 0,
            'afternoon_score': 0,
            'evening_score': 0
        }

    def find_mood_task_correlations(self, tasks: List[Dict[str, Any]],
                                    mood_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Find correlations between mood and task completion.

        Args:
            tasks: List of tasks
            mood_history: List of mood records

        Returns:
            Dictionary of mood-task correlations
        """
        # Group tasks by mood when completed
        mood_task_map = defaultdict(lambda: {
            'completed': 0,
            'total_time': 0,
            'high_priority': 0,
            'task_types': []
        })

        for task in tasks:
            if task.get('status') != 'completed':
                continue

            mood = task.get('mood', 'unknown')
            time_taken = task.get('time_taken', 0)
            priority = task.get('priority', 0)

            mood_task_map[mood]['completed'] += 1
            mood_task_map[mood]['total_time'] += time_taken

            if priority >= 7:
                mood_task_map[mood]['high_priority'] += 1

        # Find best mood for productivity
        best_moods = sorted(
            mood_task_map.items(),
            key=lambda x: x[1]['completed'],
            reverse=True
        )[:3]

        # Energy level analysis
        if mood_history:
            avg_energy_by_mood = defaultdict(list)
            for mood_entry in mood_history:
                mood_label = mood_entry.get('mood_label', 'unknown')
                energy = mood_entry.get('energy_level', 5)
                avg_energy_by_mood[mood_label].append(energy)

            energy_averages = {
                mood: sum(levels) / len(levels)
                for mood, levels in avg_energy_by_mood.items()
            }

            high_energy_moods = [
                mood for mood, avg in energy_averages.items()
                if avg >= 7
            ]
        else:
            energy_averages = {}
            high_energy_moods = []

        return {
            'mood_productivity': dict(mood_task_map),
            'best_moods_for_productivity': [m[0] for m in best_moods],
            'energy_averages': energy_averages,
            'high_energy_moods': high_energy_moods,
            'insights': self._generate_mood_insights(best_moods, high_energy_moods)
        }

    def find_weekly_patterns(self, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Identify day-of-week patterns.

        Args:
            tasks: List of tasks

        Returns:
            Dictionary of weekly patterns
        """
        day_stats = defaultdict(lambda: {
            'completed': 0,
            'total_tasks': 0,
            'total_time': 0,
            'high_priority': 0
        })

        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

        for task in tasks:
            created_at = task.get('created_at')
            if not created_at:
                continue

            if isinstance(created_at, str):
                try:
                    created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                except Exception:
                    continue

            day_of_week = created_at.weekday()  # 0=Monday, 6=Sunday
            day_name = day_names[day_of_week]

            day_stats[day_name]['total_tasks'] += 1

            if task.get('status') == 'completed':
                day_stats[day_name]['completed'] += 1
                day_stats[day_name]['total_time'] += task.get('time_taken', 0)

                if task.get('priority', 0) >= 7:
                    day_stats[day_name]['high_priority'] += 1

        # Calculate completion rates
        for day, stats in day_stats.items():
            if stats['total_tasks'] > 0:
                stats['completion_rate'] = stats['completed'] / stats['total_tasks']
            else:
                stats['completion_rate'] = 0

        # Find best and worst days
        if day_stats:
            best_day = max(day_stats.items(), key=lambda x: x[1]['completion_rate'])[0]
            worst_day = min(day_stats.items(), key=lambda x: x[1]['completion_rate'])[0]

            # Weekday vs weekend
            weekday_stats = {
                day: stats for day, stats in day_stats.items()
                if day in day_names[:5]
            }
            weekend_stats = {
                day: stats for day, stats in day_stats.items()
                if day in day_names[5:]
            }

            weekday_avg_completion = (
                sum(s['completion_rate'] for s in weekday_stats.values()) / len(weekday_stats)
                if weekday_stats else 0
            )
            weekend_avg_completion = (
                sum(s['completion_rate'] for s in weekend_stats.values()) / len(weekend_stats)
                if weekend_stats else 0
            )
        else:
            best_day = 'Unknown'
            worst_day = 'Unknown'
            weekday_avg_completion = 0
            weekend_avg_completion = 0

        return {
            'daily_breakdown': dict(day_stats),
            'best_day': best_day,
            'worst_day': worst_day,
            'weekday_avg_completion': weekday_avg_completion,
            'weekend_avg_completion': weekend_avg_completion,
            'works_on_weekends': weekend_avg_completion > 0
        }

    def find_task_completion_patterns(self, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Identify patterns in task completion behavior.

        Args:
            tasks: List of tasks

        Returns:
            Dictionary of completion patterns
        """
        completed_tasks = [t for t in tasks if t.get('status') == 'completed']

        if not completed_tasks:
            return {
                'avg_tasks_per_day': 0,
                'completion_streak': 0,
                'most_common_priority': 'medium',
                'task_type_distribution': {},
                'quick_wins': 0,
                'deep_work_tasks': 0
            }

        # Tasks per day
        dates = set()
        for task in completed_tasks:
            created_at = task.get('created_at')
            if created_at:
                if isinstance(created_at, str):
                    try:
                        created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        dates.add(created_at.date())
                    except Exception:
                        continue

        avg_tasks_per_day = len(completed_tasks) / len(dates) if dates else 0

        # Priority distribution
        priorities = [t.get('priority', 5) for t in completed_tasks]
        priority_counter = Counter(priorities)
        most_common_priority = priority_counter.most_common(1)[0][0] if priority_counter else 5

        # Task type distribution (by mode)
        modes = [t.get('mode', 'work') for t in completed_tasks]
        task_type_distribution = dict(Counter(modes))

        # Quick wins (tasks < 30 min)
        quick_wins = sum(1 for t in completed_tasks if t.get('time_taken', 0) < 30)

        # Deep work (tasks > 60 min with high priority)
        deep_work_tasks = sum(
            1 for t in completed_tasks
            if t.get('time_taken', 0) >= 60 and t.get('priority', 0) >= 7
        )

        return {
            'avg_tasks_per_day': round(avg_tasks_per_day, 2),
            'total_completed': len(completed_tasks),
            'most_common_priority': most_common_priority,
            'task_type_distribution': task_type_distribution,
            'quick_wins': quick_wins,
            'deep_work_tasks': deep_work_tasks,
            'quick_wins_percentage': (quick_wins / len(completed_tasks) * 100) if completed_tasks else 0
        }

    def get_pattern_report(self, tasks: List[Dict[str, Any]],
                          mood_history: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate comprehensive pattern recognition report.

        Args:
            tasks: List of all tasks
            mood_history: List of mood records

        Returns:
            Complete pattern analysis report
        """
        productive_hours = self.find_productive_hours(tasks)
        mood_correlations = self.find_mood_task_correlations(tasks, mood_history or [])
        weekly_patterns = self.find_weekly_patterns(tasks)
        completion_patterns = self.find_task_completion_patterns(tasks)

        # Generate actionable insights
        insights = self._generate_actionable_insights(
            productive_hours,
            mood_correlations,
            weekly_patterns,
            completion_patterns
        )

        return {
            'productive_hours': productive_hours,
            'mood_correlations': mood_correlations,
            'weekly_patterns': weekly_patterns,
            'completion_patterns': completion_patterns,
            'actionable_insights': insights,
            'report_generated_at': datetime.now(timezone.utc).isoformat()
        }

    # Helper methods

    def _generate_mood_insights(self, best_moods: List[Tuple],
                               high_energy_moods: List[str]) -> List[str]:
        """Generate insights from mood correlations."""
        insights = []

        if best_moods:
            top_mood = best_moods[0][0]
            insights.append(
                f"You're most productive when feeling '{top_mood}'. "
                f"Try to schedule important tasks during these mood states."
            )

        if high_energy_moods:
            insights.append(
                f"Your energy is highest when {', '.join(high_energy_moods[:2])}. "
                f"Perfect time for challenging tasks!"
            )

        return insights

    def _generate_actionable_insights(self, productive_hours: Dict,
                                     mood_correlations: Dict,
                                     weekly_patterns: Dict,
                                     completion_patterns: Dict) -> List[str]:
        """Generate actionable insights from all patterns."""
        insights = []

        # Time-based insights
        if productive_hours.get('best_time_of_day'):
            best_time = productive_hours['best_time_of_day']
            insights.append(
                f"📅 Schedule your most important work in the {best_time}. "
                f"That's when you're most productive!"
            )

        # Day-based insights
        if weekly_patterns.get('best_day'):
            best_day = weekly_patterns['best_day']
            insights.append(
                f"🌟 {best_day} is your most productive day. "
                f"Plan key deliverables for {best_day}s."
            )

        # Quick wins pattern
        quick_wins_pct = completion_patterns.get('quick_wins_percentage', 0)
        if quick_wins_pct > 50:
            insights.append(
                f"⚡ {quick_wins_pct:.0f}% of your completed tasks are quick wins (<30min). "
                f"You're great at knocking out small tasks!"
            )

        # Deep work pattern
        deep_work = completion_patterns.get('deep_work_tasks', 0)
        if deep_work > 0:
            insights.append(
                f"🎯 You've completed {deep_work} deep work sessions. "
                f"Keep dedicating time to high-priority, focused work."
            )

        # Weekend work
        if weekly_patterns.get('works_on_weekends'):
            insights.append(
                "⚖️ You're working on weekends. Remember to take breaks "
                "and maintain work-life balance!"
            )

        return insights
