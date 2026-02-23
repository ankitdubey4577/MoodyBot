"""
Anomaly Detection System
Detects unusual patterns and behaviors in productivity and mood
"""
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime, timedelta, timezone
from collections import defaultdict
import logging
import statistics

logger = logging.getLogger(__name__)

class AnomalyDetection:
    """
    Detects anomalies in user behavior and productivity patterns.

    Detects:
    - Unusual work hours
    - Productivity drops
    - Mood deterioration
    - Workload spikes
    - Extended work sessions
    - Pattern breaks
    """

    def __init__(self, sensitivity: float = 0.7):
        """
        Initialize anomaly detector.

        Args:
            sensitivity: Detection sensitivity (0-1). Higher = more sensitive
        """
        self.name = "AnomalyDetection"
        self.sensitivity = sensitivity

    def detect_unusual_work_hours(self, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Detect unusual work hours (late nights, very early mornings, weekends).

        Args:
            tasks: List of tasks with timestamps

        Returns:
            Dictionary with unusual work hour detections
        """
        unusual_sessions = []
        late_night_count = 0
        early_morning_count = 0
        weekend_count = 0

        for task in tasks:
            created_at = task.get('created_at')
            if not created_at:
                continue

            if isinstance(created_at, str):
                try:
                    created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                except Exception:
                    continue

            hour = created_at.hour
            day_of_week = created_at.weekday()  # 0=Monday, 6=Sunday

            # Late night work (10 PM - 2 AM)
            if 22 <= hour or hour <= 2:
                late_night_count += 1
                unusual_sessions.append({
                    'task_id': task.get('id'),
                    'timestamp': created_at.isoformat(),
                    'type': 'late_night',
                    'hour': hour,
                    'severity': 'high' if hour >= 23 or hour <= 1 else 'medium'
                })

            # Very early morning (3 AM - 5 AM)
            elif 3 <= hour <= 5:
                early_morning_count += 1
                unusual_sessions.append({
                    'task_id': task.get('id'),
                    'timestamp': created_at.isoformat(),
                    'type': 'early_morning',
                    'hour': hour,
                    'severity': 'high'
                })

            # Weekend work (Saturday, Sunday)
            if day_of_week >= 5:
                weekend_count += 1
                # Only add if not already added for time
                if not any(s['task_id'] == task.get('id') for s in unusual_sessions):
                    unusual_sessions.append({
                        'task_id': task.get('id'),
                        'timestamp': created_at.isoformat(),
                        'type': 'weekend',
                        'day': 'Saturday' if day_of_week == 5 else 'Sunday',
                        'severity': 'medium'
                    })

        # Determine if this is anomalous
        total_tasks = len([t for t in tasks if t.get('created_at')])
        unusual_percentage = (len(unusual_sessions) / total_tasks * 100) if total_tasks > 0 else 0

        is_anomaly = unusual_percentage > (30 * self.sensitivity)

        # Generate alert
        alerts = []
        if late_night_count > 5:
            alerts.append(f"⚠️ {late_night_count} tasks completed during late night hours (10 PM - 2 AM)")
        if early_morning_count > 3:
            alerts.append(f"⚠️ {early_morning_count} tasks completed during very early morning (3 AM - 5 AM)")
        if weekend_count > 10:
            alerts.append(f"⚠️ {weekend_count} tasks completed during weekends - work-life balance concern")

        return {
            'is_anomaly': is_anomaly,
            'unusual_sessions': unusual_sessions,
            'late_night_count': late_night_count,
            'early_morning_count': early_morning_count,
            'weekend_count': weekend_count,
            'unusual_percentage': round(unusual_percentage, 2),
            'alerts': alerts,
            'recommendation': self._get_work_hours_recommendation(
                late_night_count, early_morning_count, weekend_count
            )
        }

    def detect_productivity_drops(self, daily_metrics: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Detect sudden drops in productivity.

        Args:
            daily_metrics: List of daily productivity metrics

        Returns:
            Dictionary with productivity drop detections
        """
        if len(daily_metrics) < 7:
            return {
                'is_anomaly': False,
                'drops_detected': [],
                'message': 'Insufficient data for productivity drop detection (need 7+ days)'
            }

        # Extract productivity scores
        scores = [d.get('productivity_score', 0) for d in daily_metrics]

        if not scores:
            return {
                'is_anomaly': False,
                'drops_detected': [],
                'message': 'No productivity scores available'
            }

        # Calculate baseline (average of recent period)
        baseline = statistics.mean(scores[-14:]) if len(scores) >= 14 else statistics.mean(scores)
        std_dev = statistics.stdev(scores) if len(scores) >= 2 else 0

        # Detect drops (more than 1.5 standard deviations below baseline)
        threshold = baseline - (1.5 * std_dev * self.sensitivity)

        drops_detected = []
        consecutive_low_days = 0

        for i, metric in enumerate(daily_metrics[-7:]):  # Check last 7 days
            score = metric.get('productivity_score', 0)
            date = metric.get('date')

            if score < threshold:
                drop_magnitude = ((baseline - score) / baseline * 100) if baseline > 0 else 0
                severity = 'critical' if drop_magnitude > 50 else 'high' if drop_magnitude > 30 else 'medium'

                drops_detected.append({
                    'date': date,
                    'score': score,
                    'baseline': baseline,
                    'drop_percentage': round(drop_magnitude, 2),
                    'severity': severity
                })
                consecutive_low_days += 1
            else:
                consecutive_low_days = 0

        is_anomaly = len(drops_detected) >= 2 or consecutive_low_days >= 3

        # Generate alerts
        alerts = []
        if consecutive_low_days >= 3:
            alerts.append(f"⚠️ CRITICAL: {consecutive_low_days} consecutive days of low productivity")
        elif drops_detected:
            avg_drop = sum(d['drop_percentage'] for d in drops_detected) / len(drops_detected)
            alerts.append(f"⚠️ Productivity dropped by {avg_drop:.1f}% on {len(drops_detected)} days")

        return {
            'is_anomaly': is_anomaly,
            'drops_detected': drops_detected,
            'baseline_productivity': round(baseline, 2),
            'threshold': round(threshold, 2),
            'consecutive_low_days': consecutive_low_days,
            'alerts': alerts,
            'recommendation': self._get_productivity_drop_recommendation(
                len(drops_detected), consecutive_low_days
            )
        }

    def detect_mood_deterioration(self, mood_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Detect declining mood trends.

        Args:
            mood_history: List of mood records with scores

        Returns:
            Dictionary with mood deterioration detections
        """
        if len(mood_history) < 5:
            return {
                'is_anomaly': False,
                'trend': 'unknown',
                'message': 'Insufficient data for mood analysis (need 5+ records)'
            }

        # Extract mood scores (assuming 1-10 scale)
        mood_scores = []
        energy_scores = []

        for record in mood_history:
            # Map mood labels to scores if needed
            mood_score = record.get('mood_score')
            if mood_score is None:
                mood_label = record.get('mood_label', '').lower()
                mood_score = self._mood_label_to_score(mood_label)

            mood_scores.append(mood_score)
            energy_scores.append(record.get('energy_level', 5))

        # Calculate trends
        recent_moods = mood_scores[-7:]
        recent_energy = energy_scores[-7:]

        if len(mood_scores) >= 14:
            older_moods = mood_scores[-14:-7]
            mood_change = statistics.mean(recent_moods) - statistics.mean(older_moods)
        else:
            mood_change = recent_moods[-1] - recent_moods[0] if len(recent_moods) >= 2 else 0

        if len(energy_scores) >= 14:
            older_energy = energy_scores[-14:-7]
            energy_change = statistics.mean(recent_energy) - statistics.mean(older_energy)
        else:
            energy_change = recent_energy[-1] - recent_energy[0] if len(recent_energy) >= 2 else 0

        # Detect deterioration
        is_mood_declining = mood_change < -(1.5 * self.sensitivity)
        is_energy_declining = energy_change < -(1.5 * self.sensitivity)

        is_anomaly = is_mood_declining or is_energy_declining

        # Count concerning days
        concerning_days = sum(
            1 for m, e in zip(recent_moods, recent_energy)
            if m <= 4 or e <= 3
        )

        # Determine trend
        if mood_change < -1:
            trend = 'declining'
        elif mood_change > 1:
            trend = 'improving'
        else:
            trend = 'stable'

        # Generate alerts
        alerts = []
        if is_mood_declining:
            alerts.append(f"⚠️ Mood has declined by {abs(mood_change):.1f} points recently")
        if is_energy_declining:
            alerts.append(f"⚠️ Energy levels have dropped by {abs(energy_change):.1f} points")
        if concerning_days >= 4:
            alerts.append(f"⚠️ {concerning_days} days with low mood or energy in the last week")

        return {
            'is_anomaly': is_anomaly,
            'trend': trend,
            'mood_change': round(mood_change, 2),
            'energy_change': round(energy_change, 2),
            'recent_avg_mood': round(statistics.mean(recent_moods), 2),
            'recent_avg_energy': round(statistics.mean(recent_energy), 2),
            'concerning_days': concerning_days,
            'alerts': alerts,
            'recommendation': self._get_mood_recommendation(
                trend, mood_change, energy_change, concerning_days
            )
        }

    def detect_workload_spikes(self, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Detect sudden increases in workload.

        Args:
            tasks: List of all tasks

        Returns:
            Dictionary with workload spike detections
        """
        # Group tasks by date
        tasks_by_date = defaultdict(list)

        for task in tasks:
            created_at = task.get('created_at')
            if not created_at:
                continue

            if isinstance(created_at, str):
                try:
                    created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                except Exception:
                    continue

            date_key = created_at.date().isoformat()
            tasks_by_date[date_key].append(task)

        if len(tasks_by_date) < 7:
            return {
                'is_anomaly': False,
                'spikes_detected': [],
                'message': 'Insufficient data for workload spike detection (need 7+ days)'
            }

        # Calculate daily task counts
        daily_counts = [len(tasks) for tasks in tasks_by_date.values()]

        # Calculate baseline
        baseline = statistics.mean(daily_counts)
        std_dev = statistics.stdev(daily_counts) if len(daily_counts) >= 2 else 0

        # Detect spikes (more than 2 standard deviations above baseline)
        threshold = baseline + (2 * std_dev * self.sensitivity)

        spikes_detected = []
        recent_dates = sorted(tasks_by_date.keys())[-7:]  # Last 7 days

        for date in recent_dates:
            count = len(tasks_by_date[date])

            if count > threshold:
                spike_magnitude = ((count - baseline) / baseline * 100) if baseline > 0 else 0
                severity = 'critical' if spike_magnitude > 100 else 'high' if spike_magnitude > 50 else 'medium'

                # Calculate high priority task count
                high_priority = sum(
                    1 for t in tasks_by_date[date]
                    if t.get('priority', 0) >= 7
                )

                spikes_detected.append({
                    'date': date,
                    'task_count': count,
                    'baseline': baseline,
                    'spike_percentage': round(spike_magnitude, 2),
                    'high_priority_tasks': high_priority,
                    'severity': severity
                })

        is_anomaly = len(spikes_detected) >= 2

        # Generate alerts
        alerts = []
        if spikes_detected:
            max_spike = max(spikes_detected, key=lambda x: x['spike_percentage'])
            alerts.append(
                f"⚠️ Workload spike detected: {max_spike['task_count']} tasks "
                f"({max_spike['spike_percentage']:.0f}% above normal) on {max_spike['date']}"
            )

        return {
            'is_anomaly': is_anomaly,
            'spikes_detected': spikes_detected,
            'baseline_tasks_per_day': round(baseline, 2),
            'threshold': round(threshold, 2),
            'alerts': alerts,
            'recommendation': self._get_workload_spike_recommendation(spikes_detected)
        }

    def detect_extended_work_sessions(self, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Detect unusually long work sessions without breaks.

        Args:
            tasks: List of tasks with time tracking

        Returns:
            Dictionary with extended session detections
        """
        extended_sessions = []

        # Look for tasks with very long durations
        for task in tasks:
            time_taken = task.get('time_taken', 0)

            # Flag sessions over 4 hours
            if time_taken >= 240:  # 4+ hours
                severity = 'critical' if time_taken >= 360 else 'high' if time_taken >= 300 else 'medium'

                extended_sessions.append({
                    'task_id': task.get('id'),
                    'title': task.get('title', 'Unknown'),
                    'duration_hours': round(time_taken / 60, 2),
                    'severity': severity
                })

        is_anomaly = len(extended_sessions) >= 3

        # Generate alerts
        alerts = []
        if extended_sessions:
            total_extended_hours = sum(s['duration_hours'] for s in extended_sessions)
            alerts.append(
                f"⚠️ {len(extended_sessions)} extended work sessions detected "
                f"({total_extended_hours:.1f} hours without breaks)"
            )

        return {
            'is_anomaly': is_anomaly,
            'extended_sessions': extended_sessions,
            'count': len(extended_sessions),
            'alerts': alerts,
            'recommendation': 'Take regular breaks every 60-90 minutes to maintain focus and prevent burnout.'
        }

    def get_anomaly_report(self, tasks: List[Dict[str, Any]],
                          mood_history: List[Dict[str, Any]],
                          daily_metrics: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate comprehensive anomaly detection report.

        Args:
            tasks: List of all tasks
            mood_history: List of mood records
            daily_metrics: List of daily productivity metrics

        Returns:
            Complete anomaly detection report
        """
        # Run all detections
        unusual_hours = self.detect_unusual_work_hours(tasks)
        productivity_drops = self.detect_productivity_drops(daily_metrics)
        mood_deterioration = self.detect_mood_deterioration(mood_history)
        workload_spikes = self.detect_workload_spikes(tasks)
        extended_sessions = self.detect_extended_work_sessions(tasks)

        # Count total anomalies
        anomaly_count = sum([
            unusual_hours['is_anomaly'],
            productivity_drops['is_anomaly'],
            mood_deterioration['is_anomaly'],
            workload_spikes['is_anomaly'],
            extended_sessions['is_anomaly']
        ])

        # Collect all alerts
        all_alerts = []
        all_alerts.extend(unusual_hours.get('alerts', []))
        all_alerts.extend(productivity_drops.get('alerts', []))
        all_alerts.extend(mood_deterioration.get('alerts', []))
        all_alerts.extend(workload_spikes.get('alerts', []))
        all_alerts.extend(extended_sessions.get('alerts', []))

        # Determine overall status
        if anomaly_count == 0:
            overall_status = 'healthy'
            status_message = '✅ No significant anomalies detected. Everything looks good!'
        elif anomaly_count <= 2:
            overall_status = 'warning'
            status_message = '⚠️ Some concerning patterns detected. Monitor closely.'
        else:
            overall_status = 'critical'
            status_message = '🚨 Multiple anomalies detected. Take action to address work patterns.'

        return {
            'overall_status': overall_status,
            'status_message': status_message,
            'anomaly_count': anomaly_count,
            'all_alerts': all_alerts,
            'detections': {
                'unusual_work_hours': unusual_hours,
                'productivity_drops': productivity_drops,
                'mood_deterioration': mood_deterioration,
                'workload_spikes': workload_spikes,
                'extended_sessions': extended_sessions
            },
            'priority_recommendations': self._generate_priority_recommendations(
                unusual_hours, productivity_drops, mood_deterioration,
                workload_spikes, extended_sessions
            ),
            'report_generated_at': datetime.now(timezone.utc).isoformat()
        }

    # Helper methods

    def _mood_label_to_score(self, mood_label: str) -> int:
        """Convert mood label to numeric score (1-10)."""
        mood_mapping = {
            'terrible': 1, 'awful': 2, 'bad': 3, 'stressed': 3,
            'anxious': 4, 'overwhelmed': 3, 'sad': 3,
            'neutral': 5, 'okay': 5, 'fine': 6,
            'good': 7, 'happy': 8, 'great': 8,
            'motivated': 9, 'excited': 9, 'excellent': 10
        }
        return mood_mapping.get(mood_label.lower(), 5)

    def _get_work_hours_recommendation(self, late_night: int,
                                       early_morning: int,
                                       weekend: int) -> str:
        """Get recommendation for unusual work hours."""
        if late_night > 5 or early_morning > 3:
            return "🌙 You're working very late/early. Set clear work hours boundaries to improve sleep and recovery."
        elif weekend > 10:
            return "📅 High weekend work detected. Consider protecting weekend time for rest and personal activities."
        else:
            return "⏰ Some irregular work hours detected. Try to maintain consistent work schedule."

    def _get_productivity_drop_recommendation(self, drops: int,
                                             consecutive: int) -> str:
        """Get recommendation for productivity drops."""
        if consecutive >= 3:
            return "📉 Multiple consecutive low-productivity days. Consider: reducing workload, taking a break, or addressing blockers."
        elif drops >= 2:
            return "📊 Productivity fluctuating. Review your task priorities and eliminate distractions."
        else:
            return "✅ Productivity is stable."

    def _get_mood_recommendation(self, trend: str, mood_change: float,
                                energy_change: float, concerning_days: int) -> str:
        """Get recommendation for mood deterioration."""
        if trend == 'declining' and concerning_days >= 4:
            return "😟 Mood and energy declining. Take time for self-care, reduce workload, and consider talking to someone."
        elif trend == 'declining':
            return "📉 Mood trending down. Take breaks, engage in activities you enjoy, and monitor closely."
        elif concerning_days >= 3:
            return "⚠️ Several low-energy days detected. Ensure adequate rest and consider workload adjustment."
        else:
            return "😊 Mood and energy levels are stable."

    def _get_workload_spike_recommendation(self, spikes: List[Dict]) -> str:
        """Get recommendation for workload spikes."""
        if len(spikes) >= 3:
            return "📈 Multiple workload spikes detected. Delegate tasks, extend deadlines, or request support."
        elif spikes:
            max_spike = max(spikes, key=lambda x: x['spike_percentage'])
            if max_spike['high_priority_tasks'] > 5:
                return "🎯 High-priority task overload. Focus on critical items and defer non-urgent work."
            else:
                return "📋 Workload spike detected. Prioritize ruthlessly and consider pushing back non-critical tasks."
        else:
            return "✅ Workload is manageable."

    def _generate_priority_recommendations(self, unusual_hours: Dict,
                                          productivity_drops: Dict,
                                          mood_deterioration: Dict,
                                          workload_spikes: Dict,
                                          extended_sessions: Dict) -> List[str]:
        """Generate prioritized recommendations based on all detections."""
        recommendations = []

        # Prioritize based on severity
        if mood_deterioration['is_anomaly'] and mood_deterioration.get('concerning_days', 0) >= 4:
            recommendations.append(
                "🔴 URGENT: Mood deterioration detected. Take immediate action for mental health."
            )

        if unusual_hours.get('late_night_count', 0) > 10:
            recommendations.append(
                "🔴 URGENT: Excessive late-night work. Establish work hour boundaries immediately."
            )

        if productivity_drops['is_anomaly'] and productivity_drops.get('consecutive_low_days', 0) >= 3:
            recommendations.append(
                "🟠 HIGH: Sustained productivity drop. Review workload and address blockers."
            )

        if workload_spikes['is_anomaly']:
            recommendations.append(
                "🟠 HIGH: Workload spikes detected. Delegate or defer non-critical tasks."
            )

        if extended_sessions['is_anomaly']:
            recommendations.append(
                "🟡 MEDIUM: Long work sessions without breaks. Schedule regular breaks."
            )

        if not recommendations:
            recommendations.append("✅ No urgent issues detected. Continue current practices.")

        return recommendations
