"""
Base Model Class for ML Models
Provides common functionality for training, prediction, and persistence
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pathlib import Path
import pickle
import json
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class BaseMLModel(ABC):
    """
    Abstract base class for all ML models.
    Provides common functionality for training, prediction, and persistence.
    """

    def __init__(self, model_name: str, version: str = "1.0.0"):
        """
        Initialize the model.

        Args:
            model_name: Name of the model
            version: Model version
        """
        self.model_name = model_name
        self.version = version
        self.model = None
        self.is_trained = False
        self.metadata = {
            'model_name': model_name,
            'version': version,
            'created_at': datetime.now(timezone.utc).isoformat(),
            'trained_at': None,
            'training_samples': 0,
            'feature_names': [],
            'metrics': {}
        }

    @abstractmethod
    def train(self, X: Any, y: Any, **kwargs) -> Dict[str, Any]:
        """
        Train the model.

        Args:
            X: Training features
            y: Training labels
            **kwargs: Additional training parameters

        Returns:
            Training metrics
        """
        pass

    @abstractmethod
    def predict(self, X: Any) -> Any:
        """
        Make predictions.

        Args:
            X: Input features

        Returns:
            Predictions
        """
        pass

    def evaluate(self, X: Any, y: Any) -> Dict[str, float]:
        """
        Evaluate the model.

        Args:
            X: Test features
            y: True labels

        Returns:
            Evaluation metrics
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before evaluation")

        predictions = self.predict(X)
        metrics = self._calculate_metrics(y, predictions)
        return metrics

    @abstractmethod
    def _calculate_metrics(self, y_true: Any, y_pred: Any) -> Dict[str, float]:
        """Calculate model-specific metrics."""
        pass

    def save(self, model_path: str):
        """
        Save the model to disk.

        Args:
            model_path: Path to save the model
        """
        if not self.is_trained:
            logger.warning("Saving untrained model")

        model_path = Path(model_path)
        model_path.parent.mkdir(parents=True, exist_ok=True)

        # Save model
        with open(model_path, 'wb') as f:
            pickle.dump(self.model, f)

        # Save metadata
        metadata_path = model_path.with_suffix('.json')
        with open(metadata_path, 'w') as f:
            json.dump(self.metadata, f, indent=2)

        logger.info(f"Model saved to {model_path}")

    def load(self, model_path: str):
        """
        Load the model from disk.

        Args:
            model_path: Path to the saved model
        """
        model_path = Path(model_path)

        if not model_path.exists():
            raise FileNotFoundError(f"Model file not found: {model_path}")

        # Load model
        with open(model_path, 'rb') as f:
            self.model = pickle.load(f)

        # Load metadata
        metadata_path = model_path.with_suffix('.json')
        if metadata_path.exists():
            with open(metadata_path, 'r') as f:
                self.metadata = json.load(f)

        self.is_trained = True
        logger.info(f"Model loaded from {model_path}")

    def get_info(self) -> Dict[str, Any]:
        """Get model information."""
        return {
            'model_name': self.model_name,
            'version': self.version,
            'is_trained': self.is_trained,
            'metadata': self.metadata
        }

    def update_metadata(self, **kwargs):
        """Update model metadata."""
        self.metadata.update(kwargs)
