# Thay đổi Backtest từ Daily sang 15-Minute

## 📋 Tổng quan thay đổi

Sau khi phân tích code backtest hiện tại, tôi đã tạo **4 files mới** tối ưu cho timeframe 15m:

### 🆕 Files mới được tạo:

1. **`src/backtesting/backtest_engine_15m.py`** - Engine tối ưu cho 15m
2. **`src/backtesting/backtest_runner_15m.py`** - Runner & reporting cho 15m  
3. **`run_custom_backtest_15m.py`** - Script chuẩn bị data 15m
4. **`backtest_15m.py`** - Main script chạy backtest 15m

## 🔧 Những thay đổi quan trọng

### 1. **Holding Period** - Thay đổi từ "days" sang "bars"
```python
# Daily (cũ)
holding_period: int = 10  # 10 ngày

# 15m (mới) 
holding_period_bars: int = 36  # 36 bars = ~2 ngày giao dịch (18 bars/ngày)
```

### 2. **Transaction Cost** - Giảm cho 15m frequency
```python
# Daily (cũ)
transaction_cost: float = 0.001  # 0.1%

# 15m (mới)
transaction_cost: float = 0.0005  # 0.05% (giảm do trade nhiều hơn)
```

### 3. **Confidence Threshold** - Tăng để lọc noise
```python
# Daily (cũ) 
confidence_threshold: float = 0.6

# 15m (mới)
confidence_threshold: float = 0.65  # Cao hơn để giảm noise intraday
```

### 4. **Volatility Calculation** - Điều chỉnh cho 15m
```python
# Daily (cũ)
volatility = np.std(returns) * np.sqrt(252)

# 15m (mới)
volatility = np.std(returns) * np.sqrt(252 * 18)  # 18 bars/day
```

### 5. **Trade Object** - Thêm metrics 15m
```python
@dataclass
class Trade15m:
    # ... existing fields ...
    holding_bars: int      # Số bars 15m giữ lệnh
    holding_days: float    # Số ngày thực tế (bars/18)
```

### 6. **Benchmark Handling** - Linh hoạt hơn
```python
def get_benchmark_returns_from_fiin_15m():
    try:
        # Thử lấy VNINDEX 15m
        benchmark = fetch_15m_data("VNINDEX")
    except:
        # Fallback về daily nếu không có 15m
        benchmark = fetch_daily_data("VNINDEX")
```

### 7. **Model Paths** - Trỏ đến models 15m
```python
# Daily (cũ)
model_path: "models/xgboost_model.pkl"
scaler_path: "models/feature_scaler.pkl"

# 15m (mới)
model_path: "models/xgboost_model_15m.pkl"  
scaler_path: "models/feature_scaler_15m.pkl"
```

## 🎯 Metrics mới cho 15m

### BacktestResults15m thêm:
- `avg_holding_bars`: Trung bình số bars giữ lệnh
- `avg_holding_days`: Trung bình số ngày giữ lệnh (bars/18)
- `trades_per_day`: Số trades trung bình mỗi ngày
- Hourly performance analysis
- Intraday pattern detection

### Reporting 15m bổ sung:
- **Holding Period Distribution**: Phân bố thời gian giữ lệnh
- **Hourly Performance**: Performance theo từng giờ trong ngày  
- **Trades by Hour**: Phân bố trades theo giờ
- **Confidence vs Performance**: Scatter plot confidence vs return

## 🚀 Cách sử dụng

### 1. Chuẩn bị data 15m:
```bash
python run_custom_backtest_15m.py
```

### 2. Train model 15m (nếu chưa có):
```bash
python main.py --config-dir config/15m
```

### 3. Chạy backtest 15m:
```bash
# Default
python backtest_15m.py

# Custom parameters  
python backtest_15m.py --confidence 0.7 --holding-period-bars 72 --transaction-cost 0.0003
```

## 📊 So sánh Daily vs 15m

| Aspect | Daily | 15m |
|--------|-------|-----|
| Holding Period | 10 days | 36 bars (~2 days) |
| Transaction Cost | 0.1% | 0.05% |
| Confidence | 0.6 | 0.65 |
| Data Points | ~250/year | ~4,500/year |
| Volatility Factor | √252 | √(252×18) |
| Trade Frequency | Lower | Higher |
| Noise Level | Lower | Higher |

## 🔍 Key Benefits của 15m Backtest

### ✅ Advantages:
- **More data**: 18x nhiều data points
- **Intraday patterns**: Capture được patterns trong ngày
- **Better entry/exit**: Precise timing hơn
- **Realistic simulation**: Gần với real trading hơn
- **Risk management**: Tighter stops, faster exits

### ⚠️ Considerations:
- **Higher noise**: Cần confidence threshold cao hơn
- **More complexity**: Phải handle intraday effects
- **Resource intensive**: Memory & processing cao hơn
- **Overfitting risk**: Nhiều data có thể lead to overfitting

## 💡 Best Practices cho 15m Backtest

1. **Start conservative**: Dùng confidence cao (≥0.65)
2. **Monitor holding periods**: Đảm bảo không quá ngắn/dài
3. **Watch transaction costs**: 15m trade nhiều → cost impact lớn
4. **Validate on multiple periods**: Test trên bull/bear/sideways markets
5. **Compare with daily**: Benchmark với daily results

## 🛠️ Files Structure

```
stock-quant/
├── src/backtesting/
│   ├── backtest_engine.py          # Daily version (existing)
│   ├── backtest_engine_15m.py      # 15m version (NEW)
│   ├── backtest_runner.py          # Daily version (existing)  
│   └── backtest_runner_15m.py      # 15m version (NEW)
├── backtest.py                     # Daily script (existing)
├── backtest_15m.py                 # 15m script (NEW)
├── run_custom_15m.py               # Daily data prep (existing)
└── run_custom_backtest_15m.py      # 15m data prep (NEW)
```

## 🎯 Next Steps

1. **Test 15m pipeline**: Chạy `python run_custom_backtest_15m.py`
2. **Train 15m model**: `python main.py --config-dir config/15m`
3. **Run 15m backtest**: `python backtest_15m.py`
4. **Compare results**: So sánh performance daily vs 15m
5. **Optimize parameters**: Fine-tune confidence, holding period, etc.

Với các files mới này, bạn có thể chạy backtest 15m hoàn toàn độc lập với daily version, với metrics và reporting được tối ưu riêng cho intraday trading! 