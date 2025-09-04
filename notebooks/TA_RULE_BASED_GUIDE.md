# Hướng dẫn TA Rule-based Trading System

## Tổng quan

Hệ thống TA Rule-based sử dụng **VSA/Wyckoff patterns** kết hợp với **Portfolio Optimization** để tạo ra trading signals và quản lý danh mục đầu tư.

## 🎯 Mục tiêu bài toán

### 1. **Stock Screening**
- Lọc cổ phiếu tiềm năng từ universe lớn (1600+ stocks)
- Áp dụng tiêu chí fundamental: market cap, EPS growth, PE/PB ratios
- Phân loại theo investment style: Growth vs Defensive

### 2. **VSA/Wyckoff Pattern Detection**
- Phát hiện 8 patterns chính: 4 Signs of Strength (SOS) + 4 Signs of Weakness (SOW)
- Kết hợp với RSI để tăng độ chính xác
- State machine logic: BUY đầu tiên bắt buộc, SELL phải cách BUY ít nhất T+2

### 3. **Portfolio Optimization**
- Quadratic Programming để tối ưu trọng số danh mục
- Ràng buộc risk-return: target return 20-25%, max drawdown <10%
- Dynamic rebalancing theo market regime

### 4. **Backtesting & Performance**
- Đánh giá hiệu suất vs VNINDEX benchmark
- Risk metrics: Sharpe ratio, max drawdown, win rate
- Transaction costs: 0.1% per trade

## 📁 Cấu trúc Files

```
notebooks/
├── Code/
│   ├── Filter_stock.ipynb          # Stock screening system
│   ├── Final_Algorithms.ipynb      # VSA/Wyckoff + Portfolio optimization
│   └── data.ipynb                  # Data preprocessing
├── Data/
│   ├── 2020.csv                    # Fundamental data 2020
│   ├── 2021.csv                    # Fundamental data 2021
│   ├── 2022.csv                    # Fundamental data 2022
│   ├── 2023.csv                    # Fundamental data 2023
│   └── 2024.csv                    # Fundamental data 2024
└── TA_RULE_BASED_GUIDE.md          # This guide
```

## 🚀 Hướng dẫn chạy từng bước

### Bước 1: Stock Screening

#### 1.1 Mở notebook Filter_stock.ipynb
```bash
cd notebooks/Code
jupyter notebook Filter_stock.ipynb
```

#### 1.2 Chạy stock screening
```python
# Cell 1: Import libraries và define functions
import pandas as pd
import numpy as np

# Cell 2: Load data và run screening
df24 = pd.read_csv("../Data/2024.csv")
df23 = pd.read_csv("../Data/2023.csv")
df22 = pd.read_csv("../Data/2022.csv")
df21 = pd.read_csv("../Data/2021.csv")
df20 = pd.read_csv("../Data/2020.csv")

# Tạo dictionary
dataframes = {
    2020: df20,
    2021: df21,
    2022: df22,
    2023: df23,
    2024: df24
}

# Lọc cổ phiếu cho tất cả năm
screening_results = screen_multiple_years(dataframes)

# Cell 3: Select top 5 stocks per year
top5_each_year = select_top5_for_all_years(screening_results, n_growth=3, n_defensive=2)
```

#### 1.3 Kết quả Stock Screening
```
=== KẾT QUẢ LỌC CỔ PHIẾU NĂM 2021 ===
Growth: ['IJC', 'TDC', 'PRE']
Defensive: ['VLC', 'FMC']

=== KẾT QUẢ LỌC CỔ PHIẾU NĂM 2022 ===
Growth: ['CTG', 'TNG', 'CSV']
Defensive: ['TDM', 'SJD']

=== KẾT QUẢ LỌC CỔ PHIẾU NĂM 2023 ===
Growth: ['CTG', 'HDB', 'DRC']
Defensive: ['NT2', 'VPD']
```

### Bước 2: VSA/Wyckoff Trading System

#### 2.1 Mở notebook Final_Algorithms.ipynb
```bash
jupyter notebook Final_Algorithms.ipynb
```

#### 2.2 Setup FiinQuantX Client
```python
# Cell 1: Import libraries
import numpy as np
import pandas as pd
import cvxpy as cp
import matplotlib.pyplot as plt
from backtesting import Backtest, Strategy
from FiinQuantX import FiinSession

# Cell 2: Setup FiinQuantX
def setup_fiinquant_client():
    username = 'DSTC_19@fiinquant.vn'
    password = 'Fiinquant0606'
    client = FiinSession(username=username, password=password).login()
    return client

client = setup_fiinquant_client()
```

#### 2.3 Fetch Data và Calculate Indicators
```python
# Cell 4: Define data fetching function
def fetch_stock_data(client, tickers, from_date, to_date):
    # Lấy dữ liệu OHLCV
    df = client.Fetch_Trading_Data(
        realtime=False,
        tickers=tickers,    
        fields=['open', 'high', 'low', 'close', 'volume'],
        adjusted=True,
        by='1d', 
        from_date=from_date,
        to_date=to_date,
    ).get_data()
    
    # Tính RSI
    fi = client.FiinIndicator()
    df['rsi'] = fi.rsi(df['close'], window=14)
    
    return df
```

#### 2.4 VSA Pattern Detection
```python
# Cell 6: Define VSA signal generation
def generate_trade_signals(df, min_true=1, rsi_buy_th=35, rsi_sell_th=65):
    """
    Tín hiệu Wyckoff/VSA + RSI
    - Tín hiệu đầu tiên bắt buộc là BUY
    - SELL phải cách lần BUY gần nhất ít nhất T+2 phiên
    """
    # VSA features calculation
    # Bar type: up, down, flat
    # Volume type: low, medium, high  
    # Spread type: low, medium, high
    # Close position: bottom, middle, top third
    
    # SOS patterns (Signs of Strength)
    power_a = ((bar=="up") & (spread=="high") & (volume in ["medium","high"]) & (close=="top"))
    force_b = ((bar=="down") & (spread in ["medium","high"]) & (volume=="high") & (close=="bottom"))
    reverse_upthrust = ((spread=="high") & (volume=="high") & (close=="top"))
    selling_climax = ((bar=="down") & (spread=="high") & (volume=="high") & (close=="middle"))
    
    # SOW patterns (Signs of Weakness)  
    weakness_a = ((bar=="down") & (volume=="high") & (spread in ["low","medium"]) & (close in ["middle","bottom"]))
    no_demand = ((bar=="up") & (volume=="low") & (spread in ["low","medium"]) & (close in ["middle","top"]))
    upthrust = ((bar=="up") & (spread=="high") & (close=="bottom") & (volume in ["medium","high"]))
    buying_climax = ((bar=="up") & (spread=="high") & (volume=="high") & (close=="middle"))
    
    # Calculate scores
    buy_score = sos_patterns.sum(axis=1) + (rsi < rsi_buy_th)
    sell_score = sow_patterns.sum(axis=1) + (rsi > rsi_sell_th)
    
    # State machine logic
    # 1. Chỉ chấp nhận BUY đầu tiên
    # 2. Sau đó cho phép BUY/SELL nhiều lần  
    # 3. SELL phải cách BUY ít nhất T+2
    
    return df_with_signals
```

#### 2.5 Portfolio Optimization
```python
# Cell 8: Define portfolio optimization
def optimize_portfolio_weights(df, tickers, capital_vnd=1_000_000_000):
    """
    Quadratic Programming optimization
    Objective: Min w^T Σ w (minimize portfolio variance)
    Constraints:
    - sum(w) = 1
    - w_lower ≤ w ≤ w_upper  
    - r_20d @ w ≥ 0 (short-term positive)
    - r_60d @ w ≥ 0 (medium-term positive)
    - mu_ann @ w ∈ [0.20, 0.25] (annual return target)
    """
    # Prepare returns matrix
    px = df.pivot(index="timestamp", columns="ticker", values="close")
    ret = px.pct_change().dropna()
    
    # Annualized returns and covariance
    mu_ann = (1.0 + ret).prod(axis=0) ** (252.0 / len(ret)) - 1.0
    Sigma_ann = (ret.cov() * 252.0).values
    
    # Setup optimization problem
    w = cp.Variable(len(tickers))
    constraints = [
        cp.sum(w) == 1,
        w >= 0.05,  # min 5% per stock
        w <= 0.50,  # max 50% per stock
        mu_ann @ w >= 0.20,  # target return
        mu_ann @ w <= 0.25,
    ]
    
    objective = cp.Minimize(cp.quad_form(w, Sigma_ann))
    prob = cp.Problem(objective, constraints)
    prob.solve()
    
    return weights_df, portfolio_info
```

#### 2.6 Backtesting
```python
# Cell 10-12: Define backtesting functions
class SignalStrategy(Strategy):
    def init(self):
        pass
    
    def next(self):
        sig = int(self.data.Signal[-1])
        if sig == 1 and not self.position:
            # Buy logic
            budget = self.equity * 0.999
            size = int(budget // self.data.Close[-1])
            if size > 0:
                self.buy(size=size)
        elif sig == -1 and self.position.is_long:
            # Sell logic
            self.position.close()

def backtest_portfolio(df, weights_df, capital_vnd=1_000_000_000):
    """Backtest portfolio với optimized weights"""
    # Run backtest for each stock
    # Combine results into portfolio performance
    # Compare with VNINDEX benchmark
    return summary, per_ticker_stats, portfolio_curve
```

### Bước 3: Chạy Complete Analysis

#### 3.1 Cấu hình cho từng năm
```python
# Cell 21: Define configurations
CONFIGS = {
    2021: {
        'tickers': ['IJC', 'TDC', 'PRE', 'VLC', 'FMC'], 
        'capital': 1_000_000_000,
        'description': 'Portfolio 2021'
    },
    2022: {
        'tickers': ['CTG', 'TNG', 'CSV', 'TDM', 'SJD'], 
        'capital': 1_000_000_000,
        'description': 'Portfolio 2022'
    },
    2023: {
        'tickers': ['CTG', 'HDB', 'DRC','NT2', 'VPD'], 
        'capital': 1_000_000_000,
        'description': 'Portfolio 2023'
    }
}
```

#### 3.2 Chạy analysis cho năm cụ thể
```python
# Cell 23: Run analysis
YEAR_TO_ANALYZE = 2023  # Chọn năm muốn phân tích

config = CONFIGS[YEAR_TO_ANALYZE]
tickers = config['tickers']
capital = config['capital']

# Chạy phân tích hoàn chỉnh
results = run_complete_analysis(
    client=client,
    tickers=tickers,
    year=YEAR_TO_ANALYZE,
    capital_vnd=capital
)
```

## 📊 Kết quả mong đợi

### Portfolio Performance (2023)
```
============================================================
RUNNING COMPLETE ANALYSIS FOR 2023
Tickers: ['CTG', 'HDB', 'DRC', 'NT2', 'VPD']
Capital: 1,000,000,000 VND
============================================================

Portfolio Optimization Results:
  ticker  weight  capital_alloc  last_price  shares_est
0    HDB  0.3288      328757235    16247.81       20200
1    CTG  0.2363      236288044    27100.00        8700
2    VPD  0.2180      217951430    20619.23       10500
3    DRC  0.1372      137178881    19078.81        7100
4    NT2  0.0798       79824411    22918.33        3400

========================================
PORTFOLIO BACKTEST RESULTS
========================================
Portfolio Return [%]: 15.57
Portfolio Max Drawdown [%]: 5.62
Total Trades: 51
Win Rate [%] (est.): 60.78

PER-TICKER PERFORMANCE:
     Return[%]  Trades  WinRate[%]  MaxDD[%]
HDB      30.22     7.0      100.00     13.57
CTG      -8.36    11.0       45.45     21.21
VPD      20.45    14.0       64.29     12.20
DRC      22.93    10.0       60.00     12.42
NT2       0.06     9.0       44.44     13.46

Hiệu suất danh mục: 15.57%
Hiệu suất VNINDEX: 8.24%
Outperformance: 7.33%
```

## 🔧 Tùy chỉnh Parameters

### 1. VSA Pattern Thresholds
```python
# Trong generate_trade_signals()
vol_lo = 0.85      # Volume low threshold
vol_hi = 1.2       # Volume high threshold  
spr_lo = 0.8       # Spread low threshold
spr_hi = 1.2       # Spread high threshold
spr_lookback = 20  # Spread lookback period
```

### 2. RSI Parameters
```python
rsi_buy_th = 35    # RSI buy threshold
rsi_sell_th = 65   # RSI sell threshold
```

### 3. Portfolio Optimization
```python
target_return_range = (0.20, 0.25)  # 20-25% annual return
w_lower = 0.05     # Min 5% per stock
w_upper = 0.50     # Max 50% per stock
lookback_days = 180 # 180 days for optimization
```

### 4. Risk Management
```python
tplus2_bars = 2    # T+2 constraint for SELL
min_true = 1       # Minimum patterns to trigger signal
commission = 0.001 # 0.1% transaction cost
```

## 🎯 Performance Targets

### Expected Results
- **Annual Return**: 15-25%
- **Sharpe Ratio**: >1.0
- **Max Drawdown**: <10%
- **Win Rate**: >55%
- **Outperformance vs VNINDEX**: >5%

### Risk Metrics
- **Beta**: 0.5-1.5 (moderate market correlation)
- **Volatility**: 15-25% (reasonable risk level)
- **Profit Factor**: >1.5 (lãi > lỗ)

## 🚨 Troubleshooting

### Lỗi thường gặp

1. **FiinQuantX login failed**
   ```python
   # Kiểm tra credentials
   username = 'DSTC_19@fiinquant.vn'
   password = 'Fiinquant0606'
   ```

2. **No signals generated**
   ```python
   # Giảm min_true threshold
   min_true = 1  # thay vì 2
   
   # Điều chỉnh RSI thresholds
   rsi_buy_th = 40  # thay vì 35
   rsi_sell_th = 60  # thay vì 65
   ```

3. **Portfolio optimization failed**
   ```python
   # Nới ràng buộc
   target_return_range = (0.15, 0.30)  # rộng hơn
   w_lower = 0.02  # thấp hơn
   ```

4. **Memory issues**
   ```python
   # Giảm lookback period
   lookback_days = 90  # thay vì 180
   
   # Giảm số tickers
   tickers = tickers[:3]  # chỉ 3 tickers
   ```

## 📈 Next Steps

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

## 📚 Tài liệu tham khảo

- **VSA Theory**: Volume Spread Analysis by Tom Williams
- **Wyckoff Method**: The Wyckoff Method by Richard Wyckoff
- **Portfolio Optimization**: Modern Portfolio Theory by Markowitz
- **FiinQuantX**: Official documentation

---

**Lưu ý**: Hệ thống này được thiết kế cho educational purposes. Trước khi sử dụng với real money, cần paper trading và extensive testing.
