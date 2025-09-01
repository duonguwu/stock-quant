"""Model training pipeline"""

import pandas as pd
import numpy as np
import json
from pathlib import Path
from typing import Dict, Any, Tuple
from loguru import logger

from ..models.xgboost_trainer import create_xgboost_trainer
from ..utils.config_loader import config_loader
from ..utils.time_series_split import create_time_series_splits


class TrainingPipeline:
    """Model training and evaluation pipeline"""

    def __init__(self, config: Dict[str, Any]):
        """Initialize training pipeline

        Args:
            config: Model configuration
        """
        self.config = config
        self.trainer = None
        self.results = {}

    def setup(self) -> None:
        """Setup training pipeline"""
        logger.info("Setting up training pipeline...")
        self.trainer = create_xgboost_trainer(self.config)
        logger.info("Training pipeline setup completed")
    
    def load_data_splits(self) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Load train/validation/test data splits

        Returns:
            Tuple of (train_data, val_data, test_data)
        """
        data_dir = Path("data/final")

        train_data = pd.read_csv(data_dir / "train_data.csv")
        val_data = pd.read_csv(data_dir / "val_data.csv")
        test_data = pd.read_csv(data_dir / "test_data.csv")

        logger.info(f"Loaded data - Train: {len(train_data)}, Val: {len(val_data)}, Test: {len(test_data)}")

        return train_data, val_data, test_data

    def prepare_features_and_labels(
        self,
        data: pd.DataFrame
    ) -> Tuple[pd.DataFrame, pd.Series]:
        """Extract features and labels from data

        Args:
            data: Dataset with features and labels

        Returns:
            Tuple of (features, labels)
        """
        # Define columns to exclude from features
        exclude_cols = [
            'ticker', 'timestamp', 'label', 'hit_time', 'hit_type',
            'ub', 'lb', 'vbar_end'
        ]

        # Get feature columns
        feature_cols = [col for col in data.columns if col not in exclude_cols]

        X = data[feature_cols]
        y = data['label']

        # Remove samples without labels
        valid_mask = ~y.isnull()
        X = X[valid_mask]
        y = y[valid_mask]

        logger.info(f"Prepared features: {X.shape}, labels: {y.shape}")
        logger.info(f"Feature columns: {len(feature_cols)}")

        return X, y
 
    def run_training_pipeline(self) -> Dict[str, Any]:
        """Run complete training pipeline

        Returns:
            Training results
        """
        logger.info("Starting training pipeline...")

        # Setup if needed
        if self.trainer is None:
            self.setup()

        # Load data
        train_data, val_data, test_data = self.load_data_splits()

        # Prepare features and labels
        X_train, y_train = self.prepare_features_and_labels(train_data)
        X_val, y_val = self.prepare_features_and_labels(val_data)
        X_test, y_test = self.prepare_features_and_labels(test_data)

        # Get feature names
        feature_names = X_train.columns.tolist()

        # Prepare training data
        X_train_scaled, y_train_encoded = self.trainer.prepare_data(X_train, y_train)
        X_val_scaled, y_val_encoded = self.trainer.prepare_data(X_val, y_val, scale_features=False)
        X_test_scaled, y_test_encoded = self.trainer.prepare_data(X_test, y_test, scale_features=False)

        # Calculate sample weights for class balancing
        sample_weights = self.trainer.calculate_sample_weights(y_train_encoded)

        # Hyperparameter optimization (if enabled)
        hyperopt_config = self.config.get('model', {}).get('hyperopt', {})
        if hyperopt_config.get('enabled', False):
            logger.info("Running hyperparameter optimization...")

            # Create time series splits for CV
            combined_data = pd.concat([train_data, val_data])
            cv_splits = create_time_series_splits(combined_data, self.config)

            # Prepare combined data for optimization
            X_combined, y_combined = self.prepare_features_and_labels(combined_data)
            X_combined_scaled, y_combined_encoded = self.trainer.prepare_data(X_combined, y_combined)

            # Run optimization
            best_params = self.trainer.hyperparameter_optimization(
                X_combined_scaled,
                y_combined_encoded,
                cv_splits,
                n_trials=hyperopt_config.get('n_trials', 100)
            )

            # Update model with best parameters
            self.trainer.best_params_ = best_params

        # Train final model
        logger.info("Training final model...")
        self.trainer.train_model(
            X_train_scaled,
            y_train_encoded,
            X_val_scaled,
            y_val_encoded,
            sample_weight=sample_weights
        )

        # Evaluate model
        logger.info("Evaluating model...")
        evaluation_results = self.trainer.evaluate_model(
            X_test_scaled,
            y_test_encoded,
            feature_names=feature_names
        )

        # Save model
        model_config = self.config.get('model', {}).get('persistence', {})
        if model_config.get('save_model', True):
            model_path = model_config.get('model_path', 'models/xgboost_model.pkl')
            scaler_path = model_config.get('scaler_path', 'models/feature_scaler.pkl')

            self.trainer.save_model(model_path, scaler_path)

        # Compile results
        self.results = {
            'model_config': self.config.get('model', {}),
            'training_data_shape': X_train.shape,
            'validation_data_shape': X_val.shape,
            'test_data_shape': X_test.shape,
            'feature_names': feature_names,
            'best_params': getattr(self.trainer, 'best_params_', None),
            'evaluation': evaluation_results
        }

        # Save results
        self.save_results()

        logger.info("Training pipeline completed successfully")
        return self.results

    def save_results(self) -> None:
        """Save training results to file"""
        results_dir = Path("results")
        results_dir.mkdir(exist_ok=True)

        # Save metrics as JSON
        metrics_path = results_dir / "model_metrics.json"

        # Prepare JSON-serializable results
        json_results = {
            'model_config': self.results['model_config'],
            'data_shapes': {
                'train': list(self.results['training_data_shape']),
                'val': list(self.results['validation_data_shape']),
                'test': list(self.results['test_data_shape'])
            },
            'feature_count': len(self.results['feature_names']),
            'best_params': self.results['best_params'],
            'evaluation_metrics': {
                'accuracy': self.results['evaluation']['accuracy'],
                'macro_f1': self.results['evaluation']['macro_f1']
            },
            'classification_report': self.results['evaluation']['classification_report']
        }

        with open(metrics_path, 'w') as f:
            json.dump(json_results, f, indent=2)

        logger.info(f"Results saved to {metrics_path}")

        # Save feature importance
        if self.results['evaluation']['feature_importance']:
            importance_df = pd.DataFrame(self.results['evaluation']['feature_importance'])
            importance_path = results_dir / "feature_importance.csv"
            importance_df.to_csv(importance_path, index=False)
            logger.info(f"Feature importance saved to {importance_path}")

    def create_prediction_function(self):
        """Create a prediction function for production use

        Returns:
            Prediction function
        """
        if self.trainer is None or self.trainer.model is None:
            raise ValueError("Model not trained yet")

        feature_names = self.results.get('feature_names', [])
        
        def predict(data: pd.DataFrame) -> Dict[str, np.ndarray]:
            """Make predictions on new data

            Args:
                data: DataFrame with features
     
            Returns:
                Predictions dictionary
            """
            # Select only the features used in training
            if feature_names:
                data_features = data[feature_names]
            else:
                # Fallback: use all columns except known non-features
                exclude_cols = ['ticker', 'timestamp', 'label', 'hit_time', 'hit_type', 'ub', 'lb', 'vbar_end']
                feature_cols = [col for col in data.columns if col not in exclude_cols]
                data_features = data[feature_cols]

            return self.trainer.predict(data_features)

        return predict


def run_training_pipeline(config_path: str = "config/model_config.yaml") -> Dict[str, Any]:
    """Run training pipeline with configuration

    Args:
        config_path: Path to model configuration file

    Returns:
        Training results
    """
    # Load configuration
    config = config_loader.load_config("model_config")

    # Create and run pipeline
    pipeline = TrainingPipeline(config)
    results = pipeline.run_training_pipeline()

    return results


if __name__ == "__main__":
    # Run training pipeline
    results = run_training_pipeline()

    logger.info("Training completed!")
    logger.info(f"Model accuracy: {results['evaluation']['accuracy']:.4f}")
    logger.info(f"Macro F1 score: {results['evaluation']['macro_f1']:.4f}")
