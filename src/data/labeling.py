"""Triple-barrier labeling implementation"""

import numpy as np
import pandas as pd
from typing import Optional, Dict, Any
from loguru import logger


def rolling_volatility(close: pd.Series, window: int = 20, method: str = 'std') -> pd.Series:
    """Calculate rolling volatility for barrier scaling

    Args:
        close: Close price series
        window: Rolling window size
        method: Volatility method ('std' or 'atr')

    Returns:
        Volatility series
    """
    if method == 'std':
        returns = close.pct_change()
        return returns.rolling(window, min_periods=window//2).std()
    else:
        raise ValueError(f"Method {method} not implemented. Use 'std'.")


def event_driven_labels(
    df: pd.DataFrame,
    N: int = 20,
    tp_pct: Optional[float] = None,
    sl_pct: Optional[float] = None,
    tp_k: Optional[float] = None,
    sl_k: Optional[float] = None,
    vol: Optional[pd.Series] = None,
    vol_is_pct: bool = True,
    use_hl: bool = True,
    tie_policy: str = 'ambiguous',
    min_ret: Optional[float] = None
) -> pd.DataFrame:
    """
    Create event-driven labels using triple-barrier method

    Args:
        df: DataFrame with OHLC data
        N: Vertical barrier (maximum holding days)
        tp_pct: Fixed take profit percentage
        sl_pct: Fixed stop loss percentage  
        tp_k: Take profit volatility multiplier
        sl_k: Stop loss volatility multiplier
        vol: Volatility series
        vol_is_pct: Whether volatility is in percentage terms
        use_hl: Use high/low for barrier checking
        tie_policy: Policy when both barriers hit ('ambiguous', 'tp', 'sl', 'closest')
        min_ret: Minimum return for neutral zone

    Returns:
        DataFrame with labels and metadata
    """
    required_cols = ['close']
    if use_hl:
        required_cols.extend(['high', 'low'])

    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Required column '{col}' not found in DataFrame")

    close = df['close'].values
    high = df['high'].values if use_hl and 'high' in df else close
    low = df['low'].values if use_hl and 'low' in df else close
    openp = df['open'].values if 'open' in df else close

    n = len(df)
    labels = np.zeros(n, dtype=np.int8)
    hit_time = np.array([pd.NaT] * n, dtype='datetime64[ns]')
    hit_type = np.array(['none'] * n, dtype=object)
    ub_arr = np.full(n, np.nan)
    lb_arr = np.full(n, np.nan)
    end_time = np.array([pd.NaT] * n, dtype='datetime64[ns]')

    def barriers(i):
        """Calculate upper and lower barriers for position i"""
        p0 = close[i]

        # Upper barrier (take profit)
        if tp_pct is not None:
            ub = p0 * (1 + tp_pct)
        elif tp_k is not None and vol is not None and not np.isnan(vol.iloc[i]):
            if vol_is_pct:
                ub = p0 * (1 + tp_k * vol.iloc[i])
            else:
                ub = p0 + tp_k * vol.iloc[i]
        else:
            ub = np.inf

        # Lower barrier (stop loss)
        if sl_pct is not None:
            lb = p0 * (1 - sl_pct)
        elif sl_k is not None and vol is not None and not np.isnan(vol.iloc[i]):
            if vol_is_pct:
                lb = p0 * (1 - sl_k * vol.iloc[i])
            else:
                lb = p0 - sl_k * vol.iloc[i]
        else:
            lb = -np.inf

        return ub, lb

    idx = df.index

    # Process each bar (except last one)
    for i in range(n - 1):
        ub, lb = barriers(i)
        ub_arr[i], lb_arr[i] = ub, lb

        j_end = min(i + N, n - 1)
        decided = False

        # Check for barrier hits in future bars
        for j in range(i + 1, j_end + 1):
            touch_up = high[j] >= ub
            touch_dn = low[j] <= lb

            # Skip if no barriers defined
            if (ub == np.inf) and (lb == -np.inf):
                break

            # Single barrier hit
            if touch_up and not touch_dn:
                labels[i] = +1
                hit_type[i] = 'tp'
                hit_time[i] = idx[j]
                decided = True
                break

            if touch_dn and not touch_up:
                labels[i] = -1
                hit_type[i] = 'sl' 
                hit_time[i] = idx[j]
                decided = True
                break

            # Both barriers hit in same bar (tie)
            if touch_up and touch_dn:
                if tie_policy == 'ambiguous':
                    labels[i] = 0
                    hit_type[i] = 'both'
                elif tie_policy == 'tp':
                    labels[i] = +1
                    hit_type[i] = 'tp'
                elif tie_policy == 'sl':
                    labels[i] = -1
                    hit_type[i] = 'sl'
                elif tie_policy == 'closest':
                    # Use open price to determine closest barrier
                    du = abs(ub - openp[j])
                    dl = abs(openp[j] - lb)
                    if du < dl:
                        labels[i] = +1
                        hit_type[i] = 'tp'
                    elif dl < du:
                        labels[i] = -1
                        hit_type[i] = 'sl'
                    else:
                        labels[i] = 0
                        hit_type[i] = 'both'

                hit_time[i] = idx[j]
                decided = True
                break

        # Vertical barrier (time-based exit)
        if not decided:
            end_time[i] = idx[j_end]
            ret = close[j_end] / close[i] - 1.0

            if min_ret is not None and abs(ret) < min_ret:
                labels[i] = 0
                hit_type[i] = 'vbar_neutral'
            else:
                labels[i] = np.int8((ret > 0) - (ret < 0))
                hit_type[i] = 'vbar_sign'

            hit_time[i] = idx[j_end]

    # Create output DataFrame
    result = pd.DataFrame({
        'label': labels,
        'hit_time': hit_time,
        'hit_type': hit_type,
        'ub': ub_arr,
        'lb': lb_arr,
        'vbar_end': end_time
    }, index=df.index)

    return result


def apply_triple_barrier_labeling(
    data: pd.DataFrame,
    config: Dict[str, Any]
) -> pd.DataFrame:
    """Apply triple-barrier labeling to grouped data

    Args:
        data: DataFrame with OHLC data and ticker column
        config: Labeling configuration

    Returns:
        DataFrame with labels added
    """
    labeling_config = config.get('labeling', {})

    # Extract parameters
    N = labeling_config.get('vertical_barrier', {}).get('days', 10)
    barriers = labeling_config.get('barriers', {})
    tp_pct = barriers.get('tp_pct')
    sl_pct = barriers.get('sl_pct')
    tp_k = barriers.get('tp_k', 2.0)
    sl_k = barriers.get('sl_k', 1.0)

    vol_config = labeling_config.get('volatility', {})
    vol_window = vol_config.get('window', 20)
    vol_is_pct = vol_config.get('is_percentage', True)

    tie_policy = labeling_config.get('tie_policy', 'ambiguous')
    min_ret = labeling_config.get('min_ret', 0.002)
    use_hl = labeling_config.get('use_hl', True)

    def apply_labeling_to_ticker(df):
        """Apply labeling to single ticker data"""
        if len(df) < N + vol_window:
            logger.warning(f"Insufficient data for ticker, skipping labeling")
            return df

        # Calculate volatility
        vol = rolling_volatility(df['close'], window=vol_window)

        # Apply triple-barrier labeling
        labels = event_driven_labels(
            df=df,
            N=N,
            tp_pct=tp_pct,
            sl_pct=sl_pct, 
            tp_k=tp_k,
            sl_k=sl_k,
            vol=vol,
            vol_is_pct=vol_is_pct,
            use_hl=use_hl,
            tie_policy=tie_policy,
            min_ret=min_ret
        )

        # Join labels with original data
        return df.join(labels)

    if 'ticker' in data.columns:
        # Group by ticker and apply labeling
        logger.info("Applying triple-barrier labeling by ticker...")
        result = data.groupby('ticker', group_keys=False).apply(apply_labeling_to_ticker)
    else:
        # Single ticker data
        logger.info("Applying triple-barrier labeling to single ticker...")
        vol = rolling_volatility(data['close'], window=vol_window)
        labels = event_driven_labels(
            df=data,
            N=N,
            tp_pct=tp_pct,
            sl_pct=sl_pct,
            tp_k=tp_k, 
            sl_k=sl_k,
            vol=vol,
            vol_is_pct=vol_is_pct,
            use_hl=use_hl,
            tie_policy=tie_policy,
            min_ret=min_ret
        )
        result = data.join(labels)

    # Log label distribution
    if 'label' in result.columns:
        label_counts = result['label'].value_counts().sort_index()
        total = len(result.dropna(subset=['label']))

        logger.info("Label distribution:")
        for label, count in label_counts.items():
            pct = count / total * 100 if total > 0 else 0
            label_name = {-1: 'Sell', 0: 'Hold', 1: 'Buy'}.get(label, str(label))
            logger.info(f"  {label_name} ({label}): {count} ({pct:.1f}%)")

    return result


def analyze_labeling_quality(
    data: pd.DataFrame,
    config: Dict[str, Any]
) -> Dict[str, Any]:
    """Analyze quality of generated labels

    Args:
        data: DataFrame with labels
        config: Configuration

    Returns:
        Dictionary with quality metrics
    """
    if 'label' not in data.columns:
        raise ValueError("Data must contain 'label' column")

    # Remove NaN labels
    labeled_data = data.dropna(subset=['label'])

    if len(labeled_data) == 0:
        return {'error': 'No valid labels found'}

    # Label distribution
    label_counts = labeled_data['label'].value_counts().sort_index()
    total_labels = len(labeled_data)

    distribution = {}
    for label in [-1, 0, 1]:
        count = label_counts.get(label, 0)
        distribution[label] = {
            'count': int(count),
            'percentage': float(count / total_labels * 100)
        }

    # Hit type distribution
    hit_type_counts = labeled_data['hit_type'].value_counts()
    hit_type_dist = {str(k): int(v) for k, v in hit_type_counts.items()}

    # Expected vs actual distribution
    expected_dist = config.get('labels', {}).get('expected_distribution', {})

    quality_metrics = {
        'total_labels': int(total_labels),
        'label_distribution': distribution,
        'hit_type_distribution': hit_type_dist,
        'expected_distribution': expected_dist
    }

    # Balance score (how close to expected distribution)
    if expected_dist:
        balance_score = 0
        for label_name, expected_pct in expected_dist.items():
            label_map = {'sell': -1, 'hold': 0, 'buy': 1}
            label_val = label_map.get(label_name, 0)
            actual_pct = distribution.get(label_val, {}).get('percentage', 0) / 100
            balance_score += abs(expected_pct - actual_pct)

        quality_metrics['balance_score'] = float(balance_score / len(expected_dist))

    return quality_metrics
