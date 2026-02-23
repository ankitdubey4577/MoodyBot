"""
Priority Prediction Model
Predicts task priority using multi-class classification
"""
from typing import Dict, Any, List
import numpy as np
import logging

from src.ml.base_model import BaseMLModel
from src.ml.feature_engineering import FeatureEngine

logger = logging.getLogger(__name__)

class PriorityPredictionModel(BaseMLModel):
    """
    Multi-class classification model for predicting task priority.

    Features:
    - Task urgency keywords
    - Deadlines
    - Current mood and stress level
    - Workload
    - Task type

    Target: Priority level (1-10)
    """

    def __init__(self, version: str = "1.0.0"):
        super().__init__("PriorityPredictionModel", version)
        self.feature_engine = FeatureEngine()
        self.feature_names = None

    def train(self, X: Any, y: Any, **kwargs) -> Dict[str, Any]:
        """
        Train the priority prediction model.

        Args:
            X: Training features
            y: Training labels (priority 1-10)
            **kwargs: Model parameters

        Returns:
            Training metrics
        """
        try:
            from sklearn.ensemble import RandomForestClassifier
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
            'max_depth': kwargs.get('max_depth', 10),
            'random_state': kwargs.get('random_state', 42)
        }

        # Train model
        self.model = RandomForestClassifier(**params)
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

        logger.info(f"Priority Prediction Model trained on {len(X)} samples")
        logger.info(f"Training Accuracy: {metrics['accuracy']:.2%}")

        return metrics

    def predict(self, X: Any) -> Any:
        """
        Predict task priority.

        Args:
            X: Input features

        Returns:
            Predicted priority (1-10)
        """
        if not self.is_trained:
            # Fallback to heuristic
            return self._heuristic_priority(X)

        # Convert feature dict to array if needed
        if isinstance(X, dict):
            if self.feature_names is None:
                return self._heuristic_priority(X)
            X = np.array([[X.get(f, 0) for f in self.feature_names]])
        elif isinstance(X, list) and isinstance(X[0], dict):
            X = np.array([[x.get(f, 0) for f in self.feature_names] for x in X])

        predictions = self.model.predict(X)

        # Ensure predictions are in valid range (1-10)
        predictions = np.clip(predictions, 1, 10).astype(int)

        return predictions[0] if len(predictions) == 1 else predictions

    def predict_proba(self, X: Any) -> np.ndarray:
        """
        Predict priority probabilities.

        Args:
            X: Input features

        Returns:
            Probability distribution over priorities
        """
        if not self.is_trained:
            return None

        if isinstance(X, dict):
            X = np.array([[X.get(f, 0) for f in self.feature_names]])

        return self.model.predict_proba(X)

    def predict_from_task(self, task: Dict[str, Any],
                         mood: Dict[str, Any] = None,
                         tasks_list: List[Dict[str, Any]] = None) -> int:
        """
        Predict priority from raw task data.

        Args:
            task: Task dictionary
            mood: Mood data
            tasks_list: List of all tasks

        Returns:
            Predicted priority (1-10)
        """
        # Extract features
        features = self.feature_engine.combine_features(
            task=task,
            mood=mood,
            tasks_list=tasks_list
        )

        # Predict
        return int(self.predict(features))

    def _heuristic_priority(self, features: Dict[str, Any]) -> int:
        """
        Fallback heuristic for priority when model is not trained.

        Args:
            features: Feature dictionary

        Returns:
            Priority (1-10)
        """
        priority = 5  # Default medium priority

        # Urgency indicators
        has_urgent = features.get('has_urgent_keyword', 0)
        has_deadline = features.get('has_deadline', 0)
        urgency_score = features.get('urgency_score', 0)

        if has_urgent or urgency_score > 0:
            priority += 3

        if has_deadline:
            priority += 2

        # Complexity
        complexity_score = features.get('complexity_score', 0)
        if complexity_score >= 3:
            priority += 1

        # Mood-based adjustment
        mood_negative = features.get('mood_negative', 0)
        energy_low = features.get('energy_low', 0)

        if mood_negative or energy_low:
            # Lower priority if stressed (to avoid burnout)
            priority -= 1

        # Workload
        high_priority_tasks = features.get('high_priority_tasks', 0)
        if high_priority_tasks > 5:
            # Don't add more high priority tasks if already overloaded
            priority = min(priority, 6)

        return int(np.clip(priority, 1, 10))

    def _calculate_metrics(self, y_true: Any, y_pred: Any) -> Dict[str, float]:
        """Calculate classification metrics."""
        from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

        accuracy = float(accuracy_score(y_true, y_pred))

        # Use weighted average for multi-class
        precision = float(precision_score(y_true, y_pred, average='weighted', zero_division=0))
        recall = float(recall_score(y_true, y_pred, average='weighted', zero_division=0))
        f1 = float(f1_score(y_true, y_pred, average='weighted', zero_division=0))

        return {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1
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
