"""
Advanced Analytics module for MoodyBot
Includes productivity metrics, pattern recognition, and predictive insights
"""

from .productivity_metrics import ProductivityMetrics
from .pattern_recognition import PatternRecognition
from .predictive_insights import PredictiveInsights
from .anomaly_detection import AnomalyDetection
from .analytics_dashboard import AnalyticsDashboard

__all__ = [
    'ProductivityMetrics',
    'PatternRecognition',
    'PredictiveInsights',
    'AnomalyDetection',
    'AnalyticsDashboard'
]
