# Hướng dẫn Backtesting

## Tổng quan

Backtesting system đánh giá hiệu suất trading strategy của mô hình ML đã train, bao gồm:

- **Tỷ suất sinh lời (Return)**
- **Số giao dịch (Number of trades)**  
- **Tỷ lệ thắng (Win-rate)**
- **Max Drawdown**
- **So sánh với VN-Index benchmark**

## Yêu cầu trước khi chạy

1. **Model đã được train:**
   ```bash
   # Kiểm tra model files
   ls -la models/
   # Expected: xgboost_model.pkl, feature_scaler.pkl
   ```

2. **Test data đã được tạo:**
   ```bash
   # Kiểm tra test data
   ls -la data/final/test_data.csv
   ```

3. **Dependencies đã cài đặt:**
   ```bash
   pip install matplotlib seaborn python-dotenv FiinQuantX loguru
   ```

## Cách sử dụng

### 1. Chạy backtest cơ bản

```bash
python backtest.py
```

### 2. Tùy chỉnh parameters

```bash
# Confidence threshold cao hơn (ít trade hơn, chất lượng cao hơn)
python backtest.py --confidence 0.7

# Holding period khác
python backtest.py --holding-period 15

# Transaction cost khác  
python backtest.py --transaction-cost 0.002

# Output directory tùy chỉnh
python backtest.py --output results/my_backtest
```

### 3. Sử dụng model khác

```bash
python backtest.py --model models/my_model.pkl --scaler models/my_scaler.pkl
```

## Kết quả Output

### Files được tạo:

```
results/backtest/
├── backtest_summary.md        # Báo cáo tóm tắt
├── backtest_metrics.json      # Metrics dạng JSON
├── backtest_charts.png        # Biểu đồ phân tích
├── detailed_trades.csv        # Chi tiết từng giao dịch
├── equity_curve.csv          # Đường cong equity
└── drawdown_curve.csv        # Đường cong drawdown
```

### Metrics chính:

#### **Performance Metrics:**
- **Total Return**: Tổng lợi nhuận
- **Annualized Return**: Lợi nhuận hàng năm
- **Volatility**: Độ biến động
- **Sharpe Ratio**: Tỷ lệ return/risk
- **Max Drawdown**: Thua lỗ tối đa

#### **Trading Statistics:**
- **Total Trades**: Tổng số giao dịch
- **Win Rate**: Tỷ lệ thắng
- **Avg Win/Loss**: Lãi/lỗ trung bình
- **Profit Factor**: Tỷ lệ tổng lãi/tổng lỗ

#### **Benchmark Comparison:**
- **Benchmark Return**: Return của VN-Index
- **Excess Return**: Return vượt trội so với benchmark
- **Beta**: Hệ số beta với thị trường
- **Alpha**: Alpha (risk-adjusted excess return)

## Giải thích Strategy Logic

### Signal Generation:
1. **Model prediction**: XGBoost predict Buy/Hold/Sell
2. **Confidence filtering**: Chỉ trade khi confidence > threshold
3. **Signal mapping**: 
   - `1` = Buy (Long)
   - `-1` = Sell (Short)
   - `0` = Hold (No position)

### Trade Execution:
1. **Entry**: Khi có signal mới và không có position
2. **Exit conditions**:
   - Max holding period reached
   - Signal thay đổi
   - Nhận signal Hold
3. **Return calculation**: Include transaction costs

### Risk Management:
- **Position sizing**: Equal weight cho tất cả trades
- **Transaction costs**: Default 0.1% per trade
- **No leverage**: Chỉ trade với capital có sẵn

## Example Results

```
📊 BACKTEST RESULTS SUMMARY
============================================================
💰 Total Return: 15.23%
📈 Annualized Return: 12.45%
📉 Max Drawdown: -8.32%
📊 Sharpe Ratio: 1.245
🎯 Total Trades: 156
✅ Win Rate: 58.33%
🏆 Profit Factor: 1.89
📊 VN-Index Return: 8.76%
💎 Excess Return: 3.69%
============================================================
```

## Interpreting Results

### Good Performance Indicators:
- **Sharpe Ratio > 1.0**: Risk-adjusted return tốt
- **Win Rate > 50%**: Nhiều trade thắng hơn thua
- **Profit Factor > 1.5**: Lãi nhiều hơn lỗ đáng kể
- **Max Drawdown < 15%**: Risk control tốt
- **Excess Return > 0**: Beat benchmark

### Warning Signs:
- **Too few trades** (<20): Model quá conservative
- **Too many trades** (>500): Có thể overtrading
- **High drawdown** (>20%): Risk management kém
- **Low win rate** (<45%): Signal quality thấp

## Optimization Suggestions

### Improve Win Rate:
```bash
# Tăng confidence threshold
python backtest.py --confidence 0.75
```

### Reduce Drawdown:
```bash
# Giảm holding period
python backtest.py --holding-period 5
```

### Increase Trading Frequency:
```bash
# Giảm confidence threshold  
python backtest.py --confidence 0.55
```

## Advanced Analysis

### 1. Parameter Sensitivity Analysis

```bash
# Test multiple confidence levels
for conf in 0.5 0.6 0.7 0.8; do
    python backtest.py --confidence $conf --output "results/backtest_conf_$conf"
done
```

### 2. Holding Period Analysis

```bash
# Test different holding periods
for days in 5 10 15 20; do
    python backtest.py --holding-period $days --output "results/backtest_hold_$days"
done
```

### 3. Compare với Buy & Hold

```bash
# Tính Buy & Hold return cho comparison
python -c "
import yfinance as yf
import pandas as pd

# Download VN-Index data
vni = yf.download('^VNI', start='2024-01-01', end='2024-12-31')
buy_hold_return = (vni['Adj Close'][-1] / vni['Adj Close'][0] - 1) * 100
print(f'VN-Index Buy & Hold Return: {buy_hold_return:.2f}%')
"
```

## Troubleshooting

### Lỗi thường gặp:

1. **"Model file not found"**
   ```bash
   # Train model trước
   python main.py
   ```

2. **"Test data not found"**
   ```bash
   # Tạo test data
   python main.py --data-only
   ```

3. **"No trades generated"**
   - Giảm confidence threshold
   - Kiểm tra signal distribution
   - Đảm bảo test data có đủ features

4. **Memory error with large datasets**
   ```bash
   # Giảm test data size hoặc batch processing
   head -1000 data/final/test_data.csv > data/final/test_data_small.csv
   python backtest.py --test-data data/final/test_data_small.csv
   ```

## Best Practices

1. **Always compare** với benchmark (VN-Index)
2. **Test multiple parameters** để tìm optimal settings
3. **Consider transaction costs** realistic (0.1-0.3%)
4. **Watch out for overfitting** trong parameter tuning
5. **Validate results** với out-of-sample data

## Next Steps

Sau khi có kết quả backtest tốt:

1. **Paper trading**: Test với real-time data
2. **Strategy refinement**: Optimize parameters
3. **Risk management**: Add position sizing, stop losses
4. **Production deployment**: Automate signal generation 

---

# Bổ sung: Tạo dữ liệu test theo khoảng thời gian mong muốn

Script `run_custom_backtest.py` cho phép chọn danh sách mã, khoảng thời gian và tạo
file test data mới trong thư mục `data/backtest_data` với tên duy nhất (timestamp),
không ghi đè file cũ.

```bash
python run_custom_backtest.py
# Output: data/backtest_data/custom_test_data_YYYYMMDD_HHMMSS.csv
```

Sau khi tạo file, dùng tham số `--test-data` để chỉ định file khi chạy backtest:

```bash
python backtest.py \
  --test-data data/backtest_data/custom_test_data_YYYYMMDD_HHMMSS.csv
```

# Bổ sung: Thư mục kết quả backtest tự tăng (backtest_N)

Khi chạy `backtest.py`, hệ thống tự động tạo thư mục kết quả mới dạng `backtest_N`
trong `results/backtest` (hoặc base dir bạn chỉ định qua `--output`). Ví dụ:

```
results/backtest/
├── backtest_1/
├── backtest_2/
└── backtest_3/
```

Trong mỗi thư mục có kèm `config.md` ghi rõ cấu hình chạy (model, scaler, test data,
confidence, holding period, transaction cost, timestamp) để bạn dễ truy vết.

# Bổ sung: Gợi ý cửa sổ dữ liệu (WINDOW) cho Production/Backtest

Dựa theo thiết kế features, cửa sổ lớn nhất cần để tính đầy đủ feature là:

- EMA/SMA: tối đa 50
- MACD (slow): 26 (≤ 50)
- Bollinger: 20
- Price Returns: 120
- Regime trend: 100
- Volatility regime: 126 (LỚN NHẤT)

Khuyến nghị:
- Dự phòng ngày nghỉ/sàn lỗi: cộng thêm buffer 10–20 ngày.
- Nếu dự báo cho ngày D, nên lấy dữ liệu từ: **D − 146 ngày đến D**
  (126 + ~20 ngày buffer, ~5 tháng gần nhất).

Công thức tổng quát:

```
start_date = as_of_date − (max_window + buffer)
end_date   = as_of_date
# Với max_window = 126, buffer ≈ 20 → tổng ≈ 146 ngày
``` 