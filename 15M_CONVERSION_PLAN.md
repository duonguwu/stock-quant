# Kế hoạch chuyển đổi từ Chart 1D sang 15M

## 📋 Phân tích hiện trạng

### 1. Review Source Code
Sau khi phân tích toàn bộ source code, nhận thấy:

**✅ Code đã sẵn sàng cho timeframe khác:**
- `data_fetcher.py`: Parameter `timeframe` đã được implement đầy đủ trong `fetch_trading_data()`
- `feature_engineering.py`: Sử dụng period-based indicators, không hard-code theo ngày
- `labeling.py`: Parameter `N` (vertical barrier) là số bars, không phải số ngày
- `backtest_engine.py`: Xử lý theo timestamp, không phụ thuộc timeframe
- `main.py`: Hoàn toàn config-driven, không có hard-code timeframe

**🔧 Thay đổi cần thiết:**
- **CHỈ CẦN THAY ĐỔI CONFIG** - Source code đã flexible
- Điều chỉnh các parameters cho phù hợp với 15M data
- Tạo config set riêng biệt cho 15M

## 🎯 Kế hoạch chuyển đổi chi tiết

### Phase 1: Config Analysis & Adjustment

#### 1.1 Data Config Changes
**Từ 1D → 15M:**
```yaml
# data_config_15m.yaml
data:
  timeframe: "15m"  # Thay từ "1d"
  start_date: "2023-01-01"  # Thu hẹp thời gian (15M data rất lớn)
  end_date: "2024-12-31"
```

**Lý do thay đổi:**
- 15M data có volume lớn hơn ~25x so với 1D (1 ngày = ~25 bars 15M)
- Cần thu hẹp time range để tránh memory issues
- Performance fetch data sẽ chậm hơn đáng kể

#### 1.2 Labeling Config Adjustments
**Critical changes cho 15M:**
```yaml
# labeling_config_15m.yaml
labeling:
  vertical_barrier:
    days: 2  # Giảm từ 10 → 2 (48 bars thay vì 10 bars)
  
  barriers:
    tp_k: 1.5  # Giảm từ 2.0 (15M ít biến động hơn)
    sl_k: 1.0  # Giữ nguyên hoặc giảm nhẹ
  
  volatility:
    window: 96  # 96 bars 15M = 24 hours (thay vì 20 bars 1D)
  
  min_ret: 0.005  # Giảm từ 0.01 (15M có noise nhiều hơn)
```

**Reasoning:**
- **N=2 days**: Với 15M, holding 10 ngày = 960 bars (quá dài, model khó học)
- **Volatility window**: 96 bars 15M ≈ 1 day trading, tương đương 20 bars 1D  
- **TP/SL scale down**: 15M ít gap, biến động nhỏ hơn daily

#### 1.3 Model Config Optimizations
**Performance & Training adjustments:**
```yaml
# model_config_15m.yaml
model:
  training:
    n_estimators: 1000  # Giảm từ 2000 (data nhiều hơn)
    early_stopping_rounds: 50  # Giảm từ 100

cross_validation:
  n_splits: 3  # Giảm từ 5 (15M data có tính seasonal)
  test_size: 0.15  # Giảm từ 0.2

hyperopt:
  n_trials: 50  # Giảm từ 100 (tiết kiệm time)
  timeout: 1800  # 30 phút thay vì 1 giờ
```

### Phase 2: Feature Engineering Adjustments

#### 2.1 Technical Indicators Scaling
**Period adjustments cho 15M:**
```yaml
features:
  technical_indicators:
    # Trend - scale theo 15M
    ema_periods: [20, 40, 80, 200]  # Từ [5,10,20,50]
    sma_periods: [40, 80, 200]      # Từ [10,20,50]
    
    # MACD scaling
    macd:
      fast: 48   # 12 * 4 (4 bars/hour)
      slow: 104  # 26 * 4  
      signal: 36 # 9 * 4
    
    # Momentum indicators
    rsi_period: 56    # 14 * 4
    stoch_period: 56  # 14 * 4
    
    # Volatility
    bollinger:
      period: 80      # 20 * 4
      std_dev: 2
    atr_period: 56    # 14 * 4
    
    # Volume 
    mfi_period: 56    # 14 * 4
    vwap_period: 56   # 14 * 4

  price_features:
    returns_periods: [4, 20, 40, 80, 240, 480]  # 1H, 5H, 10H, 20H, 2.5D, 5D
    volatility_window: 80    # 20 * 4
    volume_ratio_window: 80  # 20 * 4

  regime_features:
    trend_window: 400        # 100 * 4 
    volatility_regime_window: 504  # 126 * 4
```

**Rationale:**
- **4x multiplier**: 4 bars 15M = 1 hour, tương đương tỷ lệ với daily
- **Returns periods**: Map sang timeframe 15M có ý nghĩa (1H, 5H, etc.)
- **Regime windows**: Giữ nguyên ý nghĩa time-wise

#### 2.2 Data Volume Considerations
**Memory & Performance:**
```yaml
# Trong data_config_15m.yaml
data:
  # Giới hạn tickers để tránh memory overflow
  custom_tickers: ['VCB', 'HPG', 'VIC', 'VNM', 'TCB']  # Giảm từ 14 → 5
  
  # Thu hẹp time range
  start_date: "2023-01-01"  # Thay vì 2016
  end_date: "2024-12-31"    # 2 năm data thay vì 6 năm
```

### Phase 3: Expected Benefits & Challenges

#### 3.1 Lợi ích của 15M
✅ **Data richness**: 25x nhiều data points hơn  
✅ **Pattern detection**: Capture intraday patterns, market microstructure  
✅ **Better labels**: Ít gap, ít noise từ overnight events  
✅ **Real-time applicable**: Model có thể trade intraday  
✅ **Volatility scaling**: Triple-barrier sẽ accurate hơn  

#### 3.2 Thách thức dự kiến
⚠️ **Memory usage**: 25x data → cần optimize pipeline  
⚠️ **Training time**: Tăng đáng kể (có thể 5-10x)  
⚠️ **Overfitting risk**: Nhiều data có thể lead to overfitting  
⚠️ **Market noise**: 15M có nhiều noise hơn daily  
⚠️ **Fetch time**: FiinQuantX API sẽ chậm hơn significantly  

### Phase 4: Implementation Steps

#### 4.1 Preparation
1. **Backup configs hiện tại**
2. **Test với data nhỏ** (1 ticker, 1 tháng)
3. **Monitor memory usage** during pipeline

#### 4.2 Execution Order
```bash
# Step 1: Tạo configs mới (done in next steps)
# Step 2: Test data pipeline
python main.py --data-only --config-dir config/15m

# Step 3: Validate labeling quality
python -c "
import pandas as pd
from src.data.labeling import analyze_labeling_quality
data = pd.read_csv('data/processed/labeled_data.csv')
print(analyze_labeling_quality(data, {}))
"

# Step 4: Feature engineering test
python main.py --training-only --config-dir config/15m

# Step 5: Full pipeline
python main.py --config-dir config/15m
```

#### 4.3 Validation Checkpoints
- [ ] Data fetch successful (< 30 phút cho 5 tickers)
- [ ] Memory usage < 8GB during pipeline  
- [ ] Label distribution reasonable (20-30% each class)
- [ ] Feature correlation matrix không có multicollinearity
- [ ] Model accuracy > 40% (baseline 33%)

### Phase 5: Performance Optimization

#### 5.1 Data Pipeline Optimizations
```python
# Trong data_pipeline.py - có thể cần thêm
def optimize_memory_usage(data):
    """Optimize memory by downcasting dtypes"""
    for col in data.select_dtypes(include=['float64']):
        data[col] = pd.to_numeric(data[col], downcast='float')
    return data
```

#### 5.2 Chunked Processing
Nếu memory issues:
```python
# Process by ticker chunks instead of all at once
for ticker in tickers:
    ticker_data = fetch_single_ticker(ticker)
    processed = process_ticker(ticker_data)
    save_interim(processed, ticker)
```

## 🎯 Kết luận

**Đánh giá khả thi: ✅ CAO**
- Source code đã sẵn sàng 100%
- Chỉ cần điều chỉnh configs
- Thách thức chính là performance & memory, không phải code logic

**Khuyến nghị implementation:**
1. **Start small**: Test với 1-2 tickers, 3 tháng data
2. **Gradual scaling**: Từ từ tăng lên full dataset
3. **Monitor resources**: RAM, CPU, disk space
4. **Parallel comparison**: Run cả 1D và 15M để so sánh performance

**Timeline ước tính:**
- Config setup: 30 phút
- Testing & validation: 2-3 giờ  
- Full pipeline first run: 4-6 giờ
- Optimization & tuning: 1-2 ngày

**Success metrics:**
- Model accuracy 15M > Model accuracy 1D
- Sharpe ratio cải thiện
- Drawdown giảm
- More stable label distribution 