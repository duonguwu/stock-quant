# Notebooks - TA Rule-based Trading System

## 📁 Cấu trúc thư mục

```
notebooks/
├── README.md                    # This file
├── TA_RULE_BASED_GUIDE.md      # Hướng dẫn chi tiết
├── QUICK_START_TA.md           # Hướng dẫn chạy nhanh
├── Code/
│   ├── Filter_stock.ipynb      # Stock screening system
│   ├── Final_Algorithms.ipynb  # VSA/Wyckoff + Portfolio optimization
│   └── data.ipynb              # Data preprocessing
└── Data/
    ├── 2020.csv                # Fundamental data 2020
    ├── 2021.csv                # Fundamental data 2021
    ├── 2022.csv                # Fundamental data 2022
    ├── 2023.csv                # Fundamental data 2023
    ├── 2024.csv                # Fundamental data 2024
    └── data.xlsx               # Combined data
```

## 🎯 Mục tiêu hệ thống

### 1. **Stock Screening**
- Lọc 1600+ cổ phiếu xuống còn 5-20 cổ phiếu/năm
- Tiêu chí: Market cap >1B, EPS growth >0, PE < sector avg, PB 1-2, ROE >15%
- Phân loại: 3 Growth + 2 Defensive stocks

### 2. **VSA/Wyckoff Trading**
- 8 patterns: 4 Signs of Strength + 4 Signs of Weakness
- Kết hợp RSI để tăng độ chính xác
- State machine: BUY đầu tiên bắt buộc, SELL cách BUY ít nhất T+2

### 3. **Portfolio Optimization**
- Quadratic Programming với ràng buộc risk-return
- Target: 20-25% annual return, max 10% drawdown
- Dynamic rebalancing theo market regime

### 4. **Backtesting**
- Đánh giá vs VNINDEX benchmark
- Risk metrics: Sharpe, max drawdown, win rate
- Transaction costs: 0.1% per trade

## 🚀 Bắt đầu nhanh

### Option 1: Quick Start (5 phút)
```bash
# Xem hướng dẫn chạy nhanh
cat QUICK_START_TA.md

# Chạy stock screening
cd Code
jupyter notebook Filter_stock.ipynb

# Chạy VSA trading system  
jupyter notebook Final_Algorithms.ipynb
```

### Option 2: Chi tiết (30 phút)
```bash
# Xem hướng dẫn đầy đủ
cat TA_RULE_BASED_GUIDE.md

# Follow step-by-step instructions
```

## 📊 Kết quả đạt được

### Stock Screening (2020-2024)
| Năm | Tổng stocks | Sau screening | Growth | Defensive |
|-----|-------------|---------------|---------|-----------|
| 2020 | 1,664 | 21 | 3 | 2 |
| 2021 | 1,664 | 22 | 3 | 2 |
| 2022 | 1,664 | 16 | 3 | 2 |
| 2023 | 1,662 | 13 | 3 | 2 |
| 2024 | 1,662 | 11 | 3 | 2 |

### Trading Performance
| Năm | Market | Return | VNINDEX | Outperformance | Sharpe | Max DD |
|-----|--------|--------|---------|----------------|--------|--------|
| 2021 | Uptrend | 45.64% | 33.72% | +12.57% | 0.587 | -21.74% |
| 2022 | Downtrend | 39.34% | -33.99% | +74.00% | 0.134 | -29.33% |
| 2023 | Sideway | 167.86% | 8.24% | +163.50% | 3.718 | -7.05% |

## 🔧 Tùy chỉnh

### Stock Screening Parameters
```python
# Trong Filter_stock.ipynb
market_cap_min = 1000000000  # 1B VND
eps_growth_min = 0.0
pe_max_ratio = 1.0  # vs sector average
pb_min, pb_max = 1.0, 2.0
roe_min = 0.15
volume_min = 100000
```

### VSA Trading Parameters
```python
# Trong Final_Algorithms.ipynb
vol_lo, vol_hi = 0.85, 1.2
spr_lo, spr_hi = 0.8, 1.2
rsi_buy_th, rsi_sell_th = 35, 65
min_true = 1
tplus2_bars = 2
```

### Portfolio Optimization
```python
target_return_range = (0.20, 0.25)  # 20-25%
w_lower, w_upper = 0.05, 0.50  # 5-50% per stock
lookback_days = 180
bank_rate = 0.10
```

## 📈 Key Insights

### 1. Market Regime Adaptation
- **Uptrend**: Confidence thấp (0.4), nhiều trades (95)
- **Downtrend**: Confidence cao (0.8), ít trades (6) nhưng chất lượng cao
- **Sideway**: Confidence trung bình (0.5), balanced approach (76 trades)

### 2. Risk Management
- **2023**: Negative beta (-0.125) - hedge market risk
- **Drawdown Control**: Tốt nhất trong sideway market (7.05%)
- **Consistent Outperformance**: Vượt benchmark trong mọi điều kiện

### 3. Strategy Effectiveness
- **VSA Patterns**: Hiệu quả trong mọi market regime
- **Portfolio Optimization**: Tối ưu risk-return trade-off
- **State Machine**: Tránh false signals và overtrading

## 🚨 Troubleshooting

### Common Issues
1. **FiinQuantX login failed**: Kiểm tra credentials
2. **No signals generated**: Giảm min_true threshold
3. **Portfolio optimization failed**: Nới ràng buộc
4. **Memory issues**: Giảm lookback period hoặc số tickers

### Solutions
- Xem chi tiết trong `TA_RULE_BASED_GUIDE.md`
- Check logs trong notebook outputs
- Adjust parameters theo market conditions

## 📚 Tài liệu tham khảo

- **[TA_RULE_BASED_GUIDE.md](TA_RULE_BASED_GUIDE.md)**: Hướng dẫn chi tiết đầy đủ
- **[QUICK_START_TA.md](QUICK_START_TA.md)**: Hướng dẫn chạy nhanh
- **VSA Theory**: Volume Spread Analysis by Tom Williams
- **Wyckoff Method**: The Wyckoff Method by Richard Wyckoff
- **Portfolio Optimization**: Modern Portfolio Theory by Markowitz

## 🎯 Next Steps

### 1. Parameter Optimization
- Test different VSA thresholds
- Optimize RSI parameters  
- Fine-tune portfolio constraints

### 2. Advanced Features
- Multi-timeframe analysis
- Dynamic position sizing
- Risk parity allocation

### 3. Production Deployment
- Real-time data feeds
- Automated signal generation
- Risk monitoring system

---

**Lưu ý**: Hệ thống này được thiết kế cho educational purposes. Trước khi sử dụng với real money, cần paper trading và extensive testing.
