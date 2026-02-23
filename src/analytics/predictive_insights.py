"""
Predictive Insights Generator
Generates predictions and forecasts based on historical data
"""
from typing import Dict, Any, List
from datetime import datetime, timedelta, timezone
import logging

logger = logging.getLogger(__name__)

class PredictiveInsights:
    """
    Generates predictive insights and forecasts.

    Predictions:
    - Task completion probability
    - Weekly productivity forecast
    - Burnout risk trend
    - Workload projections
    - Optimal scheduling suggestions
    """

    def __init__(self):
        self.name = "PredictiveInsights"

    def predict_task_completion_probability(self, task: Dict[str, Any],
                                           user_history: Dict[str, Any]) -> Dict[str, Any]:
        """
        Predict the probability that a task will be completed today.

        Args:
            task: Task to analyze
            user_history: User's historical performance data

        Returns:
            Dictionary with completion probability and factors
        """
        # Base probability
        probability = 0.7  # Start at 70%

        # Factor 1: Priority (higher priority = more likely to complete)
        priority = task.get('priority', 5)
        if priority >= 8:
            probability += 0.15
        elif priority >= 6:
            probability += 0.10
        elif priority <= 3:
            probability -= 0.10

        # Factor 2: Estimated time (shorter tasks = higher completion)
        estimated_time = task.get('estimated_time', 1.0)
        if estimated_time < 0.5:  # < 30 min
            probability += 0.10
        elif estimated_time > 3:  # > 3 hours
            probability -= 0.15

        # Factor 3: Time of day (based on historical patterns)
        current_hour = datetime.now(timezone.utc).hour
        productive_hours = user_history.get('productive_hours', {})
        if current_hour in productive_hours.get('peak_hours', []):
            probability += 0.10

        # Factor 4: Current workload
        current_tasks = user_history.get('current_pending_tasks', 5)
        if current_tasks > 10:
            probability -= 0.15
        elif current_tasks < 3:
            probability += 0.10

        # Factor 5: Historical completion rate
        completion_rate = user_history.get('avg_completion_rate', 0.7)
        if completion_rate > 0.8:
            probability += 0.10
        elif completion_rate < 0.5:
            probability -= 0.10

        # Clamp probability between 0 and 1
        probability = max(0, min(1, probability))

        # Determine confidence level
        if probability >= 0.8:
            confidence = 'high'
            recommendation = 'Great! This task is highly likely to be completed today.'
        elif probability >= 0.6:
            confidence = 'medium'
            recommendation = 'Good chance of completion. Stay focused!'
        else:
            confidence = 'low'
            recommendation = 'This might be challenging. Consider breaking it into smaller tasks.'

        return {
            'probability': probability,
            'confidence': confidence,
            'recommendation': recommendation,
            'factors': {
                'priority': priority,
                'estimated_time': estimated_time,
                'current_hour': current_hour,
                'workload': current_tasks,
                'completion_rate': completion_rate
            }
        }

    def forecast_weekly_productivity(self, historical_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Forecast productivity for the next week.

        Args:
            historical_data: Historical productivity metrics

        Returns:
            Dictionary with weekly forecast
        """
        # Get historical weekly averages
        avg_tasks_per_day = historical_data.get('avg_tasks_per_day', 5)
        avg_completion_rate = historical_data.get('avg_completion_rate', 0.7)
        avg_productivity_score = historical_data.get('avg_productivity_score', 70)

        # Trend analysis (simple linear trend)
        recent_weeks = historical_data.get('recent_weeks', [])
        if len(recent_weeks) >= 3:
            # Calculate trend
            recent_scores = [w.get('productivity_score', 70) for w in recent_weeks[-3:]]
            trend = (recent_scores[-1] - recent_scores[0]) / len(recent_scores)
        else:
            trend = 0

        # Forecast next week
        forecasted_productivity = avg_productivity_score + (trend * 7)
        forecasted_productivity = max(0, min(100, forecasted_productivity))

        # Forecast tasks
        forecasted_tasks_per_day = max(0, avg_tasks_per_day + (trend / 10))

        # Determine outlook
        if forecasted_productivity >= 75:
            outlook = 'excellent'
            message = 'Next week looks highly productive! Keep up the great work.'
        elif forecasted_productivity >= 60:
            outlook = 'good'
            message = 'Solid productivity expected next week.'
        elif forecasted_productivity >= 45:
            outlook = 'moderate'
            message = 'Average productivity forecasted. Stay focused on priorities.'
        else:
            outlook = 'concerning'
            message = 'Productivity may be low next week. Consider reducing workload.'

        return {
            'forecasted_productivity_score': round(forecasted_productivity, 2),
            'forecasted_tasks_per_day': round(forecasted_tasks_per_day, 2),
            'forecasted_completion_rate': avg_completion_rate,
            'trend': 'increasing' if trend > 0 else 'decreasing' if trend < 0 else 'stable',
            'trend_magnitude': abs(trend),
            'outlook': outlook,
            'message': message
        }

    def predict_burnout_trend(self, burnout_history: List[float]) -> Dict[str, Any]:
        """
        Predict burnout risk trend.

        Args:
            burnout_history: List of historical burnout scores (0-1)

        Returns:
            Dictionary with burnout trend prediction
        """
        if not burnout_history or len(burnout_history) < 2:
            return {
                'current_risk': 0.3,
                'predicted_risk_7_days': 0.3,
                'trend': 'stable',
                'warning': None
            }

        # Current risk
        current_risk = burnout_history[-1]

        # Calculate trend
        if len(burnout_history) >= 5:
            recent_trend = burnout_history[-1] - burnout_history[-5]
        else:
            recent_trend = burnout_history[-1] - burnout_history[0]

        # Predict 7 days forward
        predicted_risk = current_risk + (recent_trend * 1.5)  # Extrapolate
        predicted_risk = max(0, min(1, predicted_risk))

        # Determine trend
        if recent_trend > 0.1:
            trend = 'increasing'
            trend_description = 'rising'
        elif recent_trend < -0.1:
            trend = 'decreasing'
            trend_description = 'improving'
        else:
            trend = 'stable'
            trend_description = 'stable'

        # Generate warning if needed
        warning = None
        if predicted_risk >= 0.7:
            warning = '⚠️ CRITICAL: Burnout risk predicted to reach critical levels within 7 days. Take immediate action!'
        elif predicted_risk >= 0.5:
            warning = '⚠️ HIGH: Burnout risk is increasing. Schedule breaks and reduce workload.'
        elif current_risk >= 0.6 and trend == 'increasing':
            warning = '⚠️ WARNING: Current burnout risk is high and trending upward.'

        return {
            'current_risk': current_risk,
            'predicted_risk_7_days': predicted_risk,
            'trend': trend,
            'trend_description': trend_description,
            'warning': warning,
            'recommendation': self._get_burnout_recommendation(predicted_risk, trend)
        }

    def suggest_optimal_schedule(self, tasks: List[Dict[str, Any]],
                                user_patterns: Dict[str, Any]) -> Dict[str, Any]:
        """
        Suggest optimal task schedule based on patterns.

        Args:
            tasks: List of pending tasks
            user_patterns: User's productivity patterns

        Returns:
            Dictionary with schedule suggestions
        """
        if not tasks:
            return {
                'suggestions': [],
                'message': 'No pending tasks to schedule.'
            }

        # Get user's best time of day
        best_time = user_patterns.get('best_time_of_day', 'Morning')
        peak_hours = user_patterns.get('peak_hours', [9, 10, 11])

        # Sort tasks by priority
        sorted_tasks = sorted(tasks, key=lambda t: t.get('priority', 0), reverse=True)

        suggestions = []

        for i, task in enumerate(sorted_tasks[:5]):  # Top 5 tasks
            priority = task.get('priority', 5)
            estimated_time = task.get('estimated_time', 1.0)
            title = task.get('title', 'Task')

            # Suggest time slot based on priority and patterns
            if priority >= 8:
                suggested_time = f"{best_time} ({peak_hours[0]}:00 - {peak_hours[0]+2}:00)"
                reason = "High priority - schedule during peak productivity"
            elif priority >= 6:
                suggested_time = f"{best_time} or early afternoon"
                reason = "Medium-high priority - good time for focused work"
            elif estimated_time < 0.5:
                suggested_time = "Anytime - quick win"
                reason = "Short task - use as filler between larger tasks"
            else:
                suggested_time = "Afternoon"
                reason = "Standard priority - afternoon slot works well"

            suggestions.append({
                'task_id': task.get('id'),
                'title': title,
                'priority': priority,
                'estimated_time': estimated_time,
                'suggested_time': suggested_time,
                'reason': reason
            })

        return {
            'suggestions': suggestions,
            'message': f"Optimized schedule based on your {best_time.lower()} productivity peak.",
            'total_estimated_time': sum(t.get('estimated_time', 0) for t in sorted_tasks[:5])
        }

    def generate_insights_report(self, tasks: List[Dict[str, Any]],
                                 historical_data: Dict[str, Any],
                                 burnout_history: List[float]) -> Dict[str, Any]:
        """
        Generate comprehensive predictive insights report.

        Args:
            tasks: List of current tasks
            historical_data: Historical performance data
            burnout_history: Burnout risk history

        Returns:
            Complete predictive insights report
        """
        # Generate predictions for pending tasks
        pending_tasks = [t for t in tasks if t.get('status') == 'pending']
        task_predictions = []

        for task in pending_tasks[:5]:  # Top 5 pending tasks
            prediction = self.predict_task_completion_probability(task, historical_data)
            task_predictions.append({
                'task_id': task.get('id'),
                'title': task.get('title', 'Task'),
                'completion_probability': prediction['probability'],
                'confidence': prediction['confidence'],
                'recommendation': prediction['recommendation']
            })

        # Weekly forecast
        weekly_forecast = self.forecast_weekly_productivity(historical_data)

        # Burnout trend
        burnout_trend = self.predict_burnout_trend(burnout_history)

        # Optimal schedule
        optimal_schedule = self.suggest_optimal_schedule(
            pending_tasks,
            historical_data.get('patterns', {})
        )

        # Summary insights
        summary_insights = self._generate_summary_insights(
            task_predictions,
            weekly_forecast,
            burnout_trend
        )

        return {
            'task_completion_predictions': task_predictions,
            'weekly_productivity_forecast': weekly_forecast,
            'burnout_risk_trend': burnout_trend,
            'optimal_schedule': optimal_schedule,
            'summary_insights': summary_insights,
            'report_generated_at': datetime.now(timezone.utc).isoformat()
        }

    # Helper methods

    def _get_burnout_recommendation(self, predicted_risk: float, trend: str) -> str:
        """Get recommendation based on burnout prediction."""
        if predicted_risk >= 0.7:
            return "Take immediate action: reduce workload, schedule time off, delegate tasks."
        elif predicted_risk >= 0.5:
            return "Be proactive: increase break frequency, avoid overtime, prioritize self-care."
        elif trend == 'increasing':
            return "Monitor closely: maintain current pace, don't add extra commitments."
        else:
            return "Continue current practices: you're managing burnout risk well."

    def _generate_summary_insights(self, task_predictions: List[Dict],
                                   weekly_forecast: Dict,
                                   burnout_trend: Dict) -> List[str]:
        """Generate summary insights from all predictions."""
        insights = []

        # Task completion insights
        if task_predictions:
            high_prob_tasks = [t for t in task_predictions if t['completion_probability'] >= 0.7]
            if high_prob_tasks:
                insights.append(
                    f"✅ {len(high_prob_tasks)} tasks have high completion probability today!"
                )

            low_prob_tasks = [t for t in task_predictions if t['completion_probability'] < 0.5]
            if low_prob_tasks:
                insights.append(
                    f"⚠️ {len(low_prob_tasks)} tasks may be challenging - consider breaking them down."
                )

        # Weekly forecast insights
        outlook = weekly_forecast.get('outlook', 'good')
        if outlook == 'excellent':
            insights.append("📈 Next week looks great! You're on an upward trend.")
        elif outlook == 'concerning':
            insights.append("📉 Next week may be challenging. Plan accordingly.")

        # Burnout insights
        if burnout_trend.get('warning'):
            insights.append(burnout_trend['warning'])

        return insights
