"""Backtesting engine for trading strategy evaluation"""

import pandas as pd
import numpy as np
import joblib
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from datetime import datetime
from loguru import logger
import yfinance as yf


@dataclass
class Trade:
    """Individual trade record"""
    entry_date: str
    exit_date: str
    ticker: str
    signal: int  # -1, 0, 1
    entry_price: float
    exit_price: float
    return_pct: float
    holding_days: int
    confidence: float


@dataclass
class BacktestResults:
    """Comprehensive backtest results"""
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

    # Benchmark Comparison
    benchmark_return: float
    excess_return: float
    beta: float
    alpha: float

    # Detailed Records
    trades: List[Trade]
    equity_curve: pd.DataFrame
    drawdown_curve: pd.DataFrame


class BacktestEngine:
    """Backtesting engine for model evaluation"""

    def __init__(self, model_path: str, scaler_path: str):
        """Initialize backtest engine

        Args:
            model_path: Path to trained model
            scaler_path: Path to feature scaler
        """
        self.model = joblib.load(model_path)
        self.scaler = joblib.load(scaler_path)
        logger.info(f"Loaded model from {model_path}")
        logger.info(f"Loaded scaler from {scaler_path}")

    def prepare_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Prepare features for prediction

        Args:
            data: Raw data with all columns

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

    def generate_signals(self, data: pd.DataFrame, confidence_threshold: float = 0.6) -> pd.DataFrame:
        """Generate trading signals from model predictions

        Args:
            data: Input data with features
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
        signals[confidence < confidence_threshold] = 0  # Hold if low confidence

        # Create signals DataFrame
        signals_df = pd.DataFrame({
            'signal': signals,
            'confidence': confidence,
            'prob_sell': probabilities[:, 0] if probabilities.shape[1] > 0 else 0,
            'prob_hold': probabilities[:, 1] if probabilities.shape[1] > 1 else 0,
            'prob_buy': probabilities[:, 2] if probabilities.shape[1] > 2 else 0,
        }, index=data.index)

        return signals_df

    def simulate_trades(
        self, 
        data: pd.DataFrame, 
        signals: pd.DataFrame,
        holding_period: int = 10,
        transaction_cost: float = 0.001
    ) -> List[Trade]:
        """Simulate trading based on signals

        Args:
            data: Price data
            signals: Trading signals
            holding_period: Maximum holding period (days)
            transaction_cost: Transaction cost as percentage

        Returns:
            List of executed trades
        """
        trades = []

        # Group by ticker for individual simulation
        for ticker in data['ticker'].unique():
            ticker_data = data[data['ticker'] == ticker].copy()
            ticker_signals = signals.loc[ticker_data.index].copy()

            trades.extend(self._simulate_ticker_trades(
                ticker_data, ticker_signals, ticker, holding_period, transaction_cost
            ))

        logger.info(f"Simulated {len(trades)} trades across {len(data['ticker'].unique())} tickers")
        return trades

    def _simulate_ticker_trades(
        self,
        data: pd.DataFrame,
        signals: pd.DataFrame, 
        ticker: str,
        holding_period: int,
        transaction_cost: float
    ) -> List[Trade]:
        """Simulate trades for single ticker"""
        trades = []
        position = 0  # 0: no position, 1: long, -1: short
        entry_date = None
        entry_price = None
        entry_signal = None
        entry_confidence = None

        for i, (idx, row) in enumerate(data.iterrows()):
            current_signal = signals.loc[idx, 'signal']
            current_confidence = signals.loc[idx, 'confidence']
            current_price = row['close']
            current_date = row['timestamp']

            # Check for position exit conditions
            if position != 0:
                days_held = i - entry_idx
                should_exit = False
                exit_reason = ""

                # Exit conditions
                if days_held >= holding_period:
                    should_exit = True
                    exit_reason = "max_holding"
                elif current_signal != 0 and current_signal != entry_signal:
                    should_exit = True
                    exit_reason = "signal_change"
                elif current_signal == 0:
                    should_exit = True
                    exit_reason = "hold_signal"

                if should_exit:
                    # Calculate return
                    if entry_signal == 1:  # Long position
                        return_pct = (current_price - entry_price) / entry_price - transaction_cost
                    else:  # Short position (signal == -1)
                        return_pct = (entry_price - current_price) / entry_price - transaction_cost

                    # Record trade
                    trade = Trade(
                        entry_date=entry_date,
                        exit_date=current_date,
                        ticker=ticker,
                        signal=entry_signal,
                        entry_price=entry_price,
                        exit_price=current_price,
                        return_pct=return_pct,
                        holding_days=days_held,
                        confidence=entry_confidence
                    )
                    trades.append(trade)

                    # Reset position
                    position = 0
                    entry_date = None
                    entry_price = None
                    entry_signal = None
                    entry_confidence = None

            # Check for new position entry
            if position == 0 and current_signal != 0:
                position = current_signal
                entry_date = current_date
                entry_price = current_price
                entry_signal = current_signal
                entry_confidence = current_confidence
                entry_idx = i

        return trades

    def calculate_performance_metrics(
        self, 
        trades: List[Trade],
        start_date: str,
        end_date: str,
        benchmark_ticker: str = "^VNI"
    ) -> BacktestResults:
        """Calculate comprehensive performance metrics

        Args:
            trades: List of executed trades
            start_date: Strategy start date
            end_date: Strategy end date
            benchmark_ticker: Benchmark ticker symbol

        Returns:
            BacktestResults with all metrics
        """
        if not trades:
            logger.warning("No trades to analyze")
            return self._empty_results()

        # Convert trades to DataFrame for analysis
        trades_df = pd.DataFrame([
            {
                'entry_date': t.entry_date,
                'exit_date': t.exit_date,
                'ticker': t.ticker,
                'signal': t.signal,
                'return_pct': t.return_pct,
                'holding_days': t.holding_days,
                'confidence': t.confidence
            }
            for t in trades
        ])

        # Strategy Performance
        strategy_returns = trades_df['return_pct'].values
        total_return = (1 + strategy_returns).prod() - 1

        # Annualized metrics
        days_total = (pd.to_datetime(end_date) - pd.to_datetime(start_date)).days
        years = days_total / 365.25
        annualized_return = (1 + total_return) ** (1/years) - 1 if years > 0 else 0
        volatility = np.std(strategy_returns) * np.sqrt(252) if len(strategy_returns) > 1 else 0
        sharpe_ratio = annualized_return / volatility if volatility > 0 else 0

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

        avg_win = trades_df[trades_df['return_pct'] > 0]['return_pct'].mean() if winning_trades > 0 else 0
        avg_loss = trades_df[trades_df['return_pct'] < 0]['return_pct'].mean() if losing_trades > 0 else 0
        profit_factor = (winning_trades * avg_win) / abs(losing_trades * avg_loss) if losing_trades > 0 and avg_loss != 0 else float('inf')

        # Benchmark comparison
        benchmark_return, beta, alpha = self._calculate_benchmark_metrics(
            strategy_returns, start_date, end_date, benchmark_ticker
        )
        excess_return = annualized_return - benchmark_return

        # Create equity curve
        equity_curve = self._create_equity_curve(trades_df)
        drawdown_curve = self._create_drawdown_curve(equity_curve)

        return BacktestResults(
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
            benchmark_return=benchmark_return,
            excess_return=excess_return,
            beta=beta,
            alpha=alpha,
            trades=trades,
            equity_curve=equity_curve,
            drawdown_curve=drawdown_curve
        )

    def _calculate_benchmark_metrics(
        self, 
        strategy_returns: np.ndarray,
        start_date: str,
        end_date: str,
        benchmark_ticker: str
    ) -> Tuple[float, float, float]:
        """Calculate benchmark comparison metrics"""
        try:
            # Download benchmark data
            benchmark = yf.download(benchmark_ticker, start=start_date, end=end_date, progress=False)
            benchmark_returns = benchmark['Adj Close'].pct_change().dropna().values

            if len(benchmark_returns) == 0:
                return 0.0, 0.0, 0.0

            # Align lengths
            min_len = min(len(strategy_returns), len(benchmark_returns))
            strategy_returns = strategy_returns[:min_len]
            benchmark_returns = benchmark_returns[:min_len]

            # Calculate metrics
            benchmark_total_return = (1 + benchmark_returns).prod() - 1

            # Beta and Alpha
            if len(strategy_returns) > 1 and len(benchmark_returns) > 1:
                covariance = np.cov(strategy_returns, benchmark_returns)[0, 1]
                benchmark_variance = np.var(benchmark_returns)
                beta = covariance / benchmark_variance if benchmark_variance > 0 else 0

                strategy_mean = np.mean(strategy_returns)
                benchmark_mean = np.mean(benchmark_returns)
                alpha = strategy_mean - beta * benchmark_mean
            else:
                beta = 0
                alpha = 0

            return benchmark_total_return, beta, alpha

        except Exception as e:
            logger.warning(f"Could not fetch benchmark data: {e}")
            return 0.0, 0.0, 0.0

    def _create_equity_curve(self, trades_df: pd.DataFrame) -> pd.DataFrame:
        """Create equity curve from trades"""
        trades_df_sorted = trades_df.sort_values('exit_date')
        cumulative_return = (1 + trades_df_sorted['return_pct']).cumprod()

        equity_curve = pd.DataFrame({
            'date': trades_df_sorted['exit_date'],
            'equity': cumulative_return,
            'return': trades_df_sorted['return_pct']
        })

        return equity_curve.reset_index(drop=True)

    def _create_drawdown_curve(self, equity_curve: pd.DataFrame) -> pd.DataFrame:
        """Create drawdown curve from equity curve"""
        running_max = equity_curve['equity'].expanding().max()
        drawdown = (equity_curve['equity'] - running_max) / running_max

        return pd.DataFrame({
            'date': equity_curve['date'],
            'drawdown': drawdown
        })

    def _empty_results(self) -> BacktestResults:
        """Return empty results when no trades"""
        return BacktestResults(
            total_return=0.0, annualized_return=0.0, volatility=0.0, sharpe_ratio=0.0, max_drawdown=0.0,
            total_trades=0, winning_trades=0, losing_trades=0, win_rate=0.0, avg_win=0.0, avg_loss=0.0, profit_factor=0.0,
            benchmark_return=0.0, excess_return=0.0, beta=0.0, alpha=0.0,
            trades=[], equity_curve=pd.DataFrame(), drawdown_curve=pd.DataFrame()
        )

    def run_backtest(
        self,
        test_data: pd.DataFrame,
        confidence_threshold: float = 0.6,
        holding_period: int = 10,
        transaction_cost: float = 0.001,
        benchmark_ticker: str = "^VNI"
    ) -> BacktestResults:
        """Run complete backtest

        Args:
            test_data: Test dataset with all features
            confidence_threshold: Minimum confidence for signal generation
            holding_period: Maximum holding period in days
            transaction_cost: Transaction cost as percentage
            benchmark_ticker: Benchmark for comparison

        Returns:
            BacktestResults object with all metrics
        """
        logger.info("Starting backtest...")

        # Generate trading signals
        signals = self.generate_signals(test_data, confidence_threshold)
        logger.info(f"Generated signals - Buy: {sum(signals['signal'] == 1)}, Sell: {sum(signals['signal'] == -1)}, Hold: {sum(signals['signal'] == 0)}")

        # Simulate trades
        trades = self.simulate_trades(
            test_data, signals, holding_period, transaction_cost
        )

        # Calculate performance metrics
        start_date = test_data['timestamp'].min()
        end_date = test_data['timestamp'].max()

        results = self.calculate_performance_metrics(
            trades, start_date, end_date, benchmark_ticker
        )

        logger.info("Backtest completed successfully")
        return results


def create_backtest_engine(model_path: str, scaler_path: str) -> BacktestEngine:
    """Create BacktestEngine instance

    Args:
        model_path: Path to trained model
        scaler_path: Path to feature scaler

    Returns:
        BacktestEngine instance
    """
    return BacktestEngine(model_path, scaler_path)
