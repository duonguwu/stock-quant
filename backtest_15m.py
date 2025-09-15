#!/usr/bin/env python3
"""
Stock Signal Backtesting Script for 15-minute timeframe

Run backtesting on trained 15m model with comprehensive analysis
"""

import argparse
from pathlib import Path
from datetime import datetime
from loguru import logger
from src.backtesting.backtest_runner_15m import run_backtest_analysis_15m


def _get_next_output_dir(base_dir: Path) -> Path:
    """Return next available backtest_15m_N directory under base_dir."""
    base_dir.mkdir(parents=True, exist_ok=True)
    n = 1
    while True:
        candidate = base_dir / f"backtest_15m_{n}"
        if not candidate.exists():
            candidate.mkdir(parents=True, exist_ok=True)
            return candidate
        n += 1


def _write_run_config_15m(output_dir: Path, args: argparse.Namespace) -> None:
    """Write 15m run configuration into config.md in output directory."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        "# 15-Minute Backtest Run Configuration\n\n",
        f"- Timeframe: 15-minute bars\n",
        f"- Model: {args.model}\n",
        f"- Scaler: {args.scaler}\n",
        f"- Test data: {args.test_data}\n",
        f"- Confidence: {args.confidence}\n",
        f"- Holding period: {args.holding_period_bars} bars (~{args.holding_period_bars/18:.1f} days)\n",
        f"- Transaction cost: {args.transaction_cost} (optimized for 15m)\n",
        f"- Created at: {ts}\n",
    ]
    (output_dir / "config_15m.md").write_text("".join(lines), encoding="utf-8")


def main():
    """Main function for 15m backtesting"""
    parser = argparse.ArgumentParser(
        description="Stock Signal Backtesting for 15-minute timeframe",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            """
Examples:
  # Run 15m backtest with default settings
  python backtest_15m.py

  # Run with custom confidence threshold
  python backtest_15m.py --confidence 0.7

  # Use custom 15m model path
  python backtest_15m.py --model models/xgboost_model_15m.pkl

  # Save results to custom directory
  python backtest_15m.py --output results/my_backtest_15m

  # Custom holding period (in 15m bars)
  python backtest_15m.py --holding-period-bars 72  # ~4 trading days
"""
        ),
    )

    parser.add_argument(
        "--model",
        default="models/model15/xgboost_model.pkl",
        help=(
            "Path to trained 15m model file "
            "(default: models/xgboost_model_15m.pkl)"
        ),
    )

    parser.add_argument(
        "--scaler",
        default="models/model15/feature_scaler.pkl",
        help=(
            "Path to 15m feature scaler file "
            "(default: models/feature_scaler_15m.pkl)"
        ),
    )

    parser.add_argument(
        "--test-data",
        default="data/backtest_data/chart_15m_new.csv",
        help=(
            "Path to 15m test data CSV "
            "(default: data/backtest_data/chart_15m_new.csv)"
        ),
    )

    parser.add_argument(
        "--confidence",
        type=float,
        default=0.65,  # Higher for 15m to reduce noise
        help=(
            "Minimum confidence threshold for signals "
            "(default: 0.65, higher than daily due to 15m noise)"
        ),
    )

    parser.add_argument(
        "--output",
        default="results/backtest_15m",
        help=(
            "Base output directory for 15m results "
            "(default: results/backtest_15m)"
        ),
    )

    parser.add_argument(
        "--holding-period-bars",
        type=int,
        default=36,  # ~2 trading days for 15m
        help=(
            "Maximum holding period in 15m bars "
            "(default: 36 bars ≈ 2 trading days)"
        ),
    )

    parser.add_argument(
        "--transaction-cost",
        type=float,
        default=0.0005,  # Lower for 15m frequency
        help=(
            "Transaction cost as percentage "
            "(default: 0.0005 = 0.05%, lower than daily)"
        ),
    )

    args = parser.parse_args()

    # Setup logging for 15m
    logger.add(
        "logs/backtest_15m.log",
        rotation="10 MB",
        retention="7 days",
        level="INFO",
    )

    try:
        # Check if required 15m files exist
        if not Path(args.model).exists():
            logger.error(f"15m model file not found: {args.model}")
            logger.info(
                "Please train the 15m model first by running: "
                "python main.py --config-dir config/15m"
            )
            return 1

        if not Path(args.scaler).exists():
            logger.error(f"15m scaler file not found: {args.scaler}")
            logger.info(
                "Please train the 15m model first by running: "
                "python main.py --config-dir config/15m"
            )
            return 1

        if not Path(args.test_data).exists():
            logger.error(f"15m test data not found: {args.test_data}")
            logger.info(
                "Please generate 15m test data first by running: "
                "python run_custom_backtest_15m.py"
            )
            return 1

        # Choose unique output directory results/backtest_15m/backtest_15m_N
        base_output = Path(args.output)
        unique_output = _get_next_output_dir(base_output)

        # Run 15m backtest analysis
        logger.info("🚀 Starting 15-Minute Stock Signal Backtesting")
        logger.info(f"Model: {args.model}")
        logger.info(f"Test Data: {args.test_data}")
        logger.info(f"Confidence Threshold: {args.confidence}")
        logger.info(f"Holding Period: {args.holding_period_bars} bars (~{args.holding_period_bars/18:.1f} days)")
        logger.info(f"Transaction Cost: {args.transaction_cost:.4f}")
        logger.info(f"Output: {unique_output}")

        run_backtest_analysis_15m(
            model_path=args.model,
            scaler_path=args.scaler,
            test_data_path=args.test_data,
            confidence_threshold=args.confidence,
            holding_period_bars=args.holding_period_bars,
            output_dir=str(unique_output),
        )

        # Write configuration used
        _write_run_config_15m(unique_output, args)

        logger.info("✅ 15m backtesting completed successfully!")
        logger.info(f"📁 Results saved to: {unique_output}")
        logger.info(
            f"📊 Summary: {unique_output / 'backtest_summary_15m.md'}"
        )
        logger.info(
            f"📈 Charts: {unique_output / 'backtest_charts_15m.png'}"
        )

        return 0

    except Exception as e:
        logger.error(f"❌ 15m backtesting failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 1


if __name__ == "__main__":
    exit(main()) 