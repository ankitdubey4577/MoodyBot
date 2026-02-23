"""
Burnout Detection ML Model
Binary classification model for predicting burnout risk
"""
from typing import Dict, Any, List
import numpy as np
import logging

from src.ml.base_model import BaseMLModel

logger = logging.getLogger(__name__)

class BurnoutDetectionModel(BaseMLModel):
    """
    Binary classification model for detecting burnout risk.

    Features:
    - Work hours and patterns
    - Task completion rate
    - Mood trends
    - Energy levels over time
    - Sentiment patterns
    - Break frequency

    Target: Burnout risk (0 = low, 1 = high)
    """

    def __init__(self, version: str = "1.0.0"):
        super().__init__("BurnoutDetectionModel", version)
        self.feature_names = None

    def train(self, X: Any, y: Any, **kwargs) -> Dict[str, Any]:
        """
        Train the burnout detection model.

        Args:
            X: Training features
            y: Training labels (0 = no burnout, 1 = burnout)
            **kwargs: Model parameters

        Returns:
            Training metrics
        """
        try:
            from sklearn.ensemble import GradientBoostingClassifier
        except ImportError:
            logger.error("scikit-learn not installed")
            return {}

        # Convert feature dicts to arrays if needed
        if isinstance(X, list) and isinstance(X[0], dict):
            self.feature_names = list(X[0].keys())
            X = np.array([[x[f] for f in self.feature_names] for x in X])
        elif hasattr(X, 'columns'):
            self.feature_names = list(X.columns)
            X = X.values

        # Model parameters
        params = {
            'n_estimators': kwargs.get('n_estimators', 100),
            'max_depth': kwargs.get('max_depth', 5),
            'learning_rate': kwargs.get('learning_rate', 0.1),
            'random_state': kwargs.get('random_state', 42)
        }

        # Train model
        self.model = GradientBoostingClassifier(**params)
        self.model.fit(X, y)

        # Update metadata
        self.is_trained = True
        self.metadata.update({
            'trained_at': np.datetime64('now').astype(str),
            'training_samples': len(X),
            'feature_names': self.feature_names,
            'model_params': params
        })

        # Calculate training metrics
        y_pred = self.model.predict(X)
        metrics = self._calculate_metrics(y, y_pred)
        self.metadata['metrics'] = metrics

        logger.info(f"Burnout Detection Model trained on {len(X)} samples")
        logger.info(f"Training Accuracy: {metrics['accuracy']:.2%}")
        logger.info(f"Training F1 Score: {metrics['f1_score']:.2%}")

        return metrics

    def predict(self, X: Any) -> Any:
        """
        Predict burnout risk.

        Args:
            X: Input features

        Returns:
            Binary prediction (0 or 1)
        """
        if not self.is_trained:
            return 0  # Default to no burnout

        # Convert feature dict to array if needed
        if isinstance(X, dict):
            if self.feature_names is None:
                return 0
            X = np.array([[X.get(f, 0) for f in self.feature_names]])
        elif isinstance(X, list) and isinstance(X[0], dict):
            X = np.array([[x.get(f, 0) for f in self.feature_names] for x in X])

        predictions = self.model.predict(X)
        return predictions[0] if len(predictions) == 1 else predictions

    def predict_proba(self, X: Any) -> float:
        """
        Predict burnout probability.

        Args:
            X: Input features

        Returns:
            Probability of burnout (0-1)
        """
        if not self.is_trained:
            return 0.0

        if isinstance(X, dict):
            if self.feature_names is None:
                return 0.0
            X = np.array([[X.get(f, 0) for f in self.feature_names]])

        proba = self.model.predict_proba(X)[0][1]  # Probability of class 1 (burnout)
        return float(proba)

    def predict_from_state(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Predict burnout from agent state.

        Args:
            state: Agent state dictionary

        Returns:
            Dictionary with prediction and probability
        """
        # Extract features from state
        features = self._extract_features_from_state(state)

        # Predict
        if self.is_trained and self.feature_names:
            burnout_proba = self.predict_proba(features)
            burnout_pred = int(burnout_proba > 0.5)
        else:
            # Fallback to heuristic (use existing burnout detector)
            from src.agents.burnout_detector import BurnoutDetector
            detector = BurnoutDetector()
            result = detector.detect(state)
            burnout_proba = result['mood']['burnout_risk']
            burnout_pred = int(burnout_proba > 0.5)

        return {
            'burnout_predicted': burnout_pred,
            'burnout_probability': burnout_proba,
            'risk_level': self._get_risk_level(burnout_proba)
        }

    def _extract_features_from_state(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Extract ML features from agent state."""
        mood_data = state.get('mood', {})
        tasks = state.get('tasks', [])
        analytics = state.get('analytics', {})

        features = {
            # Mood features
            'energy_level': mood_data.get('energy_level', 5),
            'sentiment_score': mood_data.get('sentiment_score', 0),
            'mood_negative': int(mood_data.get('label', '') in ['stressed', 'anxious', 'overwhelmed']),

            # Task load features
            'total_tasks': len(tasks),
            'high_priority_tasks': sum(1 for t in tasks if t.get('effective_priority', 0) >= 7),
            'avg_priority': np.mean([t.get('effective_priority', 5) for t in tasks]) if tasks else 5,

            # Performance features
            'completion_rate': analytics.get('completion_rate', 0.7),
            'avg_task_time': analytics.get('average_task_time', 60)
        }

        return features

    def _get_risk_level(self, probability: float) -> str:
        """Convert probability to risk level."""
        if probability >= 0.8:
            return "CRITICAL"
        elif probability >= 0.6:
            return "HIGH"
        elif probability >= 0.4:
            return "MODERATE"
        elif probability >= 0.2:
            return "LOW"
        else:
            return "MINIMAL"

    def _calculate_metrics(self, y_true: Any, y_pred: Any) -> Dict[str, float]:
        """Calculate binary classification metrics."""
        from sklearn.metrics import (
            accuracy_score, precision_score, recall_score,
            f1_score, roc_auc_score, confusion_matrix
        )

        accuracy = float(accuracy_score(y_true, y_pred))
        precision = float(precision_score(y_true, y_pred, zero_division=0))
        recall = float(recall_score(y_true, y_pred, zero_division=0))
        f1 = float(f1_score(y_true, y_pred, zero_division=0))

        # ROC AUC if we have predicted probabilities
        try:
            y_proba = self.model.predict_proba(self.model.predict(y_true))[:, 1]
            auc = float(roc_auc_score(y_true, y_proba))
        except Exception:
            auc = 0.0

        # Confusion matrix
        cm = confusion_matrix(y_true, y_pred)
        tn, fp, fn, tp = cm.ravel() if cm.size == 4 else (0, 0, 0, 0)

        return {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1,
            'roc_auc': auc,
            'true_negatives': int(tn),
            'false_positives': int(fp),
            'false_negatives': int(fn),
            'true_positives': int(tp)
        }

    def get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance scores."""
        if not self.is_trained or self.feature_names is None:
            return {}

        try:
            importances = self.model.feature_importances_
            return dict(zip(self.feature_names, importances.tolist()))
        except AttributeError:
            return {}
