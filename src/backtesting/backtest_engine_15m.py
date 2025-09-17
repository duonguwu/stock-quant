"""Backtesting engine for 15-minute timeframe trading strategy evaluation"""

import os
import pandas as pd
import numpy as np
import joblib
from typing import List, Tuple, Optional
from dataclasses import dataclass
from loguru import logger

from ..data.data_fetcher import FiinDataFetcher
from FiinQuantX import FiinSession
from dotenv import load_dotenv


@dataclass
class Trade15m:
    """Individual trade record for 15m timeframe"""
    entry_date: str
    exit_date: str
    ticker: str
    signal: int  # -1, 0, 1
    entry_price: float
    exit_price: float
    return_pct: float
    holding_bars: int  # Number of 15m bars held
    holding_days: float  # Actual days (bars/18)
    confidence: float


@dataclass
class BacktestResults15m:
    """Comprehensive backtest results for 15m timeframe"""
    # Strategy Performance
    total_return: float
    annualized_return: float
    volatility: float
    sharpe_ratio: float
    max_drawdown: float

    # Trade Statistics
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    avg_win: float
    avg_loss: float
    profit_factor: float

    # 15m Specific Metrics
    avg_holding_bars: float
    avg_holding_days: float
    trades_per_day: float

    # Benchmark Comparison
    benchmark_return: float
    excess_return: float
    beta: float
    alpha: float

    # Detailed Records
    trades: List[Trade15m]
    equity_curve: pd.DataFrame
    drawdown_curve: pd.DataFrame
    benchmark_df: Optional[pd.DataFrame] = None


def get_benchmark_returns_from_fiin_15m(
        start_date: str,
        end_date: str) -> pd.DataFrame:
    """Fetch VNINDEX 15m returns from FiinQuantX between specified dates."""
    load_dotenv()

    client = FiinSession(
        username=os.getenv("FIIN_USERNAME"),
        password=os.getenv("FIIN_PASSWORD"),
    ).login()

    # Try to get 15m data, fallback to daily if not available
    try:
        event = client.Fetch_Trading_Data(
            realtime=False,
            tickers=["VNINDEX"],
            fields=["close"],
            adjusted=True,
            by="15m",
            from_date=start_date,
            to_date=end_date
        )
        benchmark_df = event.get_data()
    except BaseException:
        # Fallback to daily data
        logger.warning("15m VNINDEX data not available, using daily data")
        event = client.Fetch_Trading_Data(
            realtime=False,
            tickers=["VNINDEX"],
            fields=["close"],
            adjusted=True,
            by="1d",
            from_date=start_date,
            to_date=end_date
        )
        benchmark_df = event.get_data()

    benchmark_df.set_index("timestamp", inplace=True)
    benchmark_df.sort_index(inplace=True)
    benchmark_df["return"] = benchmark_df["close"].pct_change()
    return benchmark_df


class BacktestEngine15m:
    """Backtesting engine optimized for 15-minute timeframe"""

    def __init__(self, model_path: str, scaler_path: str):
        """Initialize backtest engine for 15m

        Args:
            model_path: Path to trained 15m model
            scaler_path: Path to 15m feature scaler
        """
        self.model = joblib.load(model_path)
        self.scaler = joblib.load(scaler_path)
        self.bars_per_day = 18  # Approximate 15m bars per trading day
        logger.info(f"Loaded 15m model from {model_path}")
        logger.info(f"Loaded 15m scaler from {scaler_path}")

    def prepare_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Prepare features for 15m prediction

        Args:
            data: Raw 15m data with all columns

        Returns:
            Scaled features DataFrame
        """
        # Select feature columns (exclude non-feature columns)
        exclude_cols = [
            'ticker', 'timestamp', 'label', 'hit_time', 'hit_type',
            'ub', 'lb', 'vbar_end'
        ]

        feature_cols = [col for col in data.columns if col not in exclude_cols]
        X = data[feature_cols].copy()

        # Handle missing values
        X_clean = X.fillna(X.median())
        X_clean = X_clean.replace([np.inf, -np.inf], np.nan)
        X_clean = X_clean.fillna(X_clean.median())

        # Scale features
        X_scaled = self.scaler.transform(X_clean)

        return pd.DataFrame(X_scaled, columns=feature_cols, index=data.index)

    def generate_signals(
        self, data: pd.DataFrame, confidence_threshold: float = 0.65
    ) -> pd.DataFrame:
        """Generate trading signals from 15m model predictions

        Args:
            data: Input 15m data with features
            confidence_threshold: Minimum confidence for signal generation

        Returns:
            DataFrame with signals and confidence
        """
        # Prepare features
        X_scaled = self.prepare_features(data)

        # Generate predictions
        predictions = self.model.predict(X_scaled)
        probabilities = self.model.predict_proba(X_scaled)

        # Calculate confidence (max probability)
        confidence = np.max(probabilities, axis=1)

        # Apply confidence threshold
        signals = predictions.copy()
        label_map = {0: -1, 1: 0, 2: 1}
        signals = np.vectorize(label_map.get)(predictions)
        # Hold if low confidence
        signals[confidence < confidence_threshold] = 0

        # Create signals DataFrame
        signals_df = pd.DataFrame(
            {
                'signal': signals,
                'confidence': confidence,
                'prob_sell': (
                    probabilities[:, 0] if probabilities.shape[1] > 0 else 0
                ),
                'prob_hold': (
                    probabilities[:, 1] if probabilities.shape[1] > 1 else 0
                ),
                'prob_buy': (
                    probabilities[:, 2] if probabilities.shape[1] > 2 else 0
                ),
            },
            index=data.index,
        )

        return signals_df

    def simulate_trades(
        self,
        data: pd.DataFrame,
        signals: pd.DataFrame,
        holding_period_bars: int = 36,  # ~2 trading days for 15m
        transaction_cost: float = 0.0005,  # Reduced for 15m
    ) -> List[Trade15m]:
        """Simulate 15m trading based on signals

        Args:
            data: 15m price data
            signals: Trading signals
            holding_period_bars: Maximum holding period in 15m bars
            transaction_cost: Transaction cost as percentage

        Returns:
            List of executed trades
        """
        trades = []

        # Group by ticker for individual simulation
        for ticker in data['ticker'].unique():
            ticker_data = data[data['ticker'] == ticker].copy()
            ticker_signals = signals.loc[ticker_data.index].copy()

            trades.extend(
                self._simulate_ticker_trades_15m(
                    ticker_data,
                    ticker_signals,
                    ticker,
                    holding_period_bars,
                    transaction_cost,
                )
            )

        logger.info(
            "Simulated %d trades across %d tickers (15m timeframe)",
            len(trades),
            len(data['ticker'].unique()),
        )
        return trades

    def _simulate_ticker_trades_15m(
        self,
        data: pd.DataFrame,
        signals: pd.DataFrame,
        ticker: str,
        holding_period_bars: int,
        transaction_cost: float,
    ) -> List[Trade15m]:
        """Simulate 15m trades for single ticker (long-only)"""
        trades = []
        position = 0  # 0: no position, 1: holding
        entry_date = None
        entry_price = None
        entry_confidence = None
        entry_idx = None

        for i, (idx, row) in enumerate(data.iterrows()):
            current_signal = signals.loc[idx, 'signal']
            current_confidence = signals.loc[idx, 'confidence']
            current_price = row['close']
            current_date = row['timestamp']

            # ======= LOGIC LONG-ONLY =======
            if position == 0:
                # Buy when signal == 1, not holding
                if current_signal == 1:
                    position = 1
                    entry_date = current_date
                    # Buy with transaction cost
                    entry_price = current_price * (1 + transaction_cost)
                    entry_confidence = current_confidence
                    entry_idx = i

            elif position == 1:
                bars_held = i - entry_idx

                # Sell conditions: signal == -1, or exceeded holding period
                if current_signal == -1 or bars_held >= holding_period_bars:
                    # Sell with transaction cost
                    exit_price = current_price * (1 - transaction_cost)
                    return_pct = (exit_price - entry_price) / entry_price

                    # Convert bars to days
                    holding_days = bars_held / self.bars_per_day

                    trade = Trade15m(
                        entry_date=entry_date,
                        exit_date=current_date,
                        ticker=ticker,
                        signal=1,  # Entry is always 1
                        entry_price=entry_price,
                        exit_price=exit_price,
                        return_pct=return_pct,
                        holding_bars=bars_held,
                        holding_days=holding_days,
                        confidence=entry_confidence,
                    )
                    trades.append(trade)

                    # Reset state
                    position = 0
                    entry_date = None
                    entry_price = None
                    entry_confidence = None
                    entry_idx = None

        # Force exit at end if still holding
        if position == 1:
            last_price = data.iloc[-1]['close'] * (1 - transaction_cost)
            bars_held = len(data) - entry_idx - 1
            holding_days = bars_held / self.bars_per_day

            trade = Trade15m(
                entry_date=entry_date,
                exit_date=data.iloc[-1]['timestamp'],
                ticker=ticker,
                signal=1,
                entry_price=entry_price,
                exit_price=last_price,
                return_pct=(last_price - entry_price) / entry_price,
                holding_bars=bars_held,
                holding_days=holding_days,
                confidence=entry_confidence,
            )
            trades.append(trade)

        return trades

    def calculate_performance_metrics_15m(
        self,
        trades: List[Trade15m],
        start_date: str,
        end_date: str,
        benchmark_ticker: str = "^VNI",
    ) -> BacktestResults15m:
        """Calculate comprehensive performance metrics for 15m

        Args:
            trades: List of executed 15m trades
            start_date: Strategy start date
            end_date: Strategy end date
            benchmark_ticker: Benchmark ticker symbol

        Returns:
            BacktestResults15m with all metrics
        """
        if not trades:
            logger.warning("No trades to analyze")
            return self._empty_results_15m()

        # Convert trades to DataFrame for analysis
        trades_df = pd.DataFrame(
            [
                {
                    'entry_date': t.entry_date,
                    'exit_date': t.exit_date,
                    'ticker': t.ticker,
                    'signal': t.signal,
                    'return_pct': t.return_pct,
                    'holding_bars': t.holding_bars,
                    'holding_days': t.holding_days,
                    'confidence': t.confidence,
                }
                for t in trades
            ]
        )

        # Strategy Performance
        strategy_returns = trades_df['return_pct'].values
        total_return = (1 + strategy_returns).prod() - 1

        # 15m specific metrics
        avg_holding_bars = trades_df['holding_bars'].mean()
        avg_holding_days = trades_df['holding_days'].mean()

        # Calculate trades per day
        period_days = (
            pd.to_datetime(end_date) -
            pd.to_datetime(start_date)).days
        trades_per_day = len(trades) / period_days if period_days > 0 else 0

        # Annualized metrics (adjusted for 15m)
        years = period_days / 365.25
        annualized_return = (
            (1 + total_return) ** (1 / years) - 1 if years > 0 else 0
        )

        # Volatility calculation for 15m (252 trading days * 18 bars per day)
        volatility = (
            np.std(strategy_returns) * np.sqrt(252 * self.bars_per_day)
            if len(strategy_returns) > 1
            else 0
        )

        sharpe_ratio = (
            annualized_return / volatility if volatility > 0 else 0
        )

        # Drawdown calculation
        cumulative_returns = (1 + strategy_returns).cumprod()
        running_max = np.maximum.accumulate(cumulative_returns)
        drawdown = (cumulative_returns - running_max) / running_max
        max_drawdown = np.min(drawdown)

        # Trade Statistics
        total_trades = len(trades)
        winning_trades = len(trades_df[trades_df['return_pct'] > 0])
        losing_trades = len(trades_df[trades_df['return_pct'] < 0])
        win_rate = winning_trades / total_trades if total_trades > 0 else 0

        avg_win = (
            trades_df[trades_df['return_pct'] > 0]['return_pct'].mean()
            if winning_trades > 0
            else 0
        )
        avg_loss = (
            trades_df[trades_df['return_pct'] < 0]['return_pct'].mean()
            if losing_trades > 0
            else 0
        )
        profit_factor = (
            (winning_trades * avg_win) / abs(losing_trades * avg_loss)
            if losing_trades > 0 and avg_loss != 0
            else float('inf')
        )

        # Benchmark comparison
        benchmark_df = get_benchmark_returns_from_fiin_15m(
            start_date, end_date)
        benchmark_return, beta, alpha = self._calculate_benchmark_metrics_15m(
            strategy_returns, start_date, end_date, benchmark_df
        )
        excess_return = annualized_return - benchmark_return

        # Create equity curve
        equity_curve = self._create_equity_curve(trades_df)
        drawdown_curve = self._create_drawdown_curve(equity_curve)

        return BacktestResults15m(
            total_return=total_return,
            annualized_return=annualized_return,
            volatility=volatility,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate,
            avg_win=avg_win,
            avg_loss=avg_loss,
            profit_factor=profit_factor,
            avg_holding_bars=avg_holding_bars,
            avg_holding_days=avg_holding_days,
            trades_per_day=trades_per_day,
            benchmark_return=benchmark_return,
            excess_return=excess_return,
            beta=beta,
            alpha=alpha,
            trades=trades,
            equity_curve=equity_curve,
            drawdown_curve=drawdown_curve,
            benchmark_df=benchmark_df
        )

    def _calculate_benchmark_metrics_15m(
        self,
        strategy_returns: np.ndarray,
        start_date: str,
        end_date: str,
        benchmark_returns: Optional[pd.DataFrame] = None,
    ) -> Tuple[float, float, float]:
        """Calculate benchmark comparison metrics for 15m"""
        if benchmark_returns is None or benchmark_returns.empty:
            return 0.0, 0.0, 0.0

        # Get returns, remove NaN
        benchmark_r = benchmark_returns['return'].dropna().values

        # For 15m data, we might need to aggregate or align differently
        if len(benchmark_r) != len(strategy_returns):
            # If benchmark is daily and strategy is 15m,
            # we need to align them properly
            min_len = min(len(strategy_returns), len(benchmark_r))
            strategy_aligned = strategy_returns[:min_len]
            benchmark_aligned = benchmark_r[:min_len]
        else:
            strategy_aligned = strategy_returns
            benchmark_aligned = benchmark_r

        # Total benchmark return
        benchmark_total_return = (1 + benchmark_r).prod() - 1

        # Calculate beta and alpha
        if len(strategy_aligned) > 1 and len(benchmark_aligned) > 1:
            covariance = np.cov(strategy_aligned, benchmark_aligned)[0, 1]
            benchmark_variance = np.var(benchmark_aligned)
            beta = covariance / benchmark_variance if benchmark_variance > 0 else 0

            strategy_mean = np.mean(strategy_aligned)
            benchmark_mean = np.mean(benchmark_aligned)
            alpha = strategy_mean - beta * benchmark_mean
        else:
            beta = 0
            alpha = 0

        return benchmark_total_return, beta, alpha

    def _create_equity_curve(self, trades_df: pd.DataFrame) -> pd.DataFrame:
        """Create equity curve from trades"""
        trades_df_sorted = trades_df.sort_values('exit_date')
        cumulative_return = (1 + trades_df_sorted['return_pct']).cumprod()

        equity_curve = pd.DataFrame({
            'date': trades_df_sorted['exit_date'],
            'equity': cumulative_return,
            'return': trades_df_sorted['return_pct'],
        })

        return equity_curve.reset_index(drop=True)

    def _create_drawdown_curve(
            self, equity_curve: pd.DataFrame) -> pd.DataFrame:
        """Create drawdown curve from equity curve"""
        running_max = equity_curve['equity'].expanding().max()
        drawdown = (equity_curve['equity'] - running_max) / running_max

        return pd.DataFrame({
            'date': equity_curve['date'],
            'drawdown': drawdown,
        })

    def _empty_results_15m(self) -> BacktestResults15m:
        """Return empty results when no trades for 15m"""
        return BacktestResults15m(
            total_return=0.0,
            annualized_return=0.0,
            volatility=0.0,
            sharpe_ratio=0.0,
            max_drawdown=0.0,
            total_trades=0,
            winning_trades=0,
            losing_trades=0,
            win_rate=0.0,
            avg_win=0.0,
            avg_loss=0.0,
            profit_factor=0.0,
            avg_holding_bars=0.0,
            avg_holding_days=0.0,
            trades_per_day=0.0,
            benchmark_return=0.0,
            excess_return=0.0,
            beta=0.0,
            alpha=0.0,
            trades=[],
            equity_curve=pd.DataFrame(),
            drawdown_curve=pd.DataFrame(),
        )

    def run_backtest_15m(
        self,
        test_data: pd.DataFrame,
        confidence_threshold: float = 0.65,
        holding_period_bars: int = 36,  # ~2 trading days
        transaction_cost: float = 0.0005,
        benchmark_ticker: str = "^VNI",
    ) -> BacktestResults15m:
        """Run complete 15m backtest

        Args:
            test_data: Test dataset with all 15m features
            confidence_threshold: Minimum confidence for signal generation
            holding_period_bars: Maximum holding period in 15m bars
            transaction_cost: Transaction cost as percentage
            benchmark_ticker: Benchmark for comparison

        Returns:
            BacktestResults15m object with all metrics
        """
        logger.info("Starting 15m backtest...")

        # Generate trading signals
        signals = self.generate_signals(test_data, confidence_threshold)
        logger.info(
            "Generated 15m signals - Buy: %d, Sell: %d, Hold: %d",
            int(sum(signals['signal'] == 1)),
            int(sum(signals['signal'] == -1)),
            int(sum(signals['signal'] == 0)),
        )

        # Simulate trades
        trades = self.simulate_trades(
            test_data, signals, holding_period_bars, transaction_cost
        )

        # Calculate performance metrics
        start_date = test_data['timestamp'].min()
        end_date = test_data['timestamp'].max()
        results = self.calculate_performance_metrics_15m(
            trades, start_date, end_date, benchmark_ticker
        )

        logger.info("15m backtest completed successfully")
        logger.info(
            f"15m metrics - Avg holding: {results.avg_holding_days:.2f} days, "
            f"Trades per day: {results.trades_per_day:.2f}")
        return results


def create_backtest_engine_15m(
        model_path: str,
        scaler_path: str) -> BacktestEngine15m:
    """Create BacktestEngine15m instance

    Args:
        model_path: Path to trained 15m model
        scaler_path: Path to 15m feature scaler

    Returns:
        BacktestEngine15m instance
    """
    return BacktestEngine15m(model_path, scaler_path)
