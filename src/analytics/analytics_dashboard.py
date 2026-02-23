"""
Analytics Dashboard
Integrates all analytics components into a comprehensive dashboard
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import logging

from .productivity_metrics import ProductivityMetrics
from .pattern_recognition import PatternRecognition
from .predictive_insights import PredictiveInsights
from .anomaly_detection import AnomalyDetection

logger = logging.getLogger(__name__)

class AnalyticsDashboard:
    """
    Comprehensive analytics dashboard integrating all analytics components.

    Provides:
    - Productivity metrics
    - Pattern recognition
    - Predictive insights
    - Anomaly detection
    - Comprehensive reports
    """

    def __init__(self, anomaly_sensitivity: float = 0.7):
        """
        Initialize analytics dashboard.

        Args:
            anomaly_sensitivity: Sensitivity for anomaly detection (0-1)
        """
        self.name = "AnalyticsDashboard"

        # Initialize all analytics components
        self.productivity_metrics = ProductivityMetrics()
        self.pattern_recognition = PatternRecognition()
        self.predictive_insights = PredictiveInsights()
        self.anomaly_detection = AnomalyDetection(sensitivity=anomaly_sensitivity)

    def get_dashboard_data(self, tasks: List[Dict[str, Any]],
                          mood_history: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Get complete dashboard data with all analytics.

        Args:
            tasks: List of all tasks
            mood_history: List of mood records

        Returns:
            Complete dashboard data
        """
        mood_history = mood_history or []

        # Get productivity metrics
        productivity_report = self.productivity_metrics.get_comprehensive_report(
            tasks, mood_history
        )

        # Get pattern analysis
        pattern_report = self.pattern_recognition.get_pattern_report(
            tasks, mood_history
        )

        # Get predictive insights
        # Prepare historical data from patterns
        historical_data = {
            'avg_tasks_per_day': pattern_report['completion_patterns']['avg_tasks_per_day'],
            'avg_completion_rate': productivity_report['summary']['overall_completion_rate'],
            'avg_productivity_score': productivity_report['today']['productivity_score'],
            'productive_hours': pattern_report['productive_hours'],
            'patterns': pattern_report['productive_hours'],
            'current_pending_tasks': len([t for t in tasks if t.get('status') == 'pending']),
            'recent_weeks': []  # Could be populated from historical data
        }

        # Get burnout history (simplified from mood data)
        burnout_history = self._extract_burnout_history(mood_history)

        predictive_report = self.predictive_insights.generate_insights_report(
            tasks, historical_data, burnout_history
        )

        # Get anomaly detection
        daily_metrics = productivity_report['this_week']['daily_breakdown']
        anomaly_report = self.anomaly_detection.get_anomaly_report(
            tasks, mood_history, daily_metrics
        )

        # Generate executive summary
        executive_summary = self._generate_executive_summary(
            productivity_report,
            pattern_report,
            predictive_report,
            anomaly_report
        )

        return {
            'executive_summary': executive_summary,
            'productivity': productivity_report,
            'patterns': pattern_report,
            'predictions': predictive_report,
            'anomalies': anomaly_report,
            'generated_at': datetime.now(timezone.utc).isoformat()
        }

    def get_quick_insights(self, tasks: List[Dict[str, Any]],
                          mood_history: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Get quick insights summary (faster, less detailed).

        Args:
            tasks: List of all tasks
            mood_history: List of mood records

        Returns:
            Quick insights summary
        """
        mood_history = mood_history or []

        # Calculate key metrics
        total_tasks = len(tasks)
        completed_tasks = len([t for t in tasks if t.get('status') == 'completed'])
        pending_tasks = len([t for t in tasks if t.get('status') == 'pending'])
        completion_rate = (completed_tasks / total_tasks) if total_tasks > 0 else 0

        # Today's productivity
        daily_metrics = self.productivity_metrics.calculate_daily_metrics(tasks)

        # Best time of day
        productive_hours = self.pattern_recognition.find_productive_hours(tasks)
        best_time = productive_hours.get('best_time_of_day', 'Unknown')

        # Anomaly check (quick)
        recent_mood = mood_history[-5:] if len(mood_history) >= 5 else mood_history
        mood_trend = self._quick_mood_check(recent_mood)

        # Quick recommendations
        recommendations = []
        if completion_rate < 0.5:
            recommendations.append("⚠️ Low completion rate. Focus on fewer, high-priority tasks.")
        if best_time != 'Unknown':
            recommendations.append(f"💡 Schedule important work during your {best_time} peak.")
        if mood_trend == 'declining':
            recommendations.append("😟 Mood trending down. Consider taking a break.")
        if pending_tasks > 15:
            recommendations.append("📋 High pending task count. Review and prioritize.")

        return {
            'summary': {
                'total_tasks': total_tasks,
                'completed': completed_tasks,
                'pending': pending_tasks,
                'completion_rate': round(completion_rate * 100, 1),
                'today_productivity_score': daily_metrics['productivity_score']
            },
            'insights': {
                'best_time_of_day': best_time,
                'mood_trend': mood_trend,
                'recommendations': recommendations
            },
            'generated_at': datetime.now(timezone.utc).isoformat()
        }

    def get_weekly_summary(self, tasks: List[Dict[str, Any]],
                          mood_history: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Get weekly summary report.

        Args:
            tasks: List of all tasks
            mood_history: List of mood records

        Returns:
            Weekly summary
        """
        mood_history = mood_history or []

        # Weekly metrics
        weekly_metrics = self.productivity_metrics.calculate_weekly_metrics(tasks)

        # Weekly patterns
        weekly_patterns = self.pattern_recognition.find_weekly_patterns(tasks)

        # Predictions for next week
        # Calculate average tasks per day from daily breakdown
        if weekly_patterns['daily_breakdown']:
            total_tasks = sum(day_stats['total_tasks'] for day_stats in weekly_patterns['daily_breakdown'].values())
            num_days = len(weekly_patterns['daily_breakdown'])
            avg_tasks = total_tasks / num_days if num_days > 0 else 5
        else:
            avg_tasks = 5

        historical_data = {
            'avg_tasks_per_day': avg_tasks,
            'avg_completion_rate': weekly_metrics['avg_completion_rate'],
            'avg_productivity_score': weekly_metrics['avg_productivity_score'],
            'recent_weeks': [{'productivity_score': weekly_metrics['avg_productivity_score']}]
        }

        weekly_forecast = self.predictive_insights.forecast_weekly_productivity(historical_data)

        # Key achievements
        achievements = []
        if weekly_metrics['avg_productivity_score'] >= 75:
            achievements.append(f"🏆 Excellent week! Productivity score: {weekly_metrics['avg_productivity_score']:.0f}/100")
        if weekly_metrics['avg_completion_rate'] >= 0.8:
            achievements.append(f"✅ High completion rate: {weekly_metrics['avg_completion_rate']*100:.0f}%")
        if weekly_patterns['best_day']:
            achievements.append(f"🌟 Best day: {weekly_patterns['best_day']}")

        # Areas for improvement
        improvements = []
        if weekly_metrics['avg_completion_rate'] < 0.6:
            improvements.append("📊 Completion rate below 60%. Focus on finishing started tasks.")
        if weekly_patterns['worst_day'] and weekly_patterns['works_on_weekends']:
            improvements.append("⚖️ Working on weekends. Try to protect rest time.")

        return {
            'week_period': f"{weekly_metrics['week_start']} to {weekly_metrics['week_end']}",
            'metrics': {
                'total_completed': weekly_metrics['total_completed'],
                'avg_productivity_score': weekly_metrics['avg_productivity_score'],
                'avg_completion_rate': round(weekly_metrics['avg_completion_rate'] * 100, 1),
                'working_days': weekly_metrics['working_days'],
                'most_productive_day': weekly_metrics['most_productive_day']
            },
            'next_week_forecast': weekly_forecast,
            'achievements': achievements,
            'areas_for_improvement': improvements,
            'generated_at': datetime.now(timezone.utc).isoformat()
        }

    def get_burnout_assessment(self, tasks: List[Dict[str, Any]],
                               mood_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Get comprehensive burnout risk assessment.

        Args:
            tasks: List of all tasks
            mood_history: List of mood records

        Returns:
            Burnout assessment report
        """
        # Extract burnout indicators
        burnout_history = self._extract_burnout_history(mood_history)

        # Get burnout trend prediction
        burnout_prediction = self.predictive_insights.predict_burnout_trend(burnout_history)

        # Anomaly detection
        daily_metrics = self.productivity_metrics.calculate_weekly_metrics(tasks)['daily_breakdown']
        unusual_hours = self.anomaly_detection.detect_unusual_work_hours(tasks)
        mood_deterioration = self.anomaly_detection.detect_mood_deterioration(mood_history)
        extended_sessions = self.anomaly_detection.detect_extended_work_sessions(tasks)

        # Calculate overall burnout risk
        risk_factors = []
        risk_score = 0

        if burnout_prediction['current_risk'] >= 0.6:
            risk_factors.append("High baseline burnout risk")
            risk_score += 25

        if burnout_prediction['trend'] == 'increasing':
            risk_factors.append("Burnout risk trending upward")
            risk_score += 20

        if unusual_hours['is_anomaly']:
            risk_factors.append("Unusual work hours detected")
            risk_score += 15

        if mood_deterioration['is_anomaly']:
            risk_factors.append("Mood deterioration detected")
            risk_score += 25

        if extended_sessions['is_anomaly']:
            risk_factors.append("Extended work sessions without breaks")
            risk_score += 15

        # Determine risk level
        if risk_score >= 60:
            risk_level = 'critical'
            risk_message = '🚨 CRITICAL: High burnout risk. Take immediate action!'
        elif risk_score >= 40:
            risk_level = 'high'
            risk_message = '⚠️ HIGH: Elevated burnout risk. Make changes soon.'
        elif risk_score >= 20:
            risk_level = 'moderate'
            risk_message = '⚡ MODERATE: Some burnout indicators. Monitor closely.'
        else:
            risk_level = 'low'
            risk_message = '✅ LOW: Burnout risk is manageable.'

        # Generate recommendations
        recommendations = []
        if risk_score >= 40:
            recommendations.append("🛑 Take time off if possible - burnout prevention is critical")
        if unusual_hours['late_night_count'] > 5:
            recommendations.append("🌙 Stop working late nights - set strict end times")
        if extended_sessions['count'] > 0:
            recommendations.append("⏸️ Take regular breaks every 60-90 minutes")
        if mood_deterioration['is_anomaly']:
            recommendations.append("💚 Prioritize self-care and mental health activities")
        if risk_level == 'low':
            recommendations.append("✅ Continue current work-life balance practices")

        return {
            'risk_level': risk_level,
            'risk_score': risk_score,
            'risk_message': risk_message,
            'risk_factors': risk_factors,
            'current_burnout_risk': burnout_prediction['current_risk'],
            'predicted_risk_7_days': burnout_prediction['predicted_risk_7_days'],
            'trend': burnout_prediction['trend'],
            'recommendations': recommendations,
            'detailed_analysis': {
                'burnout_trend': burnout_prediction,
                'unusual_work_hours': unusual_hours,
                'mood_analysis': mood_deterioration,
                'extended_sessions': extended_sessions
            },
            'generated_at': datetime.now(timezone.utc).isoformat()
        }

    # Helper methods

    def _extract_burnout_history(self, mood_history: List[Dict[str, Any]]) -> List[float]:
        """Extract burnout scores from mood history."""
        burnout_scores = []

        for record in mood_history:
            # Calculate burnout score from mood and energy
            mood_score = record.get('mood_score', 5)
            energy = record.get('energy_level', 5)

            # Burnout is high when mood and energy are low
            # Invert and normalize to 0-1 scale
            burnout_score = (10 - mood_score + 10 - energy) / 20
            burnout_scores.append(burnout_score)

        return burnout_scores

    def _quick_mood_check(self, recent_mood: List[Dict[str, Any]]) -> str:
        """Quick mood trend check."""
        if len(recent_mood) < 2:
            return 'unknown'

        mood_scores = []
        for record in recent_mood:
            mood_score = record.get('mood_score')
            if mood_score is None:
                mood_label = record.get('mood_label', '').lower()
                mood_score = self._mood_label_to_score(mood_label)
            mood_scores.append(mood_score)

        first_avg = sum(mood_scores[:2]) / 2
        last_avg = sum(mood_scores[-2:]) / 2

        if last_avg < first_avg - 1:
            return 'declining'
        elif last_avg > first_avg + 1:
            return 'improving'
        else:
            return 'stable'

    def _mood_label_to_score(self, mood_label: str) -> int:
        """Convert mood label to numeric score."""
        mood_mapping = {
            'terrible': 1, 'awful': 2, 'bad': 3, 'stressed': 3,
            'anxious': 4, 'overwhelmed': 3, 'sad': 3,
            'neutral': 5, 'okay': 5, 'fine': 6,
            'good': 7, 'happy': 8, 'great': 8,
            'motivated': 9, 'excited': 9, 'excellent': 10
        }
        return mood_mapping.get(mood_label.lower(), 5)

    def _generate_executive_summary(self, productivity_report: Dict,
                                   pattern_report: Dict,
                                   predictive_report: Dict,
                                   anomaly_report: Dict) -> Dict[str, Any]:
        """Generate executive summary from all reports."""
        # Key metrics
        today_score = productivity_report['today']['productivity_score']
        completion_rate = productivity_report['summary']['overall_completion_rate']
        best_time = pattern_report['productive_hours']['best_time_of_day']

        # Predictions
        weekly_outlook = predictive_report['weekly_productivity_forecast']['outlook']
        burnout_risk = predictive_report['burnout_risk_trend']['current_risk']

        # Anomalies
        anomaly_count = anomaly_report['anomaly_count']
        overall_status = anomaly_report['overall_status']

        # Overall health score (0-100)
        health_score = (
            today_score * 0.3 +
            completion_rate * 100 * 0.2 +
            (100 - burnout_risk * 100) * 0.3 +
            (100 if overall_status == 'healthy' else 50 if overall_status == 'warning' else 0) * 0.2
        )

        # Status determination
        if health_score >= 80:
            status = 'excellent'
            status_icon = '🟢'
            status_message = 'Everything is going great!'
        elif health_score >= 60:
            status = 'good'
            status_icon = '🟡'
            status_message = 'Doing well with some areas to watch.'
        elif health_score >= 40:
            status = 'concerning'
            status_icon = '🟠'
            status_message = 'Some issues need attention.'
        else:
            status = 'critical'
            status_icon = '🔴'
            status_message = 'Multiple concerns require immediate action.'

        # Top insights
        top_insights = []
        top_insights.extend(predictive_report['summary_insights'])
        top_insights.extend(pattern_report['actionable_insights'])

        # Limit to top 5
        top_insights = top_insights[:5]

        return {
            'status': status,
            'status_icon': status_icon,
            'status_message': status_message,
            'health_score': round(health_score, 1),
            'key_metrics': {
                'today_productivity': today_score,
                'completion_rate': round(completion_rate * 100, 1),
                'best_time_of_day': best_time,
                'weekly_outlook': weekly_outlook,
                'burnout_risk': round(burnout_risk * 100, 1),
                'anomalies_detected': anomaly_count
            },
            'top_insights': top_insights,
            'priority_actions': anomaly_report.get('priority_recommendations', [])
        }
