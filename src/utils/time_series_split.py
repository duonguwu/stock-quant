"""Time series cross-validation utilities"""

import numpy as np
import pandas as pd
from typing import List, Tuple, Generator
from sklearn.model_selection import BaseCrossValidator
from loguru import logger


class TimeSeriesSplit(BaseCrossValidator):
    """Time series cross-validator with walk-forward validation"""
    
    def __init__(
        self,
        n_splits: int = 5,
        test_size: float = 0.2,
        expanding_window: bool = True,
        min_train_size: int = 100,
        gap: int = 0
    ):
        """
        Args:
            n_splits: Number of splits
            test_size: Proportion of data for testing
            expanding_window: If True, use expanding window; if False, use sliding window
            min_train_size: Minimum training set size
            gap: Gap between train and test sets (for embargo)
        """
        self.n_splits = n_splits
        self.test_size = test_size
        self.expanding_window = expanding_window
        self.min_train_size = min_train_size
        self.gap = gap
    
    def split(
        self, X, y=None, groups=None
    ) -> Generator[Tuple[np.ndarray, np.ndarray], None, None]:
        """Generate train/test splits for time series data
        
        Args:
            X: Features
            y: Target (optional)
            groups: Group labels (optional)
            
        Yields:
            Tuple of (train_indices, test_indices)
        """
        n_samples = len(X)
        test_size = int(n_samples * self.test_size)
        
        # Calculate split points
        split_points = []
        for i in range(self.n_splits):
            test_start = n_samples - (self.n_splits - i) * test_size
            test_end = test_start + test_size
            
            if test_end > n_samples:
                test_end = n_samples
                test_start = test_end - test_size
            
            split_points.append((test_start, test_end))
        
        for i, (test_start, test_end) in enumerate(split_points):
            train_end = test_start - self.gap
            
            if self.expanding_window:
                # Expanding window: use all data from start
                train_start = 0
            else:
                # Sliding window: use fixed window size
                train_start = max(0, train_end - self.min_train_size)
            
            if train_end - train_start < self.min_train_size:
                logger.warning(f"Split {i}: Training size too small, skipping")
                continue
            
            train_indices = np.arange(train_start, train_end)
            test_indices = np.arange(test_start, test_end)
            
            logger.info(
                f"Split {i}: Train [{train_start}:{train_end}] "
                f"Test [{test_start}:{test_end}] "
                f"(Train size: {len(train_indices)}, Test size: {len(test_indices)})"
            )
            
            yield train_indices, test_indices
    
    def get_n_splits(self, X=None, y=None, groups=None) -> int:
        """Return number of splits"""
        return self.n_splits


class PurgedTimeSeriesSplit:
    """Time series split with purging for overlapping labels"""
    
    def __init__(
        self,
        n_splits: int = 5,
        test_size: float = 0.2,
        purge_length: int = 0,
        embargo_length: int = 0
    ):
        """
        Args:
            n_splits: Number of splits
            test_size: Proportion of data for testing
            purge_length: Number of samples to purge after test set
            embargo_length: Number of samples to embargo before test set
        """
        self.n_splits = n_splits
        self.test_size = test_size
        self.purge_length = purge_length
        self.embargo_length = embargo_length
    
    def split(
        self,
        X: pd.DataFrame,
        y: pd.Series = None,
        pred_times: pd.Series = None,
        eval_times: pd.Series = None
    ) -> Generator[Tuple[np.ndarray, np.ndarray], None, None]:
        """Generate purged train/test splits
        
        Args:
            X: Features with datetime index
            y: Target series
            pred_times: Prediction times (when prediction is made)
            eval_times: Evaluation times (when outcome is known)
            
        Yields:
            Tuple of (train_indices, test_indices)
        """
        if pred_times is None:
            pred_times = X.index
        if eval_times is None:
            eval_times = X.index
        
        n_samples = len(X)
        test_size = int(n_samples * self.test_size)
        
        indices = np.arange(n_samples)
        
        for i in range(self.n_splits):
            # Calculate test set boundaries
            test_start = n_samples - (self.n_splits - i) * test_size
            test_end = min(test_start + test_size, n_samples)
            
            test_indices = indices[test_start:test_end]
            
            # Get test period boundaries
            test_start_time = pred_times.iloc[test_start]
            test_end_time = eval_times.iloc[test_end - 1]
            
            # Calculate train set with purging and embargo
            train_indices = []
            
            for idx in indices:
                pred_time = pred_times.iloc[idx]
                eval_time = eval_times.iloc[idx]
                
                # Skip if prediction overlaps with test period
                if pred_time >= test_start_time and pred_time <= test_end_time:
                    continue
                
                # Skip if evaluation overlaps with test period (purging)
                if eval_time >= test_start_time and eval_time <= test_end_time:
                    continue
                
                # Apply embargo: skip if too close to test period
                if abs((pred_time - test_start_time).days) <= self.embargo_length:
                    continue
                
                train_indices.append(idx)
            
            train_indices = np.array(train_indices)
            
            if len(train_indices) == 0:
                logger.warning(f"Split {i}: No training samples after purging")
                continue
            
            logger.info(
                f"Purged Split {i}: Train size: {len(train_indices)}, "
                f"Test size: {len(test_indices)}"
            )
            
            yield train_indices, test_indices


def create_time_series_splits(
    data: pd.DataFrame,
    config: dict
) -> List[Tuple[np.ndarray, np.ndarray]]:
    """Create time series splits based on configuration
    
    Args:
        data: DataFrame with datetime index
        config: Configuration dictionary
        
    Returns:
        List of (train_indices, test_indices) tuples
    """
    cv_config = config.get('cross_validation', {})
    method = cv_config.get('method', 'time_series')
    
    if method == 'time_series':
        cv = TimeSeriesSplit(
            n_splits=cv_config.get('n_splits', 5),
            test_size=cv_config.get('test_size', 0.2),
            expanding_window=cv_config.get('expanding_window', True),
            min_train_size=cv_config.get('min_train_size', 100)
        )
    elif method == 'purged':
        cv = PurgedTimeSeriesSplit(
            n_splits=cv_config.get('n_splits', 5),
            test_size=cv_config.get('test_size', 0.2),
            purge_length=cv_config.get('purge_length', 0),
            embargo_length=cv_config.get('embargo_length', 0)
        )
    else:
        raise ValueError(f"Unknown CV method: {method}")
    
    splits = list(cv.split(data))
    logger.info(f"Created {len(splits)} time series splits using {method} method")
    
    return splits 