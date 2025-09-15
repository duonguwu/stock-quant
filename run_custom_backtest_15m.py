import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from dotenv import load_dotenv

from src.data.data_fetcher import create_data_fetcher
from src.data.feature_engineering import create_feature_engineer
from src.utils.config_loader import ConfigLoader


def _ensure_backtest_data_dir() -> str:
    """Ensure backtest data directory exists for 15m"""
    base_dir = "data/backtest_data"
    os.makedirs(base_dir, exist_ok=True)
    return base_dir


def _unique_filename_15m(prefix: str = "custom_test_data_15m") -> str:
    """Generate unique filename for 15m backtest data"""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{ts}.csv"


def compute_backtest_window_15m(
    as_of_date: datetime, 
    max_window_bars: int = 504, 
    buffer_bars: int = 100, 
    bars_per_day: int = 18
):
    """
    Tính khoảng thời gian cần lấy dữ liệu cho backtest 15m.
    
    Args:
        as_of_date: Ngày kết thúc
        max_window_bars: Cửa sổ lớn nhất cho indicators (504 bar ~ 28 ngày giao dịch)
        buffer_bars: Thêm dự phòng (100 bar ~ 5.5 ngày giao dịch)
        bars_per_day: Số bar 15m trong 1 ngày giao dịch (≈18 bar)
        
    Returns:
        Tuple of (start_date, end_date) strings
    """
    total_bars = max_window_bars + buffer_bars
    need_days = int(np.ceil(total_bars / bars_per_day))  # số ngày giao dịch
    # Chuyển sang ngày lịch (cộng thêm cuối tuần/nghỉ lễ: ~1.4x)
    need_calendar_days = int(need_days * 1.4)
    start_date = as_of_date - timedelta(days=need_calendar_days)
    
    return start_date.strftime("%Y-%m-%d"), as_of_date.strftime("%Y-%m-%d")


def prepare_backtest_features_15m(
    username, password, tickers, start_date, end_date, config
):
    """
    Chuẩn bị features cho backtest 15m
    
    Args:
        username: FiinQuantX username
        password: FiinQuantX password
        tickers: List of ticker symbols
        start_date: Start date string
        end_date: End date string
        config: Configuration dictionary
        
    Returns:
        DataFrame with engineered features for 15m timeframe
    """
    # 1. Fetch raw 15m data
    fetcher = create_data_fetcher(username, password)
    
    try:
        data = fetcher.fetch_trading_data(
            tickers=tickers,
            fields=["open", "high", "low", "close", "volume", "bu", "sd"],
            start_date=start_date,
            end_date=end_date,
            timeframe="15m",
            adjusted=True,
        )
        data = fetcher.validate_data(data)
        
        if data.empty:
            raise ValueError("No 15m data retrieved from FiinQuantX")
            
        print(f"✅ Fetched {len(data)} rows of 15m data")
        print(f"📊 Date range: {data['timestamp'].min()} to {data['timestamp'].max()}")
        print(f"📈 Tickers: {data['ticker'].unique()}")
        
    except Exception as e:
        print(f"❌ Error fetching 15m data: {e}")
        raise

    # 2. Feature engineering for 15m
    feature_engineer = create_feature_engineer(fetcher.client)
    
    try:
        features = feature_engineer.engineer_features(data, config)
        print(f"✅ Generated {len(features.columns)} features for 15m data")
        
    except Exception as e:
        print(f"❌ Error in 15m feature engineering: {e}")
        raise
    
    return features


def validate_15m_features(features_df, reference_path=None):
    """
    Validate and align 15m features with reference dataset
    
    Args:
        features_df: DataFrame with engineered features
        reference_path: Path to reference dataset (optional)
        
    Returns:
        Validated and aligned features DataFrame
    """
    if reference_path and os.path.exists(reference_path):
        print(f"🔍 Validating against reference: {reference_path}")
        
        test_ref = pd.read_csv(reference_path)
        ignore_cols = ["label", "hit_time", "hit_type", "ub", "lb", "vbar_end"]
        feature_cols = [col for col in test_ref.columns if col not in ignore_cols]

        # Add missing columns with NaN
        missing_cols = set(feature_cols) - set(features_df.columns)
        if missing_cols:
            print(f"⚠️ Adding {len(missing_cols)} missing features: {list(missing_cols)[:5]}...")
            for col in missing_cols:
                features_df[col] = np.nan

        # Reorder columns to match reference
        common_cols = [col for col in feature_cols if col in features_df.columns]
        features_df = features_df[common_cols]
        
        print(f"✅ Features aligned: {len(common_cols)} columns")
        
    else:
        print(f"⚠️ No reference file found at {reference_path}, using current features.")
    
    return features_df


def analyze_15m_data_quality(features_df):
    """
    Analyze data quality for 15m features
    
    Args:
        features_df: DataFrame with features
    """
    print("\n📊 15m Data Quality Analysis:")
    print(f"Total rows: {len(features_df):,}")
    print(f"Total columns: {len(features_df.columns):,}")
    
    # Missing values analysis
    missing_pct = (features_df.isnull().sum() / len(features_df) * 100)
    high_missing = missing_pct[missing_pct > 10]
    
    if not high_missing.empty:
        print(f"⚠️ Features with >10% missing values: {len(high_missing)}")
        print(high_missing.head().to_dict())
    else:
        print("✅ No features with excessive missing values")
    
    # Infinite values check
    inf_cols = []
    for col in features_df.select_dtypes(include=[np.number]).columns:
        if np.isinf(features_df[col]).any():
            inf_cols.append(col)
    
    if inf_cols:
        print(f"⚠️ Features with infinite values: {len(inf_cols)}")
        print(inf_cols[:5])
    else:
        print("✅ No infinite values detected")
    
    # Time coverage
    if 'timestamp' in features_df.columns:
        time_range = pd.to_datetime(features_df['timestamp'])
        print(f"📅 Time coverage: {time_range.min()} to {time_range.max()}")
        print(f"📈 Trading days: ~{len(time_range.dt.date.unique())} days")
        print(f"⏰ Bars per day: ~{len(features_df) / len(time_range.dt.date.unique()):.1f}")


if __name__ == "__main__":
    load_dotenv()
    username = os.getenv("FIIN_USERNAME")
    password = os.getenv("FIIN_PASSWORD")
    
    if not username or not password:
        print("❌ FiinQuantX credentials not found in environment variables")
        exit(1)
    
    # 15m optimized ticker list (liquid stocks for better 15m data)
    tickers = ["VCB", "BID", "CTG", "MBB", "ACB", "HPG", "VIC", "VNM", "TCB"]
    
    # Determine backtest window (more recent for 15m)
    as_of_date = datetime.now()
    start_date, end_date = compute_backtest_window_15m(as_of_date)
    
    print(f"🚀 Preparing 15m backtest data for {len(tickers)} tickers")
    print(f"📅 Period: {start_date} to {end_date}")
    
    # Load 15m configs
    config_loader = ConfigLoader("config/15m")
    config = {}
    
    try:
        config.update(config_loader.load_config("data_config"))
        config.update(config_loader.load_config("labeling_config"))
        print("✅ Loaded 15m configurations")
    except Exception as e:
        print(f"❌ Error loading 15m configs: {e}")
        exit(1)
    
    # Feature engineering for 15m data
    try:
        features = prepare_backtest_features_15m(
            username, password, tickers, start_date, end_date, config
        )
        
        # Analyze data quality
        analyze_15m_data_quality(features)
        
        # Validate against reference if available
        ref_path = "data/final/test_data.csv"
        features = validate_15m_features(features, ref_path)
        
        # Save 15m backtest data
        out_dir = _ensure_backtest_data_dir()
        out_file = os.path.join(out_dir, _unique_filename_15m())
        features.to_csv(out_file, index=False)
        
        print(f"\n✅ 15m backtest data saved: {out_file}")
        print(f"📊 Final dataset: {len(features)} rows × {len(features.columns)} columns")
        print(f"🎯 Ready for 15m backtesting!")
        
        # Save a fixed name version for easy reference
        fixed_file = os.path.join(out_dir, "chart_15m_new.csv")
        features.to_csv(fixed_file, index=False)
        print(f"📌 Also saved as: {fixed_file}")
        
    except Exception as e:
        print(f"❌ Error in 15m data preparation: {e}")
        import traceback
        traceback.print_exc()
        exit(1) 