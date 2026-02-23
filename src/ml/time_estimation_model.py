"""
Time Estimation Model
Predicts task completion time using XGBoost regression
"""
from typing import Dict, Any, List
import numpy as np
import logging

from src.ml.base_model import BaseMLModel
from src.ml.feature_engineering import FeatureEngine

logger = logging.getLogger(__name__)

class TimeEstimationModel(BaseMLModel):
    """
    XGBoost regression model for predicting task completion time.

    Features:
    - Task complexity (text length, verb type)
    - User priority
    - Mood and energy level
    - Time of day
    - Historical patterns

    Target: Completion time in hours
    """

    def __init__(self, version: str = "1.0.0"):
        super().__init__("TimeEstimationModel", version)
        self.feature_engine = FeatureEngine()
        self.feature_names = None

    def train(self, X: Any, y: Any, **kwargs) -> Dict[str, Any]:
        """
        Train the XGBoost regression model.

        Args:
            X: Training features (array-like or list of feature dicts)
            y: Training labels (completion times in hours)
            **kwargs: XGBoost parameters

        Returns:
            Training metrics
        """
        try:
            # Try importing xgboost
            import xgboost as xgb
        except ImportError:
            logger.warning("XGBoost not installed, using simple linear model")
            return self._train_simple_model(X, y)

        # Convert feature dicts to arrays if needed
        if isinstance(X, list) and isinstance(X[0], dict):
            self.feature_names = list(X[0].keys())
            X = np.array([[x[f] for f in self.feature_names] for x in X])
        elif hasattr(X, 'columns'):
            self.feature_names = list(X.columns)
            X = X.values

        # XGBoost parameters
        params = {
            'objective': 'reg:squarederror',
            'max_depth': kwargs.get('max_depth', 6),
            'learning_rate': kwargs.get('learning_rate', 0.1),
            'n_estimators': kwargs.get('n_estimators', 100),
            'random_state': kwargs.get('random_state', 42)
        }

        # Train model
        self.model = xgb.XGBRegressor(**params)
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

        logger.info(f"Time Estimation Model trained on {len(X)} samples")
        logger.info(f"Training MAE: {metrics['mae']:.2f} hours")

        return metrics

    def _train_simple_model(self, X: Any, y: Any) -> Dict[str, Any]:
        """Fallback: Train simple linear regression model."""
        from sklearn.linear_model import LinearRegression

        if isinstance(X, list) and isinstance(X[0], dict):
            self.feature_names = list(X[0].keys())
            X = np.array([[x[f] for f in self.feature_names] for x in X])

        self.model = LinearRegression()
        self.model.fit(X, y)
        self.is_trained = True

        y_pred = self.model.predict(X)
        metrics = self._calculate_metrics(y, y_pred)

        logger.info("Using simple Linear Regression model (XGBoost not available)")
        return metrics

    def predict(self, X: Any) -> Any:
        """
        Predict task completion time.

        Args:
            X: Input features

        Returns:
            Predicted completion time (hours)
        """
        if not self.is_trained:
            # Fallback to heuristic
            return self._heuristic_estimate(X)

        # Convert feature dict to array if needed
        if isinstance(X, dict):
            if self.feature_names is None:
                return self._heuristic_estimate(X)
            X = np.array([[X.get(f, 0) for f in self.feature_names]])
        elif isinstance(X, list) and isinstance(X[0], dict):
            X = np.array([[x.get(f, 0) for f in self.feature_names] for x in X])

        predictions = self.model.predict(X)

        # Ensure predictions are positive and reasonable (0.1 to 40 hours)
        predictions = np.clip(predictions, 0.1, 40)

        return predictions[0] if len(predictions) == 1 else predictions

    def predict_from_task(self, task: Dict[str, Any],
                         mood: Dict[str, Any] = None,
                         tasks_list: List[Dict[str, Any]] = None) -> float:
        """
        Predict completion time from raw task data.

        Args:
            task: Task dictionary
            mood: Mood data
            tasks_list: List of all tasks

        Returns:
            Predicted completion time (hours)
        """
        # Extract features
        features = self.feature_engine.combine_features(
            task=task,
            mood=mood,
            tasks_list=tasks_list
        )

        # Predict
        return float(self.predict(features))

    def _heuristic_estimate(self, features: Dict[str, Any]) -> float:
        """
        Fallback heuristic for time estimation when model is not trained.

        Args:
            features: Feature dictionary

        Returns:
            Estimated time (hours)
        """
        # Base estimate on text length and complexity
        total_words = features.get('total_words', 10)
        complexity_score = features.get('complexity_score', 1)
        priority = features.get('priority', 5)

        # Simple heuristic
        if total_words < 10:
            base_hours = 0.5
        elif total_words < 20:
            base_hours = 1.0
        elif total_words < 40:
            base_hours = 2.0
        else:
            base_hours = 4.0

        # Adjust for complexity
        base_hours *= (1 + complexity_score * 0.2)

        # Adjust for priority (high priority might be more complex)
        if priority >= 8:
            base_hours *= 1.2

        return round(base_hours, 1)

    def _calculate_metrics(self, y_true: Any, y_pred: Any) -> Dict[str, float]:
        """Calculate regression metrics."""
        from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

        mae = float(mean_absolute_error(y_true, y_pred))
        rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
        r2 = float(r2_score(y_true, y_pred))

        return {
            'mae': mae,
            'rmse': rmse,
            'r2_score': r2
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
