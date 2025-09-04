# Q&A - Hỏi đáp về Stock Signal Classification System

## 1. Tính toán Technical Indicators như thế nào?

**Tính toán cái gì?**
Technical indicators là các chỉ báo kỹ thuật được tính từ dữ liệu giá OHLCV:

- **Trend indicators**: EMA (5,10,20,50), SMA (10,20,50), MACD, ADX
- **Momentum indicators**: RSI (14), Stochastic (14)
- **Volatility indicators**: Bollinger Bands, ATR
- **Volume indicators**: MFI, OBV, VWAP

**Tính xong dùng để làm gì?**
Các indicators này trở thành features (đặc trưng) để train mô hình ML:
- RSI > 70 → có thể quá mua
- MACD cắt lên → tín hiệu tăng giá
- Bollinger Bands → đo độ biến động
- Volume indicators → đo dòng tiền

**Cấu hình:**
Trong `config/data_config.yaml`:
```yaml
features:
  technical_indicators:
    ema_periods: [5, 10, 20, 50]
    rsi_period: 14
    bollinger:
      period: 20
      std_dev: 2
```

## 2. Feature Engineering là làm gì?

**Mục đích:** Chuyển đổi dữ liệu thô thành features có ý nghĩa cho mô hình ML.

**Quá trình xử lý:**
1. **Technical Indicators**: Tính 30+ chỉ báo từ FiinQuantX
2. **Price Features**: Returns, volatility, gap, high-low ratio
3. **Volume Features**: Volume ratios, z-scores, active trading (BU/SD)
4. **Market Regime**: Trend regime, volatility regime
5. **Momentum Features**: ROC, cumulative returns, price rank

**Có cần thiết không?**
Rất cần thiết! Raw price data không đủ thông tin:
- Giá 100k hôm nay có cao không? → Cần so với MA
- Có đột biến volume không? → Cần volume ratio
- Thị trường đang trending hay sideway? → Cần regime features

## 3. XGBoost Model Configuration

**Thông số chính:**
```yaml
xgboost:
  objective: "multi:softprob"  # 3-class classification
  num_class: 3                 # Buy/Hold/Sell
  learning_rate: 0.1
  max_depth: 6
  subsample: 0.8
  colsample_bytree: 0.8
  
training:
  n_estimators: 1000
  early_stopping_rounds: 50
  class_weight: "balanced"     # Handle imbalanced labels
```

**Tại sao XGBoost?**
- Hiệu quả với tabular data
- Handle missing values tự động
- Feature importance built-in
- Ít overfitting hơn deep learning

## 4. Hướng dẫn sử dụng data_config.yaml

**Cho người không biết lập trình:**

**Theo dõi 10 cổ phiếu cụ thể:**
```yaml
data:
  universe: null  # Tắt universe
  custom_tickers: ["VCB", "HPG", "VIC", "VNM", "TCB", "BID", "CTG", "VRE", "MSN", "PLX"]
```

**Thay đổi thời gian:**
```yaml
data:
  start_date: "2022-01-01"  # Từ ngày
  end_date: null            # Đến hiện tại
```

**Train 1 lúc hay riêng lẻ?**
Train 1 lút tất cả 10 cổ phiếu trong cùng 1 model:
- Features được tính riêng cho từng mã
- Labels được tính riêng cho từng mã  
- Model học pattern chung từ tất cả

## 5. python main.py --data-only tạo ra file gì?

**Có, tạo ra các file CSV:**

```
data/
├── raw/
│   └── trading_data.csv          # OHLCV raw data
├── processed/
│   ├── labeled_data.csv          # Data + labels
│   └── featured_data.csv         # Data + features + labels
└── final/
    ├── final_dataset.csv         # Cleaned final data
    ├── train_data.csv           # Training set
    ├── val_data.csv             # Validation set
    └── test_data.csv            # Test set
```

**Từng file chứa gì:**
- `trading_data.csv`: OHLCV + volume BU/SD
- `labeled_data.csv`: + nhãn Buy/Hold/Sell
- `featured_data.csv`: + 30+ technical indicators
- `final_dataset.csv`: Đã clean, ready for ML

## 6. Volatility là gì và ứng dụng

**Volatility là gì?**
Độ biến động giá - đo bằng standard deviation của returns:
```python
returns = close.pct_change()
volatility = returns.rolling(20).std()
```

**Ứng dụng trong project:**
1. **Volatility-scaled barriers**: TP/SL thích ứng với độ biến động
   - Thị trường biến động cao → barriers rộng hơn
   - Thị trường ổn định → barriers hẹp hơn
   
2. **Feature engineering**: Volatility là feature quan trọng
3. **Risk management**: Đo rủi ro của strategy

**Ích lợi:**
- Labels ổn định hơn across market regimes
- Tránh overfitting với fixed % barriers
- Realistic với thực tế trading

## 7. Market Regime là gì?

**Market Regime:** Trạng thái thị trường hiện tại.

**Trong project tính toán:**

**Trend Regime:**
```python
trend_sma = close.rolling(50).mean()
above_trend = (close > trend_sma).astype(int)  # 1=uptrend, 0=downtrend
```

**Volatility Regime:**
```python
vol = returns.rolling(252).std()
# 0=low vol, 1=medium vol, 2=high vol
vol_regime = pd.cut(vol, bins=[0, 33%, 67%, 100%], labels=[0,1,2])
```

**Ứng dụng:**
- Model học được patterns khác nhau cho từng regime
- Bull market vs Bear market có signals khác nhau
- High vol vs Low vol có risk tolerance khác nhau

## 8. Kết quả tốt là như thế nào?

**Metrics quan tâm nhất:**

1. **Accuracy**: >45% (random baseline = 33%)
2. **Macro F1**: >0.4 (balanced across 3 classes)
3. **Precision/Recall per class**: Đặc biệt quan tâm Buy/Sell precision
4. **Feature Importance**: Top features có ý nghĩa không?

**Cách cải thiện:**

**Data Quality:**
- Tăng training data (thêm years)
- Thêm features (more indicators)
- Check data leakage

**Model Tuning:**
- Hyperparameter optimization
- Ensemble methods
- Feature selection

**Labeling:**
- Adjust TP/SL ratios
- Try different N (holding period)
- Experiment với tie_policy

## 9. Accuracy >45% có ý nghĩa gì?

**Random baseline = 33%:**
Với 3 classes (Buy/Hold/Sell), đoán ngẫu nhiên có accuracy = 1/3 = 33%.

**45% có ý nghĩa:**
- Cao hơn random 12 percentage points
- Model đã học được patterns
- Nhưng vẫn còn room for improvement

**Tại sao target 45%?**
- Realistic cho financial time series
- Higher accuracy có thể là overfitting
- Focus vào economic metrics (Sharpe ratio) quan trọng hơn

**Trong thực tế:**
- 45% accuracy với good risk management có thể profitable
- 80% accuracy với poor risk management có thể loss money

## 10. Thêm Features mới - add_custom_features

**Mục đích:**
Thêm domain-specific features mà standard indicators không cover.

**Khi nào cần thêm:**

**Market microstructure:**
```python
def add_custom_features(self, data):
    # Bid-ask spread proxy
    data['spread_proxy'] = (data['high'] - data['low']) / data['close']
    
    # Intraday momentum
    data['intraday_ret'] = (data['close'] - data['open']) / data['open']
    
    # Volume acceleration
    data['volume_accel'] = data['volume'].pct_change()
    
    return data
```

**Sector/Macro features:**
- VN-Index correlation
- USD/VND exchange rate
- Interest rates
- Sector rotation signals

**Khi nào cần:**
- Model performance plateau
- Missing important market dynamics
- Domain expertise suggests new patterns

## 11. Cách sử dụng Config Files

**Nguyên tắc:**
1. **Không sửa code** - chỉ sửa config
2. **Test với data nhỏ** trước khi full run
3. **Backup config** trước khi thay đổi

**Workflow:**
```bash
# 1. Copy default config
cp config/data_config.yaml config/data_config_backup.yaml

# 2. Edit config
# Sửa universe, tickers, dates...

# 3. Test với data nhỏ
python main.py --data-only

# 4. Check results
ls data/raw/  # Có file trading_data.csv không?

# 5. Full run
python main.py
```

---

## Câu hỏi thêm cho người Non-Tech

### 12. Làm thế nào để biết model đang hoạt động?

**Check logs:**
```bash
tail -f logs/pipeline.log
```

**Check file outputs:**
- `data/` folder có files không?
- `models/` có model.pkl không?
- `results/` có metrics.json không?

### 13. Lỗi thường gặp và cách fix

**"FiinQuantX login failed":**
```bash
# Check credentials
echo $FIIN_USERNAME
echo $FIIN_PASSWORD
```

**"Insufficient data":**
- Giảm `start_date` trong config
- Giảm `technical_indicators` windows

**"Memory error":**
- Giảm số tickers
- Increase `missing_threshold`

### 14. Model prediction có ý nghĩa gì?

**Output:** Xác suất cho 3 classes
```
Probability: [0.2, 0.6, 0.2]
Classes:     [Sell, Hold, Buy]
→ Prediction: Hold (60% confidence)
```

**Cách interpret:**
- High confidence (>70%): Strong signal
- Low confidence (<40%): Unclear, nên Hold
- Balance giữa accuracy và actionability

### 15. Khi nào nên retrain model?

**Định kỳ:**
- Mỗi quarter (3 tháng)
- Khi có data mới đáng kể

**Khi performance giảm:**
- Accuracy drop >5%
- Sharpe ratio giảm
- Drawdown tăng

**Market regime change:**
- Bull → Bear market
- Low vol → High vol period
- Major economic events 