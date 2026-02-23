"""
Train ML Models Script
Trains all machine learning models with synthetic data
"""
import sys
sys.path.insert(0, '.')

import logging
from src.ml.model_trainer import ModelTrainer
from src.ml.data_collector import DataCollector

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

print("=" * 70)
print("ML MODELS TRAINING PIPELINE")
print("=" * 70)
print()

# Initialize trainer (without database for now - will use synthetic data)
print("Initializing Model Trainer...")
trainer = ModelTrainer(db_session=None, model_dir="models")
print("[OK] Trainer initialized")
print()

# Generate synthetic training data
print("Generating Synthetic Training Data...")
data_collector = DataCollector(None)
synthetic_data = data_collector.generate_synthetic_training_data(num_samples=200)
print(f"[OK] Generated {len(synthetic_data['task_completion'])} samples per model")
print()

# Train all models
print("=" * 70)
print("TRAINING ALL MODELS")
print("=" * 70)
print()

results = trainer.train_all_models(use_synthetic=True)

# Display results
print()
print("=" * 70)
print("TRAINING RESULTS")
print("=" * 70)
print()

for model_name, result in results.items():
    print(f"Model: {model_name.replace('_', ' ').title()}")
    print("-" * 70)

    if result.get('status') == 'success':
        print(f"  Status: SUCCESS")
        print(f"  Training Samples: {result.get('samples', 0)}")

        metrics = result.get('metrics', {})
        if metrics:
            print(f"  Metrics:")
            for metric_name, value in metrics.items():
                if isinstance(value, float):
                    print(f"    - {metric_name}: {value:.4f}")
                else:
                    print(f"    - {metric_name}: {value}")

        print(f"  Model Saved: {result.get('model_path', 'N/A')}")
    else:
        print(f"  Status: FAILED")
        print(f"  Reason: {result.get('reason', result.get('error', 'Unknown'))}")

    print()

# Test predictions with each model
print("=" * 70)
print("TESTING MODEL PREDICTIONS")
print("=" * 70)
print()

# Test 1: Time Estimation
print("Test 1: Time Estimation Model")
print("-" * 70)
try:
    test_task = {
        'title': 'Implement new authentication feature with OAuth integration',
        'description': 'Build complete OAuth2 authentication system',
        'priority': 8
    }

    test_mood = {
        'label': 'focused',
        'energy_level': 7,
        'sentiment_score': 0.3
    }

    estimated_time = trainer.time_model.predict_from_task(test_task, test_mood)
    print(f"  Task: \"{test_task['title']}\"")
    print(f"  Estimated Time: {estimated_time:.1f} hours")
    print(f"  [OK] Prediction successful")
except Exception as e:
    print(f"  [ERROR] {e}")
print()

# Test 2: Priority Prediction
print("Test 2: Priority Prediction Model")
print("-" * 70)
try:
    test_task = {
        'title': 'URGENT: Fix critical production bug causing downtime',
        'description': 'Server crashes every hour',
        'priority': 5
    }

    predicted_priority = trainer.priority_model.predict_from_task(test_task)
    print(f"  Task: \"{test_task['title']}\"")
    print(f"  User Priority: {test_task['priority']}/10")
    print(f"  AI Predicted Priority: {predicted_priority}/10")
    print(f"  [OK] Prediction successful")
except Exception as e:
    print(f"  [ERROR] {e}")
print()

# Test 3: Burnout Detection
print("Test 3: Burnout Detection Model")
print("-" * 70)
try:
    test_state = {
        'mood': {
            'label': 'overwhelmed',
            'energy_level': 2,
            'sentiment_score': -0.6
        },
        'tasks': [
            {'title': f'High priority task {i}', 'effective_priority': 9}
            for i in range(12)
        ],
        'analytics': {
            'completion_rate': 0.3
        }
    }

    burnout_result = trainer.burnout_model.predict_from_state(test_state)
    print(f"  Mood: {test_state['mood']['label'].title()}")
    print(f"  Energy Level: {test_state['mood']['energy_level']}/10")
    print(f"  Total Tasks: {len(test_state['tasks'])}")
    print(f"  Completion Rate: {test_state['analytics']['completion_rate']:.1%}")
    print()
    print(f"  Burnout Prediction: {burnout_result['burnout_predicted']} (0=No, 1=Yes)")
    print(f"  Burnout Probability: {burnout_result['burnout_probability']:.2%}")
    print(f"  Risk Level: {burnout_result['risk_level']}")
    print(f"  [OK] Prediction successful")
except Exception as e:
    print(f"  [ERROR] {e}")
print()

# Model Information
print("=" * 70)
print("MODEL INFORMATION")
print("=" * 70)
print()

models = trainer.get_all_models()
for name, model in models.items():
    info = model.get_info()
    print(f"{name.replace('_', ' ').title()}:")
    print(f"  - Version: {info['version']}")
    print(f"  - Trained: {info['is_trained']}")
    print(f"  - Training Samples: {info['metadata'].get('training_samples', 0)}")
    print()

# Feature Importance
print("=" * 70)
print("FEATURE IMPORTANCE (Top 5)")
print("=" * 70)
print()

for name, model in models.items():
    if model.is_trained:
        importance = model.get_feature_importance()
        if importance:
            print(f"{name.replace('_', ' ').title()}:")

            # Sort by importance
            sorted_features = sorted(importance.items(), key=lambda x: x[1], reverse=True)[:5]

            for feature, score in sorted_features:
                print(f"  - {feature}: {score:.4f}")
            print()

print("=" * 70)
print("TRAINING COMPLETE")
print("=" * 70)
print()
print("All models have been trained and saved to the 'models/' directory.")
print("Models are now ready to be integrated into the MoodyBot system.")
print()
print("Next Steps:")
print("  1. Integrate models with existing agents")
print("  2. Replace heuristics with ML predictions")
print("  3. Collect real user data for retraining")
print("  4. Monitor model performance")
print()
