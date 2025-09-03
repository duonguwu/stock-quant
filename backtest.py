#!/usr/bin/env python3
"""
Stock Signal Backtesting Script

Run backtesting on trained model with comprehensive analysis
"""

import argparse
from pathlib import Path
from datetime import datetime
from loguru import logger
from src.backtesting.backtest_runner import run_backtest_analysis


def _get_next_output_dir(base_dir: Path) -> Path:
    """Return next available backtest_N directory under base_dir."""
    base_dir.mkdir(parents=True, exist_ok=True)
    n = 1
    while True:
        candidate = base_dir / f"backtest_{n}"
        if not candidate.exists():
            candidate.mkdir(parents=True, exist_ok=True)
            return candidate
        n += 1


def _write_run_config(output_dir: Path, args: argparse.Namespace) -> None:
    """Write run configuration into config.md in output directory."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        "# Backtest Run Configuration\n\n",
        f"- Model: {args.model}\n",
        f"- Scaler: {args.scaler}\n",
        f"- Test data: {args.test_data}\n",
        f"- Confidence: {args.confidence}\n",
        f"- Holding period: {args.holding_period}\n",
        f"- Transaction cost: {args.transaction_cost}\n",
        f"- Created at: {ts}\n",
    ]
    (output_dir / "config.md").write_text("".join(lines), encoding="utf-8")


def main():
    """Main function for backtesting"""
    parser = argparse.ArgumentParser(
        description="Stock Signal Backtesting",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            """
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
        ),
    )

    parser.add_argument(
        "--model",
        default="models/model1822/xgboost_model.pkl",
        help=(
            "Path to trained model file "
            "(default: models/model1620/xgboost_model.pkl)"
        ),
    )

    parser.add_argument(
        "--scaler",
        default="models/model1822/feature_scaler.pkl",
        help=(
            "Path to feature scaler file "
            "(default: models/model1721/feature_scaler.pkl)"
        ),
    )

    parser.add_argument(
        "--test-data",
        default="data/backtest_data/data_23_sideway.csv",
        help=(
            "Path to test data CSV "
            "(default: data/backtest_data/data_21_up.csv)"
        ),
    )

    parser.add_argument(
        "--confidence",
        type=float,
        default=0.6,
        help=(
            "Minimum confidence threshold for signals "
            "(default: 0.6)"
        ),
    )

    parser.add_argument(
        "--output",
        default="results/backtest",
        help=(
            "Base output directory for results "
            "(default: results/backtest)"
        ),
    )

    parser.add_argument(
        "--holding-period",
        type=int,
        default=10,
        help="Maximum holding period in days (default: 10)",
    )

    parser.add_argument(
        "--transaction-cost",
        type=float,
        default=0.001,
        help=(
            "Transaction cost as percentage "
            "(default: 0.001 = 0.1%)"
        ),
    )

    args = parser.parse_args()

    # Setup logging
    logger.add(
        "logs/backtest.log",
        rotation="10 MB",
        retention="7 days",
        level="INFO",
    )

    try:
        # Check if required files exist
        if not Path(args.model).exists():
            logger.error(f"Model file not found: {args.model}")
            logger.info(
                "Please train the model first by running: python main.py"
            )
            return 1

        if not Path(args.scaler).exists():
            logger.error(f"Scaler file not found: {args.scaler}")
            logger.info(
                "Please train the model first by running: python main.py"
            )
            return 1

        if not Path(args.test_data).exists():
            logger.error(f"Test data not found: {args.test_data}")
            logger.info(
                "Please generate test data first by running: "
                "python main.py --data-only"
            )
            return 1

        # Choose unique output directory results/backtest/backtest_N
        base_output = Path(args.output)
        unique_output = _get_next_output_dir(base_output)

        # Run backtest analysis (ignore return value)
        logger.info("🚀 Starting Stock Signal Backtesting")
        logger.info(f"Model: {args.model}")
        logger.info(f"Test Data: {args.test_data}")
        logger.info(f"Confidence Threshold: {args.confidence}")
        logger.info(f"Output base: {base_output}")
        logger.info(f"Output unique: {unique_output}")

        run_backtest_analysis(
            model_path=args.model,
            scaler_path=args.scaler,
            test_data_path=args.test_data,
            confidence_threshold=args.confidence,
            output_dir=str(unique_output),
        )

        # Write configuration used
        _write_run_config(unique_output, args)

        logger.info("✅ Backtesting completed successfully!")
        logger.info(f"📁 Results saved to: {unique_output}")
        logger.info(
            f"📊 Summary: {unique_output / 'backtest_summary.md'}"
        )
        logger.info(
            f"📈 Charts: {unique_output / 'backtest_charts.png'}"
        )

        return 0

    except Exception as e:
        logger.error(f"❌ Backtesting failed: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
