"""End-to-end data processing pipeline"""

import pandas as pd
from pathlib import Path
from typing import Dict, Any, Tuple
from loguru import logger

from ..data.data_fetcher import create_data_fetcher
from ..data.feature_engineering import create_feature_engineer
from ..data.labeling import apply_triple_barrier_labeling, analyze_labeling_quality
from ..utils.config_loader import config_loader


class DataPipeline:
    """End-to-end data processing pipeline"""

    def __init__(self, username: str, password: str):
        """Initialize pipeline with FiinQuantX credentials

        Args:
            username: FiinQuantX username
            password: FiinQuantX password
        """
        self.username = username
        self.password = password
        self.data_fetcher = None
        self.feature_engineer = None

    def setup(self) -> None:
        """Setup pipeline components"""
        logger.info("Setting up data pipeline...")

        # Create data fetcher
        self.data_fetcher = create_data_fetcher(self.username, self.password)

        # Create feature engineer
        self.feature_engineer = create_feature_engineer(self.data_fetcher.client)

        logger.info("Data pipeline setup completed")

    def run_data_pipeline(
        self,
        config: Dict[str, Any],
        save_intermediate: bool = True
    ) -> pd.DataFrame:
        """Run complete data processing pipeline

        Args:
            config: Configuration dictionary
            save_intermediate: Whether to save intermediate results

        Returns:
            Processed dataset with features and labels
        """
        logger.info("Starting data pipeline...")

        # Setup if not done
        if self.data_fetcher is None:
            self.setup()

        # Step 1: Fetch raw data
        logger.info("Step 1: Fetching raw data...")
        raw_data = self.data_fetcher.prepare_dataset(config, save_raw=True)

        if save_intermediate:
            raw_path = "data/raw/trading_data.csv"
            raw_data.to_csv(raw_path, index=False)
            logger.info(f"Saved raw data to {raw_path}")

        # Step 2: Apply triple-barrier labeling
        logger.info("Step 2: Applying triple-barrier labeling...")
        labeled_data = apply_triple_barrier_labeling(raw_data, config)

        # Analyze labeling quality
        labeling_quality = analyze_labeling_quality(labeled_data, config)
        logger.info(f"Labeling quality metrics: {labeling_quality}")

        if save_intermediate:
            labeled_path = "data/processed/labeled_data.csv"
            Path(labeled_path).parent.mkdir(parents=True, exist_ok=True)
            labeled_data.to_csv(labeled_path, index=False)
            logger.info(f"Saved labeled data to {labeled_path}")

        # Step 3: Feature engineering
        logger.info("Step 3: Engineering features...")
        featured_data = self.feature_engineer.engineer_features(labeled_data, config)

        if save_intermediate:
            featured_path = "data/processed/featured_data.csv"
            featured_data.to_csv(featured_path, index=False)
            logger.info(f"Saved featured data to {featured_path}")

        # Step 4: Data cleaning and validation
        logger.info("Step 4: Cleaning and validating data...")
        final_data = self.clean_and_validate_data(featured_data)

        # Save final dataset
        final_path = "data/final/final_dataset.csv"
        Path(final_path).parent.mkdir(parents=True, exist_ok=True)
        final_data.to_csv(final_path, index=False)
        logger.info(f"Saved final dataset to {final_path}")

        logger.info("Data pipeline completed successfully")
        return final_data

    def clean_and_validate_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """Clean and validate processed data

        Args:
            data: Processed data with features and labels

        Returns:
            Cleaned dataset
        """
        logger.info("Cleaning and validating data...")

        initial_rows = len(data)

        # Remove rows without labels
        data = data.dropna(subset=['label'])
        logger.info(f"Removed {initial_rows - len(data)} rows without labels")

        # Get feature columns
        feature_cols = self.feature_engineer.get_feature_list(data)

        # Remove rows with too many missing features
        missing_threshold = 0.5  # Remove rows with >50% missing features
        missing_counts = data[feature_cols].isnull().sum(axis=1)
        valid_rows = missing_counts <= (len(feature_cols) * missing_threshold)
        data = data[valid_rows]

        removed_rows = initial_rows - len(data)
        logger.info(f"Removed {removed_rows} rows with excessive missing values")

        # Fill remaining missing values
        for col in feature_cols:
            if data[col].isnull().any():
                if data[col].dtype in ['float64', 'int64']:
                    # Fill numeric columns with median
                    data[col] = data[col].fillna(data[col].median())
                else:
                    # Fill categorical columns with mode
                    data[col] = data[col].fillna(data[col].mode().iloc[0] if not data[col].mode().empty else 0)

        # Remove infinite values
        for col in feature_cols:
            if data[col].dtype in ['float64', 'int64']:
                data[col] = data[col].replace([float('inf'), float('-inf')], data[col].median())

        logger.info(f"Final dataset: {len(data)} rows, {len(feature_cols)} features")

        # Data quality summary
        label_distribution = data['label'].value_counts().sort_index()
        logger.info(f"Label distribution: {dict(label_distribution)}")

        return data

    def split_data(
        self,
        data: pd.DataFrame,
        config: Dict[str, Any]
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Split data into train/validation/test sets

        Args:
            data: Complete dataset
            config: Configuration with split ratios

        Returns:
            Tuple of (train_data, val_data, test_data)
        """
        splits_config = config.get('data', {}).get('splits', {})
        train_ratio = splits_config.get('train_ratio', 0.6)
        val_ratio = splits_config.get('validation_ratio', 0.2)

        # Sort by timestamp for time-based splitting
        if 'timestamp' in data.columns:
            data = data.sort_values('timestamp')

        n = len(data)
        train_end = int(n * train_ratio)
        val_end = int(n * (train_ratio + val_ratio))

        train_data = data.iloc[:train_end]
        val_data = data.iloc[train_end:val_end]
        test_data = data.iloc[val_end:]

        logger.info(f"Data split - Train: {len(train_data)}, Val: {len(val_data)}, Test: {len(test_data)}")

        # Save splits
        splits_dir = Path("data/final")
        splits_dir.mkdir(parents=True, exist_ok=True)

        train_data.to_csv(splits_dir / "train_data.csv", index=False)
        val_data.to_csv(splits_dir / "val_data.csv", index=False)
        test_data.to_csv(splits_dir / "test_data.csv", index=False)

        logger.info("Data splits saved")

        return train_data, val_data, test_data


def run_data_pipeline(
    username: str,
    password: str,
    data_config_path: str = "config/data_config.yaml",
    labeling_config_path: str = "config/labeling_config.yaml"
) -> pd.DataFrame:
    """Run data pipeline with configuration files

    Args:
        username: FiinQuantX username
        password: FiinQuantX password
        data_config_path: Path to data configuration
        labeling_config_path: Path to labeling configuration

    Returns:
        Processed dataset
    """
    # Load configurations
    data_config = config_loader.load_config("data_config")
    labeling_config = config_loader.load_config("labeling_config")

    # Combine configs
    combined_config = {**data_config, **labeling_config}

    # Create and run pipeline
    pipeline = DataPipeline(username, password)

    # Run complete pipeline
    final_data = pipeline.run_data_pipeline(combined_config)

    # Split data
    train_data, val_data, test_data = pipeline.split_data(final_data, combined_config)

    return final_data


if __name__ == "__main__":
    # Example usage
    import os

    username = os.getenv("FIIN_USERNAME", "YOUR_USERNAME")
    password = os.getenv("FIIN_PASSWORD", "YOUR_PASSWORD")

    if username == "YOUR_USERNAME":
        logger.error("Please set FIIN_USERNAME and FIIN_PASSWORD environment variables")
    else:
        final_data = run_data_pipeline(username, password)
        logger.info(f"Pipeline completed with {len(final_data)} samples")
