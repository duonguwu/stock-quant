"""Backtest runner and report generator"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import json
from loguru import logger

from .backtest_engine import create_backtest_engine, BacktestResults


class BacktestRunner:
    """Runner for backtesting with reporting"""

    def __init__(self, model_path: str = "models/xgboost_model.pkl",
                 scaler_path: str = "models/feature_scaler.pkl"):
        """Initialize backtest runner

        Args:
            model_path: Path to trained model
            scaler_path: Path to feature scaler
        """
        self.engine = create_backtest_engine(model_path, scaler_path)
        self.results = None

    def run_backtest(
        self,
        test_data_path: str = "data/final/custom_test_data.csv",
        confidence_threshold: float = 0.6,
        holding_period: int = 10,
        transaction_cost: float = 0.001,
        benchmark_ticker: str = "^VNI"
    ) -> BacktestResults:
        """Run backtest on test data

        Args:
            test_data_path: Path to test data CSV
            confidence_threshold: Minimum confidence for trades
            holding_period: Maximum holding period
            transaction_cost: Transaction cost percentage
            benchmark_ticker: Benchmark ticker

        Returns:
            BacktestResults object
        """
        logger.info(f"Loading test data from {test_data_path}")
        test_data = pd.read_csv(test_data_path)

        # Ensure timestamp is datetime
        test_data['timestamp'] = pd.to_datetime(test_data['timestamp'])

        # Run backtest
        self.results = self.engine.run_backtest(
            test_data=test_data,
            confidence_threshold=confidence_threshold,
            holding_period=holding_period,
            transaction_cost=transaction_cost,
            benchmark_ticker=benchmark_ticker
        )

        return self.results

    def generate_report(self, output_dir: str = "results/backtest") -> None:
        """Generate comprehensive backtest report

        Args:
            output_dir: Directory to save report files
        """
        if self.results is None:
            raise ValueError(
                "No backtest results available. Run backtest first."
            )

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Generate text summary
        self._generate_summary_report(output_path)

        # Generate visualizations
        self._generate_charts(output_path)

        # Save detailed data
        self._save_detailed_data(output_path)

        logger.info(f"Backtest report saved to {output_path}")

    def _generate_summary_report(self, output_path: Path) -> None:
        """Generate text summary report"""
        results = self.results

        summary = f"""
# BACKTEST RESULTS SUMMARY

## Performance Overview
- **Tổng Return**: {results.total_return:.2%}
- **Return Hàng Năm**: {results.annualized_return:.2%}
- **Volatility**: {results.volatility:.2%}
- **Sharpe Ratio**: {results.sharpe_ratio:.3f}
- **Max Drawdown**: {results.max_drawdown:.2%}

## Trading Statistics
- **Tổng Số Giao Dịch**: {results.total_trades:,}
- **Giao Dịch Thắng**: {results.winning_trades:,}
- **Giao Dịch Thua**: {results.losing_trades:,}
- **Tỷ Lệ Thắng**: {results.win_rate:.2%}
- **Avg Win**: {results.avg_win:.2%}
- **Avg Loss**: {results.avg_loss:.2%}
- **Profit Factor**: {results.profit_factor:.2f}

## Benchmark Comparison (VN-Index)
- **Benchmark Return**: {results.benchmark_return:.2%}
- **Excess Return**: {results.excess_return:.2%}
- **Beta**: {results.beta:.3f}
- **Alpha**: {results.alpha:.4f}

## Signal Distribution
"""

        # Add signal analysis
        if results.trades:
            buy_trades = len([t for t in results.trades if t.signal == 1])
            sell_trades = len([t for t in results.trades if t.signal == -1])

            summary += (
                f"- **Buy Signals**: {buy_trades:,} "
                f"({buy_trades/results.total_trades:.1%})\n"
            )
            summary += (
                f"- **Sell Signals**: {sell_trades:,} "
                f"({sell_trades/results.total_trades:.1%})\n\n"
            )
            summary += "## Average Metrics by Signal Type\n"

            buy_returns = [
                t.return_pct for t in results.trades if t.signal == 1
            ]
            sell_returns = [
                t.return_pct for t in results.trades if t.signal == -1
            ]

            if buy_returns:
                avg_buy = sum(buy_returns) / len(buy_returns)
                summary += f"- **Avg Buy Return**: {avg_buy:.2%}\n"
            if sell_returns:
                avg_sell = sum(sell_returns) / len(sell_returns)
                summary += f"- **Avg Sell Return**: {avg_sell:.2%}\n"

        # Save summary
        with open(
            output_path / "backtest_summary.md", "w", encoding="utf-8"
        ) as f:
            f.write(summary)

        # Save metrics as JSON
        metrics = {
            "performance": {
                "total_return": results.total_return,
                "annualized_return": results.annualized_return,
                "volatility": results.volatility,
                "sharpe_ratio": results.sharpe_ratio,
                "max_drawdown": results.max_drawdown,
            },
            "trading": {
                "total_trades": results.total_trades,
                "winning_trades": results.winning_trades,
                "losing_trades": results.losing_trades,
                "win_rate": results.win_rate,
                "avg_win": results.avg_win,
                "avg_loss": results.avg_loss,
                "profit_factor": results.profit_factor,
            },
            "benchmark": {
                "benchmark_return": results.benchmark_return,
                "excess_return": results.excess_return,
                "beta": results.beta,
                "alpha": results.alpha,
            },
        }

        with open(output_path / "backtest_metrics.json", "w") as f:
            json.dump(metrics, f, indent=2)

    def _generate_charts(self, output_path: Path) -> None:
        """Generate visualization charts"""
        if not self.results.trades:
            logger.warning("No trades to visualize")
            return

        plt.style.use('default')
        plt.figure(figsize=(16, 12))

        # 1. Equity Curve
        plt.subplot(2, 3, 1)
        if not self.results.equity_curve.empty:
            plt.plot(
                pd.to_datetime(self.results.equity_curve['date']),
                self.results.equity_curve['equity'],
            )
            plt.title('Equity Curve')
            plt.xlabel('Date')
            plt.ylabel('Equity')
            plt.xticks(rotation=45)

        # 2. Drawdown
        plt.subplot(2, 3, 2)
        if not self.results.drawdown_curve.empty:
            plt.fill_between(
                pd.to_datetime(self.results.drawdown_curve['date']),
                self.results.drawdown_curve['drawdown'],
                0,
                color='red',
                alpha=0.3,
            )
            plt.title('Drawdown')
            plt.xlabel('Date')
            plt.ylabel('Drawdown')
            plt.xticks(rotation=45)

        # 3. Return Distribution
        plt.subplot(2, 3, 3)
        returns = [t.return_pct for t in self.results.trades]
        plt.hist(returns, bins=30, alpha=0.7, edgecolor='black')
        plt.title('Return Distribution')
        plt.xlabel('Return (%)')
        plt.ylabel('Frequency')
        plt.axvline(x=0, color='red', linestyle='--', alpha=0.7)

        # 4. Signal Performance
        plt.subplot(2, 3, 4)
        buy_returns = [
            t.return_pct for t in self.results.trades if t.signal == 1
        ]
        sell_returns = [
            t.return_pct for t in self.results.trades if t.signal == -1
        ]

        if buy_returns and sell_returns:
            plt.boxplot([buy_returns, sell_returns], labels=['Buy', 'Sell'])
            plt.title('Return by Signal Type')
            plt.ylabel('Return (%)')
            plt.axhline(y=0, color='red', linestyle='--', alpha=0.7)

        # 5. Monthly Returns Heatmap
        plt.subplot(2, 3, 5)
        if self.results.equity_curve.shape[0] > 0:
            monthly_returns = self._calculate_monthly_returns()
            if not monthly_returns.empty:
                sns.heatmap(
                    monthly_returns, annot=True, fmt='.1%', cmap='RdYlGn', center=0
                )
                plt.title('Monthly Returns')

        # 6. Win Rate by Confidence
        plt.subplot(2, 3, 6)
        confidence_bins = [0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
        win_rates = []

        for i in range(len(confidence_bins) - 1):
            low, high = confidence_bins[i], confidence_bins[i + 1]
            filtered_trades = [
                t for t in self.results.trades if low <= t.confidence < high
            ]
            if filtered_trades:
                wins = sum(1 for t in filtered_trades if t.return_pct > 0)
                win_rate = wins / len(filtered_trades)
                win_rates.append(win_rate)
            else:
                win_rates.append(0)

        if win_rates:
            plt.bar(range(len(win_rates)), win_rates)
            plt.title('Win Rate by Confidence')
            plt.xlabel('Confidence Range')
            plt.ylabel('Win Rate')
            plt.xticks(
                range(len(win_rates)),
                [
                    f"{confidence_bins[i]:.1f}-{confidence_bins[i+1]:.1f}"
                    for i in range(len(confidence_bins) - 1)
                ],
                rotation=45,
            )

        plt.tight_layout()
        plt.savefig(
            output_path / "backtest_charts.png", dpi=300, bbox_inches='tight'
        )
        plt.close()

        logger.info("Charts saved successfully")

    def _calculate_monthly_returns(self) -> pd.DataFrame:
        """Calculate monthly returns for heatmap"""
        if self.results.equity_curve.empty:
            return pd.DataFrame()

        equity_curve = self.results.equity_curve.copy()
        equity_curve['date'] = pd.to_datetime(equity_curve['date'])
        equity_curve = equity_curve.set_index('date')

        # Resample to monthly
        monthly_equity = equity_curve['equity'].resample('M').last()
        monthly_returns = monthly_equity.pct_change().dropna()

        # Create pivot table for heatmap
        monthly_returns.index = pd.to_datetime(monthly_returns.index)
        monthly_df = pd.DataFrame({
            'Year': monthly_returns.index.year,
            'Month': monthly_returns.index.month,
            'Return': monthly_returns.values
        })

        if len(monthly_df) == 0:
            return pd.DataFrame()

        pivot_table = monthly_df.pivot(
            index='Year', columns='Month', values='Return'
        )

        # Rename columns to month names
        month_names = [
            'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
            'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
        ]
        pivot_table.columns = [
            month_names[int(col) - 1] if col <= 12 else f'M{col}'
            for col in pivot_table.columns
        ]

        return pivot_table

    def _save_detailed_data(self, output_path: Path) -> None:
        """Save detailed trade data"""
        if not self.results.trades:
            return

        # Save trades data
        trades_data = []
        for trade in self.results.trades:
            trades_data.append({
                'entry_date': trade.entry_date,
                'exit_date': trade.exit_date,
                'ticker': trade.ticker,
                'signal': trade.signal,
                'signal_name': {1: 'Buy', -1: 'Sell'}.get(
                    trade.signal, 'Unknown'
                ),
                'entry_price': trade.entry_price,
                'exit_price': trade.exit_price,
                'return_pct': trade.return_pct,
                'holding_days': trade.holding_days,
                'confidence': trade.confidence
            })

        trades_df = pd.DataFrame(trades_data)
        trades_df.to_csv(output_path / "detailed_trades.csv", index=False)

        # Save equity curve
        if not self.results.equity_curve.empty:
            self.results.equity_curve.to_csv(
                output_path / "equity_curve.csv", index=False
            )

        # Save drawdown curve
        if not self.results.drawdown_curve.empty:
            self.results.drawdown_curve.to_csv(
                output_path / "drawdown_curve.csv", index=False
            )

    def print_summary(self) -> None:
        """Print quick summary to console"""
        if self.results is None:
            print("No backtest results available")
            return

        print("\n" + "=" * 60)
        print("📊 BACKTEST RESULTS SUMMARY")
        print("=" * 60)
        print(f"💰 Total Return: {self.results.total_return:.2%}")
        print(f"📈 Annualized Return: {self.results.annualized_return:.2%}")
        print(f"📉 Max Drawdown: {self.results.max_drawdown:.2%}")
        print(f"📊 Sharpe Ratio: {self.results.sharpe_ratio:.3f}")
        print(f"🎯 Total Trades: {self.results.total_trades:,}")
        print(f"✅ Win Rate: {self.results.win_rate:.2%}")
        print(f"🏆 Profit Factor: {self.results.profit_factor:.2f}")
        print(f"📊 VN-Index Return: {self.results.benchmark_return:.2%}")
        print(f"💎 Excess Return: {self.results.excess_return:.2%}")
        print("=" * 60)


def run_backtest_analysis(
    model_path: str = "models/xgboost_model.pkl",
    scaler_path: str = "models/feature_scaler.pkl",
    test_data_path: str = "data/final/custom_test_data.csv",
    confidence_threshold: float = 0.6,
    output_dir: str = "results/backtest"
) -> BacktestResults:
    """Run complete backtest analysis

    Args:
        model_path: Path to trained model
        scaler_path: Path to feature scaler
        test_data_path: Path to test data
        confidence_threshold: Minimum confidence threshold
        output_dir: Output directory for reports

    Returns:
        BacktestResults object
    """
    logger.info("Starting backtest analysis...")

    # Create runner
    runner = BacktestRunner(model_path, scaler_path)

    # Run backtest
    results = runner.run_backtest(
        test_data_path=test_data_path,
        confidence_threshold=confidence_threshold
    )

    # Generate reports
    runner.generate_report(output_dir)

    # Print summary
    runner.print_summary()

    logger.info("Backtest analysis completed")
    return results


if __name__ == "__main__":
    # Run backtest with default parameters
    results = run_backtest_analysis()
