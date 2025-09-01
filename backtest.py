#!/usr/bin/env python3
"""
Stock Signal Backtesting Script

Run backtesting on trained model with comprehensive analysis
"""

import argparse
from pathlib import Path
from loguru import logger
from src.backtesting.backtest_runner import run_backtest_analysis


def main():
    """Main function for backtesting"""
    parser = argparse.ArgumentParser(
        description="Stock Signal Backtesting",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run backtest with default settings
  python backtest.py

  # Run with custom confidence threshold
  python backtest.py --confidence 0.7

  # Use custom model path
  python backtest.py --model models/xgboost_model.pkl

  # Save results to custom directory
  python backtest.py --output results/my_backtest
        """
    )

    parser.add_argument(
        "--model",
        default="models/xgboost_model.pkl",
        help="Path to trained model file (default: models/xgboost_model.pkl)"
    )

    parser.add_argument(
        "--scaler", 
        default="models/feature_scaler.pkl",
        help="Path to feature scaler file (default: models/feature_scaler.pkl)"
    )

    parser.add_argument(
        "--test-data",
        default="data/final/test_data.csv",
        help="Path to test data CSV (default: data/final/test_data.csv)"
    )

    parser.add_argument(
        "--confidence",
        type=float,
        default=0.6,
        help="Minimum confidence threshold for signals (default: 0.6)"
    )

    parser.add_argument(
        "--output",
        default="results/backtest",
        help="Output directory for results (default: results/backtest)"
    )

    parser.add_argument(
        "--holding-period",
        type=int,
        default=10,
        help="Maximum holding period in days (default: 10)"
    )

    parser.add_argument(
        "--transaction-cost",
        type=float,
        default=0.001,
        help="Transaction cost as percentage (default: 0.001 = 0.1%)"
    )

    args = parser.parse_args()

    # Setup logging
    logger.add(
        "logs/backtest.log",
        rotation="10 MB",
        retention="7 days",
        level="INFO"
    )

    try:
        # Check if required files exist
        if not Path(args.model).exists():
            logger.error(f"Model file not found: {args.model}")
            logger.info("Please train the model first by running: python main.py")
            return 1

        if not Path(args.scaler).exists():
            logger.error(f"Scaler file not found: {args.scaler}")
            logger.info("Please train the model first by running: python main.py")
            return 1

        if not Path(args.test_data).exists():
            logger.error(f"Test data not found: {args.test_data}")
            logger.info("Please generate test data first by running: python main.py --data-only")
            return 1

        # Run backtest analysis
        logger.info("🚀 Starting Stock Signal Backtesting")
        logger.info(f"Model: {args.model}")
        logger.info(f"Test Data: {args.test_data}")
        logger.info(f"Confidence Threshold: {args.confidence}")
        logger.info(f"Output: {args.output}")

        results = run_backtest_analysis(
            model_path=args.model,
            scaler_path=args.scaler,
            test_data_path=args.test_data,
            confidence_threshold=args.confidence,
            output_dir=args.output
        )

        logger.info("✅ Backtesting completed successfully!")
        logger.info(f"📁 Results saved to: {args.output}")
        logger.info(f"📊 Summary: {Path(args.output) / 'backtest_summary.md'}")
        logger.info(f"📈 Charts: {Path(args.output) / 'backtest_charts.png'}")

        return 0

    except Exception as e:
        logger.error(f"❌ Backtesting failed: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
