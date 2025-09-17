"""Backtest runner and report generator for 15-minute timeframe"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from pathlib import Path
import json
from loguru import logger

from .backtest_engine_15m import create_backtest_engine_15m, BacktestResults15m


class BacktestRunner15m:
    """Runner for 15m backtesting with reporting"""

    def __init__(self, model_path: str = "models/xgboost_model_15m.pkl",
                 scaler_path: str = "models/feature_scaler_15m.pkl"):
        """Initialize 15m backtest runner

        Args:
            model_path: Path to trained 15m model
            scaler_path: Path to 15m feature scaler
        """
        self.engine = create_backtest_engine_15m(model_path, scaler_path)
        self.results = None
        self.test_data = None
        self.signals = None

    def run_backtest(
        self,
        test_data_path: str = "data/backtest_data/custom_test_data_15m.csv",
        confidence_threshold: float = 0.65,
        holding_period_bars: int = 36,  # ~2 trading days for 15m
        transaction_cost: float = 0.0005,  # Reduced for 15m
        benchmark_ticker: str = "^VNI"
    ) -> BacktestResults15m:
        """Run 15m backtest on test data

        Args:
            test_data_path: Path to 15m test data CSV
            confidence_threshold: Minimum confidence for trades
            holding_period_bars: Maximum holding period in 15m bars
            transaction_cost: Transaction cost percentage (lower for 15m)
            benchmark_ticker: Benchmark ticker

        Returns:
            BacktestResults15m object
        """
        logger.info(f"Loading 15m test data from {test_data_path}")
        test_data = pd.read_csv(test_data_path)

        # Ensure timestamp is datetime
        test_data['timestamp'] = pd.to_datetime(test_data['timestamp'])

        # Run 15m backtest
        self.results = self.engine.run_backtest_15m(
            test_data=test_data,
            confidence_threshold=confidence_threshold,
            holding_period_bars=holding_period_bars,
            transaction_cost=transaction_cost,
            benchmark_ticker=benchmark_ticker
        )

        # Generate signals for visualization
        self.test_data = test_data.copy()
        self.signals = self.engine.generate_signals(
            self.test_data, confidence_threshold
        )

        from collections import Counter
        cnt = Counter([t.ticker for t in self.results.trades])
        logger.info(f"15m Trades per ticker: {dict(cnt)}")
        logger.info(f"Total 15m trades: {sum(cnt.values())}")
        return self.results

    def generate_report(
            self,
            output_dir: str = "results/backtest_15m") -> None:
        """Generate comprehensive 15m backtest report

        Args:
            output_dir: Directory to save 15m report files
        """
        if self.results is None:
            raise ValueError(
                "No backtest results available. Run backtest first."
            )

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Generate text summary
        self._generate_summary_report_15m(output_path)

        # Generate visualizations
        self._generate_charts_15m(output_path)

        # Generate price charts with signals
        self._generate_price_charts_15m(output_path)

        # Save detailed data
        self._save_detailed_data_15m(output_path)

        logger.info(f"15m backtest report saved to {output_path}")

    def _generate_summary_report_15m(self, output_path: Path) -> None:
        """Generate text summary report for 15m"""
        results = self.results

        summary = f"""
# 15-MINUTE BACKTEST RESULTS SUMMARY

## Performance Overview (15m Timeframe)
- **Tổng Return**: {results.total_return:.2%}
- **Return Hàng Năm**: {results.annualized_return:.2%}
- **Volatility**: {results.volatility:.2%}
- **Sharpe Ratio**: {results.sharpe_ratio:.3f}
- **Max Drawdown**: {results.max_drawdown:.2%}

## Trading Statistics (15m Specific)
- **Tổng Số Giao Dịch**: {results.total_trades:,}
- **Giao Dịch Thắng**: {results.winning_trades:,}
- **Giao Dịch Thua**: {results.losing_trades:,}
- **Tỷ Lệ Thắng**: {results.win_rate:.2%}
- **Avg Win**: {results.avg_win:.2%}
- **Avg Loss**: {results.avg_loss:.2%}
- **Profit Factor**: {results.profit_factor:.2f}

## 15m Timeframe Metrics
- **Avg Holding Time**: {results.avg_holding_bars:.1f} bars ({results.avg_holding_days:.1f} days)
- **Trades per Day**: {results.trades_per_day:.2f}
- **Total Bars Analyzed**: {len(self.test_data) if self.test_data is not None else 'N/A'}

## Benchmark Comparison (VN-Index)
- **Benchmark Return**: {results.benchmark_return:.2%}
- **Excess Return**: {results.excess_return:.2%}
- **Beta**: {results.beta:.3f}
- **Alpha**: {results.alpha:.4f}

## 15m Signal Distribution
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
            summary += "## Average Metrics by Signal Type (15m)\n"

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

        # Add 15m specific insights
        summary += f"""
## 15m Trading Insights
- **Intraday Strategy**: Optimized for 15-minute bars
- **Transaction Cost**: {0.0005:.2%} (lower than daily due to frequency)
- **Holding Period**: Max {36} bars (~2 trading days)
- **Signal Confidence**: Threshold optimized for intraday noise
"""

        # Save summary
        with open(
            output_path / "backtest_summary_15m.md", "w", encoding="utf-8"
        ) as f:
            f.write(summary)

        # Save metrics as JSON
        metrics = {
            "timeframe": "15m",
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
            "intraday_15m": {
                "avg_holding_bars": results.avg_holding_bars,
                "avg_holding_days": results.avg_holding_days,
                "trades_per_day": results.trades_per_day,
            },
            "benchmark": {
                "benchmark_return": results.benchmark_return,
                "excess_return": results.excess_return,
                "beta": results.beta,
                "alpha": results.alpha,
            },
        }

        with open(output_path / "backtest_metrics_15m.json", "w") as f:
            json.dump(metrics, f, indent=2)

    def _generate_charts_15m(self, output_path: Path) -> None:
        """Generate visualization charts for 15m"""
        if not self.results.trades:
            logger.warning("No trades to visualize for 15m")
            return

        plt.style.use('default')
        fig = plt.figure(figsize=(18, 14))  # Larger for 15m details

        # 1. Equity Curve
        plt.subplot(2, 4, 1)
        if not self.results.equity_curve.empty:
            plt.plot(
                pd.to_datetime(self.results.equity_curve['date']),
                self.results.equity_curve['equity'],
                color='blue', linewidth=1
            )
            plt.title('15m Equity Curve')
            plt.xlabel('Date')
            plt.ylabel('Equity')
            plt.xticks(rotation=45)

        # 2. Drawdown
        plt.subplot(2, 4, 2)
        if not self.results.drawdown_curve.empty:
            plt.fill_between(
                pd.to_datetime(self.results.drawdown_curve['date']),
                self.results.drawdown_curve['drawdown'],
                0,
                color='red',
                alpha=0.3,
            )
            plt.title('15m Drawdown')
            plt.xlabel('Date')
            plt.ylabel('Drawdown')
            plt.xticks(rotation=45)

        # 3. Return Distribution
        plt.subplot(2, 4, 3)
        returns = [t.return_pct for t in self.results.trades]
        plt.hist(returns, bins=30, alpha=0.7, edgecolor='black')
        plt.title('15m Return Distribution')
        plt.xlabel('Return (%)')
        plt.ylabel('Frequency')
        plt.axvline(x=0, color='red', linestyle='--', alpha=0.7)

        # 4. Holding Period Distribution (15m specific)
        plt.subplot(2, 4, 4)
        holding_days = [t.holding_days for t in self.results.trades]
        plt.hist(holding_days, bins=20, alpha=0.7, edgecolor='black')
        plt.title('Holding Period Distribution')
        plt.xlabel('Days Held')
        plt.ylabel('Frequency')
        plt.axvline(
            x=np.mean(holding_days),
            color='red',
            linestyle='--',
            alpha=0.7,
            label=f'Avg: {np.mean(holding_days):.1f}d')
        plt.legend()

        # 5. Hourly Performance Pattern
        plt.subplot(2, 4, 5)
        if self.test_data is not None and 'timestamp' in self.test_data.columns:
            hourly_returns = self._calculate_hourly_performance()
            if not hourly_returns.empty:
                hourly_returns.plot(kind='bar', alpha=0.7)
                plt.title('Performance by Hour (15m)')
                plt.xlabel('Hour')
                plt.ylabel('Avg Return')
                plt.xticks(rotation=45)

        # 6. Trades per Hour Distribution
        plt.subplot(2, 4, 6)
        trade_hours = []
        for trade in self.results.trades:
            hour = pd.to_datetime(trade.entry_date).hour
            trade_hours.append(hour)

        if trade_hours:
            plt.hist(
                trade_hours,
                bins=range(
                    9,
                    16),
                alpha=0.7,
                edgecolor='black')
            plt.title('Trades by Hour')
            plt.xlabel('Hour of Day')
            plt.ylabel('Number of Trades')

        # 7. Signal Performance
        plt.subplot(2, 4, 7)
        buy_returns = [
            t.return_pct for t in self.results.trades if t.signal == 1
        ]
        sell_returns = [
            t.return_pct for t in self.results.trades if t.signal == -1
        ]

        if buy_returns and sell_returns:
            plt.boxplot([buy_returns, sell_returns], labels=['Buy', 'Sell'])
            plt.title('Return by Signal Type (15m)')
            plt.ylabel('Return (%)')
            plt.axhline(y=0, color='red', linestyle='--', alpha=0.7)

        # 8. Confidence vs Performance
        plt.subplot(2, 4, 8)
        confidence_vals = [t.confidence for t in self.results.trades]
        returns_vals = [t.return_pct for t in self.results.trades]

        if confidence_vals and returns_vals:
            plt.scatter(confidence_vals, returns_vals, alpha=0.6)
            plt.title('Confidence vs Return (15m)')
            plt.xlabel('Confidence')
            plt.ylabel('Return (%)')
            plt.axhline(y=0, color='red', linestyle='--', alpha=0.7)

        plt.tight_layout()
        plt.savefig(
            output_path /
            "backtest_charts_15m.png",
            dpi=300,
            bbox_inches='tight')
        plt.close()

        # Plot portfolio vs benchmark chart
        self._plot_portfolio_vs_benchmark_chart_15m(output_path)
        logger.info("15m charts saved successfully")

    def _plot_portfolio_vs_benchmark_chart_15m(
            self, output_path: Path) -> None:
        """Plot Portfolio vs VNINDEX performance chart for 15m"""
        if self.results is None or self.results.equity_curve.empty:
            logger.warning("No equity curve available for 15m")
            return

        eq_curve = self.results.equity_curve.copy()
        eq_curve['date'] = pd.to_datetime(eq_curve['date'])
        eq_curve = eq_curve.set_index('date')

        # Portfolio performance
        portfolio_perf = (
            eq_curve['equity'] / eq_curve['equity'].iloc[0] - 1.0) * 100

        # Benchmark performance (if available)
        if hasattr(
                self.results,
                "benchmark_df") and self.results.benchmark_df is not None:
            idx = self.results.benchmark_df.copy()
            idx.index = pd.to_datetime(idx.index)
            idx_perf = (idx['close'] / idx['close'].iloc[0] - 1.0) * 100

            # Align dates
            common_idx = portfolio_perf.index.intersection(idx_perf.index)
            portfolio_perf = portfolio_perf.loc[common_idx]
            idx_perf = idx_perf.loc[common_idx]
        else:
            idx_perf = None

        # Plot
        plt.figure(figsize=(14, 8))
        plt.plot(portfolio_perf.index, portfolio_perf,
                 label="15m Portfolio", linewidth=2, color='blue')

        if idx_perf is not None:
            plt.plot(idx_perf.index, idx_perf,
                     label="VNINDEX", linewidth=2, color="orange")

        plt.title("15m Portfolio vs VNINDEX Performance")
        plt.ylabel("Cumulative Return (%)")
        plt.xlabel("Date")
        plt.legend()
        plt.grid(True, linestyle="--", alpha=0.4)

        # Add performance stats
        final_portfolio = portfolio_perf.iloc[-1] if len(
            portfolio_perf) > 0 else 0
        final_benchmark = idx_perf.iloc[-1] if idx_perf is not None and len(
            idx_perf) > 0 else 0

        plt.text(
            0.02,
            0.98,
            f'Portfolio: {final_portfolio:.1f}%\nBenchmark: {final_benchmark:.1f}%\nOutperformance: {final_portfolio - final_benchmark:.1f}%',
            transform=plt.gca().transAxes,
            verticalalignment='top',
            bbox=dict(
                boxstyle='round',
                facecolor='wheat',
                alpha=0.8))

        plt.tight_layout()

        # Save chart
        plt.savefig(output_path / "portfolio_vs_vnindex_15m.png",
                    dpi=300, bbox_inches="tight")
        plt.close()

    def _generate_price_charts_15m(self, output_path: Path) -> None:
        """Generate 15m price charts with signals for each ticker"""
        if self.test_data is None or self.signals is None:
            logger.warning(
                "No test data or signals available for 15m price charts")
            return

        # Create directory for price charts
        price_charts_dir = output_path / "price_charts_15m"
        price_charts_dir.mkdir(exist_ok=True)

        # Get unique tickers
        tickers = self.test_data['ticker'].unique()

        for ticker in tickers:
            try:
                self._plot_ticker_price_chart_15m(ticker, price_charts_dir)
            except Exception as e:
                logger.warning(f"Failed to plot 15m chart for {ticker}: {e}")

        logger.info(f"15m price charts saved to {price_charts_dir}")

    def _plot_ticker_price_chart_15m(
            self, ticker: str, output_dir: Path) -> None:
        """Plot 15m price chart with signals for a specific ticker"""
        # Filter data for this ticker
        ticker_data = self.test_data[self.test_data['ticker'] == ticker].copy()
        ticker_signals = self.signals.loc[ticker_data.index].copy()

        # Get trades for this ticker
        ticker_trades = [t for t in self.results.trades if t.ticker == ticker]

        # Create figure
        fig, (ax1, ax2) = plt.subplots(
            2, 1, figsize=(16, 12), height_ratios=[3, 1]
        )
        ax1.set_title(
            f'{ticker} - 15m Executed Trades (n={len(ticker_trades)})',
            fontsize=14
        )

        # Plot 1: Price and signals
        dates = pd.to_datetime(ticker_data['timestamp'])
        prices = ticker_data['close']

        # Plot price line
        ax1.plot(dates, prices, 'b-', linewidth=1, label='Close Price')

        # Plot signals
        buy_signals = ticker_signals[ticker_signals['signal'] == 1]
        sell_signals = ticker_signals[ticker_signals['signal'] == -1]

        if not buy_signals.empty:
            buy_dates = pd.to_datetime(
                ticker_data.loc[buy_signals.index, 'timestamp']
            )
            buy_prices = ticker_data.loc[buy_signals.index, 'close']
            ax1.scatter(buy_dates, buy_prices, color='green', marker='^',
                        s=80, label='Buy Signal', zorder=5, alpha=0.7)

        if not sell_signals.empty:
            sell_dates = pd.to_datetime(
                ticker_data.loc[sell_signals.index, 'timestamp']
            )
            sell_prices = ticker_data.loc[sell_signals.index, 'close']
            ax1.scatter(sell_dates, sell_prices, color='red', marker='v',
                        s=80, label='Sell Signal', zorder=5, alpha=0.7)

        # Plot entry/exit points from trades
        for i, trade in enumerate(ticker_trades):
            entry_date = pd.to_datetime(trade.entry_date)
            exit_date = pd.to_datetime(trade.exit_date)

            # Find closest dates in data
            entry_idx = ticker_data[
                ticker_data['timestamp'] == trade.entry_date
            ].index
            exit_idx = ticker_data[
                ticker_data['timestamp'] == trade.exit_date
            ].index

            if not entry_idx.empty and not exit_idx.empty:
                entry_price = ticker_data.loc[entry_idx[0], 'close']
                exit_price = ticker_data.loc[exit_idx[0], 'close']

                # Plot entry point
                ax1.scatter(entry_date, entry_price, color='darkgreen',
                            marker='o', s=120,
                            label='Entry' if i == 0 else "",
                            zorder=6, edgecolor='white', linewidth=2)

                # Plot exit point
                color = 'darkred' if trade.return_pct < 0 else 'darkgreen'
                ax1.scatter(exit_date, exit_price, color=color,
                            marker='x', s=120,
                            label='Exit' if i == 0 else "",
                            zorder=6, linewidth=3)

                # Draw line between entry and exit
                ax1.plot([entry_date, exit_date], [entry_price, exit_price],
                         color=color, alpha=0.6, linewidth=2)

                # Add return text
                ax1.text(exit_date, exit_price,
                         f'{trade.return_pct:.1%}',
                         fontsize=8, ha='left', va='bottom')

        ax1.set_title(f'{ticker} - 15m Price Chart with Signals and Trades',
                      fontsize=14)
        ax1.set_ylabel('Price (VND)')
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        # Plot 2: Volume
        if 'volume' in ticker_data.columns:
            volumes = ticker_data['volume']
            ax2.bar(dates, volumes, alpha=0.6, color='gray', width=0.001)
            ax2.set_ylabel('Volume')
            ax2.set_xlabel('Date')
        else:
            ax2.set_visible(False)

        # Format x-axis
        plt.xticks(rotation=45)
        plt.tight_layout()

        # Save chart
        chart_path = output_dir / f"{ticker}_price_chart_15m.png"
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close()

    def _calculate_hourly_performance(self) -> pd.Series:
        """Calculate performance by hour for 15m data"""
        if self.results is None or not self.results.trades:
            return pd.Series()

        hourly_returns = {}
        for trade in self.results.trades:
            hour = pd.to_datetime(trade.entry_date).hour
            if hour not in hourly_returns:
                hourly_returns[hour] = []
            hourly_returns[hour].append(trade.return_pct)

        # Calculate average return per hour
        avg_hourly = {hour: np.mean(returns)
                      for hour, returns in hourly_returns.items()}

        return pd.Series(avg_hourly).sort_index()

    def _save_detailed_data_15m(self, output_path: Path) -> None:
        """Save detailed 15m trade data"""
        if not self.results.trades:
            return

        # Save trades data with 15m specific columns
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
                'holding_bars': trade.holding_bars,
                'holding_days': trade.holding_days,
                'confidence': trade.confidence
            })

        trades_df = pd.DataFrame(trades_data)
        trades_df.to_csv(output_path / "detailed_trades_15m.csv", index=False)

        # Save equity curve
        if not self.results.equity_curve.empty:
            self.results.equity_curve.to_csv(
                output_path / "equity_curve_15m.csv", index=False
            )

        # Save drawdown curve
        if not self.results.drawdown_curve.empty:
            self.results.drawdown_curve.to_csv(
                output_path / "drawdown_curve_15m.csv", index=False
            )

    def print_summary_15m(self) -> None:
        """Print quick 15m summary to console"""
        if self.results is None:
            print("No 15m backtest results available")
            return

        print("\n" + "=" * 70)
        print("📊 15-MINUTE BACKTEST RESULTS SUMMARY")
        print("=" * 70)
        print(f"💰 Total Return: {self.results.total_return:.2%}")
        print(f"📈 Annualized Return: {self.results.annualized_return:.2%}")
        print(f"📉 Max Drawdown: {self.results.max_drawdown:.2%}")
        print(f"📊 Sharpe Ratio: {self.results.sharpe_ratio:.3f}")
        print(f"🎯 Total Trades: {self.results.total_trades:,}")
        print(f"✅ Win Rate: {self.results.win_rate:.2%}")
        print(f"🏆 Profit Factor: {self.results.profit_factor:.2f}")
        print(f"📊 VN-Index Return: {self.results.benchmark_return:.2%}")
        print(f"💎 Excess Return: {self.results.excess_return:.2%}")
        print("\n" + "-" * 50)
        print("15m SPECIFIC METRICS")
        print("-" * 50)
        print(
            f"⏱️  Avg Holding: {self.results.avg_holding_bars:.1f} bars ({self.results.avg_holding_days:.1f} days)")
        print(f"📊 Trades per Day: {self.results.trades_per_day:.2f}")
        print(f"🔄 Transaction Cost: 0.05% (optimized for 15m)")
        print("=" * 70)


def run_backtest_analysis_15m(
    model_path: str = "models/xgboost_model_15m.pkl",
    scaler_path: str = "models/feature_scaler_15m.pkl",
    test_data_path: str = "data/backtest_data/custom_test_data_15m.csv",
    confidence_threshold: float = 0.65,
    holding_period_bars: int = 36,
    output_dir: str = "results/backtest_15m"
) -> BacktestResults15m:
    """Run complete 15m backtest analysis

    Args:
        model_path: Path to trained 15m model
        scaler_path: Path to 15m feature scaler
        test_data_path: Path to 15m test data
        confidence_threshold: Minimum confidence threshold
        holding_period_bars: Max holding period in 15m bars
        output_dir: Output directory for reports

    Returns:
        BacktestResults15m object
    """
    logger.info("Starting 15m backtest analysis...")

    # Create runner
    runner = BacktestRunner15m(model_path, scaler_path)

    # Run backtest
    results = runner.run_backtest(
        test_data_path=test_data_path,
        confidence_threshold=confidence_threshold,
        holding_period_bars=holding_period_bars
    )

    # Generate reports
    runner.generate_report(output_dir)

    # Print summary
    runner.print_summary_15m()

    logger.info("15m backtest analysis completed")
    return results


if __name__ == "__main__":
    # Run 15m backtest with default parameters
    results = run_backtest_analysis_15m()
