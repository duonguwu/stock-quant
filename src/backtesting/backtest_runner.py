"""Backtest runner and report generator"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
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
        self.test_data = None
        self.signals = None

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

        # Generate signals for visualization
        self.test_data = test_data.copy()
        self.signals = self.engine.generate_signals(self.test_data, confidence_threshold)

        from collections import Counter
        cnt = Counter([t.ticker for t in self.results.trades])
        logger.info(f"Trades per ticker: {dict(cnt)}")
        logger.info(f"Total trades (sum): {sum(cnt.values())}")
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

        # Generate price charts with signals
        self._generate_price_charts(output_path)

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
        self._plot_portfolio_vs_benchmark_chart(output_path)
        logger.info("Charts saved successfully")

    def _plot_portfolio_vs_benchmark_chart(self, output_path: Path) -> None:
        """Plot Portfolio vs VNINDEX annualized performance chart"""
        if self.results is None or self.results.equity_curve.empty:
            logger.warning("No equity curve available")
            return

        eq_curve = self.results.equity_curve.copy()
        eq_curve['date'] = pd.to_datetime(eq_curve['date'])
        eq_curve = eq_curve.set_index('date')

        # Portfolio annualized return theo từng thời điểm
        # Portfolio annualized return
        days = (eq_curve.index - eq_curve.index[0]).days
        days = np.where(days == 0, 1, days)
        portfolio_cagr = (eq_curve['equity'] / eq_curve['equity'].iloc[0]) ** (365 / days) - 1
        portfolio_cagr = portfolio_cagr * 100


        # Benchmark annualized return (nếu có)
        if hasattr(self.results, "benchmark_df") and self.results.benchmark_df is not None:
            idx = self.results.benchmark_df.copy()
            idx.index = pd.to_datetime(idx.index)
            idx_perf = (idx['close'] / idx['close'].iloc[0] - 1.0) * 100

            # Align ngày chung
            common_idx = portfolio_cagr.index.intersection(idx_perf.index)
            portfolio_cagr = portfolio_cagr.loc[common_idx]
            idx_perf = idx_perf.loc[common_idx]
        else:
            idx_perf = None

        # Plot
        plt.figure(figsize=(12, 6))
        plt.plot(portfolio_cagr.index, portfolio_cagr, label="Portfolio", linewidth=2)
        if idx_perf is not None:
            plt.plot(idx_perf.index, idx_perf, label="VNINDEX", linewidth=2, color="orange")

        plt.title("Portfolio vs VNINDEX Annualized Performance")
        plt.ylabel("Annualized Return (%)")
        plt.xlabel("Date")
        plt.legend()
        plt.grid(True, linestyle="--", alpha=0.4)
        plt.tight_layout()

        # Save ảnh riêng
        plt.savefig(output_path / "portfolio_vs_vnindex_annualized.png", dpi=300, bbox_inches="tight")
        plt.close()

    def _generate_price_charts(self, output_path: Path) -> None:
        """Generate price charts with signals for each ticker"""
        if self.test_data is None or self.signals is None:
            logger.warning("No test data or signals available for price charts")
            return

        # Create directory for price charts
        price_charts_dir = output_path / "price_charts"
        price_charts_dir.mkdir(exist_ok=True)

        # Get unique tickers
        tickers = self.test_data['ticker'].unique()

        for ticker in tickers:
            try:
                self._plot_ticker_price_chart(ticker, price_charts_dir)
            except Exception as e:
                logger.warning(f"Failed to plot chart for {ticker}: {e}")

        logger.info(f"Price charts saved to {price_charts_dir}")

    def _plot_ticker_price_chart(self, ticker: str, output_dir: Path) -> None:
        """Plot price chart with signals for a specific ticker"""
        # Filter data for this ticker
        ticker_data = self.test_data[self.test_data['ticker'] == ticker].copy()
        ticker_signals = self.signals.loc[ticker_data.index].copy()

        # Get trades for this ticker
        ticker_trades = [t for t in self.results.trades if t.ticker == ticker]

        # Create figure
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10), height_ratios=[3, 1])
        ax1.set_title(f'{ticker} - Executed Trades (n={len(ticker_trades)})', fontsize=14)

        # Plot 1: Price and signals
        dates = pd.to_datetime(ticker_data['timestamp'])
        prices = ticker_data['close']

        # Plot price line
        ax1.plot(dates, prices, 'b-', linewidth=1, label='Close Price')

        # Plot signals
        buy_signals = ticker_signals[ticker_signals['signal'] == 1]
        sell_signals = ticker_signals[ticker_signals['signal'] == -1]

        if not buy_signals.empty:
            buy_dates = pd.to_datetime(ticker_data.loc[buy_signals.index, 'timestamp'])
            buy_prices = ticker_data.loc[buy_signals.index, 'close']
            ax1.scatter(buy_dates, buy_prices, color='green', marker='^',
                       s=100, label='Buy Signal', zorder=5)

        if not sell_signals.empty:
            sell_dates = pd.to_datetime(ticker_data.loc[sell_signals.index, 'timestamp'])
            sell_prices = ticker_data.loc[sell_signals.index, 'close']
            ax1.scatter(sell_dates, sell_prices, color='red', marker='v',
                       s=100, label='Sell Signal', zorder=5)

        # Plot entry/exit points from trades
        for trade in ticker_trades:
            entry_date = pd.to_datetime(trade.entry_date)
            exit_date = pd.to_datetime(trade.exit_date)

            # Find closest dates in data
            entry_idx = ticker_data[ticker_data['timestamp'] == trade.entry_date].index
            exit_idx = ticker_data[ticker_data['timestamp'] == trade.exit_date].index

            if not entry_idx.empty and not exit_idx.empty:
                entry_price = ticker_data.loc[entry_idx[0], 'close']
                exit_price = ticker_data.loc[exit_idx[0], 'close']

                # Plot entry point
                ax1.scatter(entry_date, entry_price, color='darkgreen', 
                           marker='o', s=150, label='Entry' if trade == ticker_trades[0] else "", 
                           zorder=6, edgecolor='white', linewidth=2)

                # Plot exit point
                color = 'darkred' if trade.return_pct < 0 else 'darkgreen'
                ax1.scatter(exit_date, exit_price, color=color, 
                           marker='x', s=150, label='Exit' if trade == ticker_trades[0] else "", 
                           zorder=6, linewidth=3)

                # Draw line between entry and exit
                ax1.plot([entry_date, exit_date], [entry_price, exit_price], 
                        color=color, alpha=0.7, linewidth=2)

        ax1.set_title(f'{ticker} - Price Chart with Signals and Trades', fontsize=14)
        ax1.set_ylabel('Price (VND)')
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        # Plot 2: Volume
        if 'volume' in ticker_data.columns:
            volumes = ticker_data['volume']
            ax2.bar(dates, volumes, alpha=0.7, color='gray', width=1)
            ax2.set_ylabel('Volume')
            ax2.set_xlabel('Date')
        else:
            ax2.set_visible(False)

        # Format x-axis
        plt.xticks(rotation=45)
        plt.tight_layout()

        # Save chart
        chart_path = output_dir / f"{ticker}_price_chart.png"
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close()

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
        print("\n" + "=" * 40)
        print("PORTFOLIO BACKTEST RESULTS")
        print("=" * 40)
        print(f"Portfolio Return [%]: {self.results.annualized_return:.2%}")
        print(f"Portfolio Max Drawdown [%]: {abs(self.results.max_drawdown):.2%}")
        print(f"Total Trades: {self.results.total_trades}")
        print(f"Win Rate [%] (est.): {self.results.win_rate:.2%}")
        print("=" * 40)
        print("PORTFOLIO BACKTEST RESULTS")
        print("=" * 40)
        print(f"Hiệu suất danh mục: {self.results.annualized_return:.2%}")
        print(f"Hiệu suất VNINDEX: {self.results.benchmark_return:.2%}")
        print(f"Outperformance: {(self.results.excess_return):.2%}")
        print("=" * 40)


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
