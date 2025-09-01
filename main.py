#!/usr/bin/env python3
"""
Stock Signal Classification Main Entry Point

Run complete pipeline from data fetching to model training.
"""

import os
import argparse
from pathlib import Path
from loguru import logger
from dotenv import load_dotenv

from src.pipeline.data_pipeline import run_data_pipeline
from src.pipeline.training_pipeline import run_training_pipeline
from src.utils.config_loader import config_loader


def setup_logging(log_level: str = "INFO") -> None:
    """Setup logging configuration"""
    logger.remove()  # Remove default handler
    logger.add(
        "logs/pipeline.log",
        rotation="10 MB",
        retention="7 days",
        level=log_level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}"
    )
    logger.add(
        lambda msg: print(msg, end=""),
        level=log_level,
        format="<green>{time:HH:mm:ss}</green> | <level>{level}</level> | {message}"
    )


def check_credentials() -> tuple[str, str]:
    """Check and get FiinQuantX credentials"""
    # Load .env file
    load_dotenv()

    username = os.getenv("FIIN_USERNAME")
    password = os.getenv("FIIN_PASSWORD")

    if not username or not password:
        logger.error("FiinQuantX credentials not found!")
        logger.info("Please create a .env file with:")
        logger.info("  FIIN_USERNAME=your_username")
        logger.info("  FIIN_PASSWORD=your_password")
        logger.info("Or copy env.example to .env and edit it")
        raise ValueError("Missing FiinQuantX credentials")

    return username, password


def run_complete_pipeline(
    username: str,
    password: str,
    data_only: bool = False,
    training_only: bool = False
) -> None:
    """Run complete pipeline from data to training

    Args:
        username: FiinQuantX username
        password: FiinQuantX password
        data_only: Run only data pipeline
        training_only: Run only training pipeline (requires existing data)
    """
    logger.info("=" * 60)
    logger.info("🚀 Stock Signal Classification Pipeline")
    logger.info("=" * 60)

    # Create directories
    for directory in ["data/raw", "data/processed", "data/final", "models", "results", "logs"]:
        Path(directory).mkdir(parents=True, exist_ok=True)

    try:
        if not training_only:
            # Run data pipeline
            logger.info("📊 Phase 1: Data Pipeline")
            logger.info("-" * 30)

            final_data = run_data_pipeline(username, password)

            logger.info(f"✅ Data pipeline completed with {len(final_data)} samples")

            if data_only:
                logger.info("Data-only mode: stopping after data pipeline")
                return

        # Run training pipeline
        logger.info("🤖 Phase 2: Model Training")
        logger.info("-" * 30)

        results = run_training_pipeline()

        # Display results
        logger.info("✅ Training completed successfully!")
        logger.info("📈 Model Performance:")
        logger.info(f"  Accuracy: {results['evaluation']['accuracy']:.4f}")
        logger.info(f"  Macro F1: {results['evaluation']['macro_f1']:.4f}")

        # Feature importance (top 10)
        if results['evaluation']['feature_importance']:
            logger.info("🎯 Top 10 Important Features:")
            for i, feat in enumerate(results['evaluation']['feature_importance'][:10]):
                logger.info(f"  {i+1:2d}. {feat['feature']}: {feat['importance']:.4f}")

        logger.info("=" * 60)
        logger.info("✨ Pipeline completed successfully!")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"❌ Pipeline failed: {e}")
        raise


def main():
    """Main function with argument parsing"""
    parser = argparse.ArgumentParser(
        description="Stock Signal Classification Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run complete pipeline
  python main.py

  # Run only data pipeline
  python main.py --data-only

  # Run only training (requires existing data)
  python main.py --training-only

  # Debug mode with verbose logging
  python main.py --log-level DEBUG

Environment Variables:
  FIIN_USERNAME    FiinQuantX username
  FIIN_PASSWORD    FiinQuantX password
        """
    )

    parser.add_argument(
        "--data-only",
        action="store_true",
        help="Run only data pipeline (skip training)"
    )

    parser.add_argument(
        "--training-only",
        action="store_true",
        help="Run only training pipeline (requires existing processed data)"
    )

    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Set logging level (default: INFO)"
    )

    parser.add_argument(
        "--config-dir",
        default="config",
        help="Configuration directory (default: config)"
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.log_level)

    try:
        # Check credentials (skip for training-only mode if using saved data)
        if not args.training_only:
            username, password = check_credentials()
        else:
            username, password = None, None

        # Validate configurations
        logger.info("📋 Validating configurations...")

        # Check if config files exist
        config_files = ["data_config.yaml", "labeling_config.yaml", "model_config.yaml"]
        config_dir = Path(args.config_dir)

        for config_file in config_files:
            config_path = config_dir / config_file
            if not config_path.exists():
                logger.warning(f"Config file not found: {config_path}")

        # Load and validate configs
        try:
            if not args.training_only:
                data_config = config_loader.load_config("data_config")
                labeling_config = config_loader.load_config("labeling_config")
                logger.info("✅ Data and labeling configs loaded")

            model_config = config_loader.load_config("model_config")
            logger.info("✅ Model config loaded")
        except FileNotFoundError as e:
            logger.error(f"❌ Configuration error: {e}")
            logger.info("Please ensure all configuration files exist in the config directory")
            return 1

        # Run pipeline
        run_complete_pipeline(
            username=username,
            password=password,
            data_only=args.data_only,
            training_only=args.training_only
        )

        return 0

    except KeyboardInterrupt:
        logger.warning("⚠️ Pipeline interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"❌ Pipeline failed: {e}")
        if args.log_level == "DEBUG":
            import traceback
            logger.error(traceback.format_exc())
        return 1


if __name__ == "__main__":
    exit(main())
