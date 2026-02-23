"""
Model Trainer - Trains all ML models with collected data
"""
from typing import Dict, Any, List, Optional
from pathlib import Path
import logging
import numpy as np

from src.ml.data_collector import DataCollector
from src.ml.feature_engineering import FeatureEngine
from src.ml.time_estimation_model import TimeEstimationModel
from src.ml.priority_prediction_model import PriorityPredictionModel
from src.ml.burnout_detection_model import BurnoutDetectionModel

logger = logging.getLogger(__name__)

class ModelTrainer:
    """
    Manages training pipeline for all ML models.
    """

    def __init__(self, db_session=None, model_dir: str = "models"):
        """
        Initialize model trainer.

        Args:
            db_session: Database session for data collection
            model_dir: Directory to save trained models
        """
        self.db_session = db_session
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)

        self.data_collector = DataCollector(db_session) if db_session else None
        self.feature_engine = FeatureEngine()

        # Initialize models
        self.time_model = TimeEstimationModel()
        self.priority_model = PriorityPredictionModel()
        self.burnout_model = BurnoutDetectionModel()

    def train_all_models(self, use_synthetic: bool = True) -> Dict[str, Dict[str, Any]]:
        """
        Train all ML models.

        Args:
            use_synthetic: Use synthetic data if real data is insufficient

        Returns:
            Dictionary of training results for each model
        """
        results = {}

        logger.info("Starting model training pipeline...")

        # Train Time Estimation Model
        logger.info("Training Time Estimation Model...")
        results['time_estimation'] = self.train_time_estimation_model(use_synthetic)

        # Train Priority Prediction Model
        logger.info("Training Priority Prediction Model...")
        results['priority_prediction'] = self.train_priority_prediction_model(use_synthetic)

        # Train Burnout Detection Model
        logger.info("Training Burnout Detection Model...")
        results['burnout_detection'] = self.train_burnout_detection_model(use_synthetic)

        logger.info("All models trained successfully!")

        return results

    def train_time_estimation_model(self, use_synthetic: bool = True) -> Dict[str, Any]:
        """Train the time estimation model."""
        try:
            # Collect data
            if self.data_collector:
                data = self.data_collector.collect_task_completion_data()
            else:
                data = []

            # Use synthetic data if insufficient real data
            if len(data) < 50 and use_synthetic:
                logger.info("Generating synthetic data for time estimation model...")
                synthetic = self.data_collector.generate_synthetic_training_data(100) if self.data_collector else {}
                if synthetic:
                    data = synthetic.get('task_completion', [])

            if not data:
                logger.warning("No training data available for time estimation model")
                return {'status': 'failed', 'reason': 'no_data'}

            # Prepare features and labels
            X, y = self._prepare_time_estimation_data(data)

            # Train model
            metrics = self.time_model.train(X, y)

            # Save model
            model_path = self.model_dir / "time_estimation_model.pkl"
            self.time_model.save(str(model_path))

            return {
                'status': 'success',
                'samples': len(X),
                'metrics': metrics,
                'model_path': str(model_path)
            }

        except Exception as e:
            logger.error(f"Error training time estimation model: {e}")
            return {'status': 'failed', 'error': str(e)}

    def train_priority_prediction_model(self, use_synthetic: bool = True) -> Dict[str, Any]:
        """Train the priority prediction model."""
        try:
            # Collect data
            if self.data_collector:
                data = self.data_collector.collect_priority_change_data()
            else:
                data = []

            # Use synthetic data if insufficient
            if len(data) < 50 and use_synthetic:
                logger.info("Generating synthetic data for priority prediction model...")
                synthetic = self.data_collector.generate_synthetic_training_data(100) if self.data_collector else {}
                if synthetic:
                    data = synthetic.get('priority_changes', [])

            if not data:
                logger.warning("No training data available for priority prediction model")
                return {'status': 'failed', 'reason': 'no_data'}

            # Prepare features and labels
            X, y = self._prepare_priority_prediction_data(data)

            # Train model
            metrics = self.priority_model.train(X, y)

            # Save model
            model_path = self.model_dir / "priority_prediction_model.pkl"
            self.priority_model.save(str(model_path))

            return {
                'status': 'success',
                'samples': len(X),
                'metrics': metrics,
                'model_path': str(model_path)
            }

        except Exception as e:
            logger.error(f"Error training priority prediction model: {e}")
            return {'status': 'failed', 'error': str(e)}

    def train_burnout_detection_model(self, use_synthetic: bool = True) -> Dict[str, Any]:
        """Train the burnout detection model."""
        try:
            # Collect data
            if self.data_collector:
                data = self.data_collector.collect_mood_history_data()
            else:
                data = []

            # Use synthetic data if insufficient
            if len(data) < 50 and use_synthetic:
                logger.info("Generating synthetic data for burnout detection model...")
                synthetic = self.data_collector.generate_synthetic_training_data(100) if self.data_collector else {}
                if synthetic:
                    data = synthetic.get('mood_history', [])

            if not data:
                logger.warning("No training data available for burnout detection model")
                return {'status': 'failed', 'reason': 'no_data'}

            # Prepare features and labels
            X, y = self._prepare_burnout_detection_data(data)

            # Train model
            metrics = self.burnout_model.train(X, y)

            # Save model
            model_path = self.model_dir / "burnout_detection_model.pkl"
            self.burnout_model.save(str(model_path))

            return {
                'status': 'success',
                'samples': len(X),
                'metrics': metrics,
                'model_path': str(model_path)
            }

        except Exception as e:
            logger.error(f"Error training burnout detection model: {e}")
            return {'status': 'failed', 'error': str(e)}

    def _prepare_time_estimation_data(self, data: List[Dict[str, Any]]) -> tuple:
        """Prepare training data for time estimation model."""
        X = []
        y = []

        for record in data:
            # Extract features
            task = {
                'title': record.get('title', ''),
                'description': record.get('description', ''),
                'priority': record.get('priority', 5)
            }

            mood = {
                'label': record.get('mood', 'neutral'),
                'energy_level': 5,
                'sentiment_score': 0.0
            }

            features = self.feature_engine.combine_features(task=task, mood=mood)

            # Target: time in hours
            time_minutes = record.get('time_taken', 60)
            time_hours = time_minutes / 60

            X.append(features)
            y.append(time_hours)

        return X, np.array(y)

    def _prepare_priority_prediction_data(self, data: List[Dict[str, Any]]) -> tuple:
        """Prepare training data for priority prediction model."""
        X = []
        y = []

        for record in data:
            task = {
                'title': record.get('title', ''),
                'priority': record.get('user_priority', 5)
            }

            features = self.feature_engine.extract_task_features(task)

            # Target: effective priority
            priority = record.get('effective_priority', record.get('priority', 5))

            X.append(features)
            y.append(int(priority))

        return X, np.array(y)

    def _prepare_burnout_detection_data(self, data: List[Dict[str, Any]]) -> tuple:
        """Prepare training data for burnout detection model."""
        X = []
        y = []

        for record in data:
            features = {
                'energy_level': record.get('energy_level', 5),
                'sentiment_score': record.get('sentiment_score', 0.0),
                'mood_negative': int(record.get('mood_label', '') in ['stressed', 'anxious', 'overwhelmed']),
                'total_tasks': 5,  # Default
                'high_priority_tasks': 2,  # Default
                'avg_priority': 5,
                'completion_rate': 0.7,
                'avg_task_time': 60
            }

            # Target: burnout level from record
            burnout_level = record.get('burnout_level', 0.0)
            is_burnout = int(burnout_level > 0.5)

            X.append(features)
            y.append(is_burnout)

        return X, np.array(y)

    def load_models(self):
        """Load all trained models from disk."""
        try:
            time_path = self.model_dir / "time_estimation_model.pkl"
            if time_path.exists():
                self.time_model.load(str(time_path))
                logger.info("Loaded Time Estimation Model")

            priority_path = self.model_dir / "priority_prediction_model.pkl"
            if priority_path.exists():
                self.priority_model.load(str(priority_path))
                logger.info("Loaded Priority Prediction Model")

            burnout_path = self.model_dir / "burnout_detection_model.pkl"
            if burnout_path.exists():
                self.burnout_model.load(str(burnout_path))
                logger.info("Loaded Burnout Detection Model")

        except Exception as e:
            logger.error(f"Error loading models: {e}")

    def get_all_models(self) -> Dict[str, Any]:
        """Get all model instances."""
        return {
            'time_estimation': self.time_model,
            'priority_prediction': self.priority_model,
            'burnout_detection': self.burnout_model
        }
