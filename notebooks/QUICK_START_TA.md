# Quick Start - TA Rule-based System

## 🚀 Chạy nhanh trong 5 phút

### Bước 1: Stock Screening
```bash
cd notebooks/Code
jupyter notebook Filter_stock.ipynb
```

**Chạy các cells:**
1. Cell 1: Import libraries và define functions
2. Cell 2: Load data và run screening cho tất cả năm
3. Cell 3: Select top 5 stocks per year

**Kết quả:** Danh sách 5 cổ phiếu/năm (3 Growth + 2 Defensive)

### Bước 2: VSA Trading System
```bash
jupyter notebook Final_Algorithms.ipynb
```

**Chạy các cells:**
1. Cell 1-2: Import libraries và setup FiinQuantX
2. Cell 4: Define data fetching function
3. Cell 6: Define VSA signal generation
4. Cell 8: Define portfolio optimization
5. Cell 10-12: Define backtesting functions
6. Cell 18: Define main analysis function
7. Cell 19: Initialize client
8. Cell 21: Define configurations
9. Cell 23: **CHỌN NĂM VÀ CHẠY ANALYSIS**

### Bước 3: Chọn năm và chạy
```python
# Trong Cell 23, thay đổi:
YEAR_TO_ANALYZE = 2023  # Chọn 2021, 2022, hoặc 2023

# Chạy cell để xem kết quả
```

## 📊 Kết quả mong đợi

### 2023 Results
- **Portfolio Return**: 15.57%
- **VNINDEX Return**: 8.24%
- **Outperformance**: +7.33%
- **Max Drawdown**: 5.62%
- **Win Rate**: 60.78%

### 2022 Results  
- **Portfolio Return**: 39.34%
- **VNINDEX Return**: -33.99%
- **Outperformance**: +74.00%
- **Max Drawdown**: 29.33%
- **Win Rate**: 66.67%

### 2021 Results
- **Portfolio Return**: 45.64%
- **VNINDEX Return**: 33.72%
- **Outperformance**: +12.57%
- **Max Drawdown**: 21.74%
- **Win Rate**: 50.53%

## ⚙️ Tùy chỉnh nhanh

### Thay đổi confidence threshold
```python
# Trong generate_trade_signals()
min_true = 1  # Giảm để có nhiều signals hơn
```

### Thay đổi RSI thresholds
```python
rsi_buy_th = 35   # RSI mua
rsi_sell_th = 65  # RSI bán
```

### Thay đổi portfolio constraints
```python
target_return_range = (0.20, 0.25)  # Target return 20-25%
w_lower = 0.05    # Min 5% per stock
w_upper = 0.50    # Max 50% per stock
```

## 🎯 Tickers cho từng năm

### 2021
- **Growth**: IJC, TDC, PRE
- **Defensive**: VLC, FMC

### 2022  
- **Growth**: CTG, TNG, CSV
- **Defensive**: TDM, SJD

### 2023
- **Growth**: CTG, HDB, DRC
- **Defensive**: NT2, VPD

## 🚨 Troubleshooting nhanh

### Lỗi login FiinQuantX
```python
# Kiểm tra credentials trong Cell 2
username = 'DSTC_19@fiinquant.vn'
password = 'Fiinquant0606'
```

### Không có signals
```python
# Giảm min_true trong Cell 6
min_true = 1  # thay vì 2
```

### Portfolio optimization failed
```python
# Nới ràng buộc trong Cell 8
target_return_range = (0.15, 0.30)  # rộng hơn
```

## 📈 Performance Summary

| Năm | Market | Return | VNINDEX | Outperformance | Sharpe | Max DD |
|-----|--------|--------|---------|----------------|--------|--------|
| 2021 | Uptrend | 45.64% | 33.72% | +12.57% | 0.587 | -21.74% |
| 2022 | Downtrend | 39.34% | -33.99% | +74.00% | 0.134 | -29.33% |
| 2023 | Sideway | 167.86% | 8.24% | +163.50% | 3.718 | -7.05% |

**Best Performance**: 2023 với Sharpe ratio 3.718
**Most Robust**: 2022 với 74% excess return trong bear market
**Most Active**: 2021 với 95 trades

---

**Lưu ý**: Để hiểu chi tiết, xem [TA_RULE_BASED_GUIDE.md](TA_RULE_BASED_GUIDE.md)
