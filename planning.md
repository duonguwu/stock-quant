## 📊 Tổng quan Dự án

### Mục tiêu
Xây dựng hệ thống phân loại tín hiệu giao dịch (signal classification) sử dụng:
- **Event-driven labeling** với triple-barrier method
- **Volatility-scaled barriers** để ổn định nhãn
- **XGBoost** cho mô hình phân loại
- **FiinQuantX** cho data pipeline và technical indicators

### Đầu ra Mong đợi
- Mô hình XGBoost đã train (`.pkl` file)
- Dataset đã xử lý (`.csv` files)
- Pipeline tự động hóa từ raw data → prediction
- Báo cáo đánh giá mô hình (metrics + backtest)

## 🏗️ Cấu trúc Thư mục

```
stock-quant/
├── config/
│   ├── model_config.yaml          # Hyperparameters XGBoost
│   ├── data_config.yaml           # Tickers, timeframes, features
│   └── labeling_config.yaml       # Triple-barrier parameters
├── data/
│   ├── raw/                       # Raw OHLCV từ FiinQuantX
│   ├── processed/                 # Features + labels
│   └── final/                     # Train/val/test splits
├── src/
│   ├── data/
│   │   ├── __init__.py
│   │   ├── data_fetcher.py        # FiinQuantX data retrieval
│   │   ├── feature_engineering.py # Technical indicators
│   │   └── labeling.py            # Triple-barrier implementation
│   ├── models/
│   │   ├── __init__.py
│   │   ├── xgboost_trainer.py     # XGBoost training pipeline
│   │   └── model_evaluation.py    # Metrics + backtesting
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── config_loader.py       # YAML config management
│   │   └── time_series_split.py   # Walk-forward validation
│   └── pipeline/
│       ├── __init__.py
│       ├── data_pipeline.py       # End-to-end data processing
│       └── training_pipeline.py   # Model training workflow
├── models/
│   ├── xgboost_model.pkl         # Trained model
│   └── feature_scaler.pkl        # Fitted scaler
├── notebooks/
│   ├── 01_data_exploration.ipynb
│   ├── 02_labeling_analysis.ipynb
│   └── 03_model_evaluation.ipynb
├── results/
│   ├── model_metrics.json
│   ├── feature_importance.png
│   └── backtest_results.csv
├── main.py                        # Entry point
├── requirements.txt
└── README.md
```

## 🔧 Công nghệ và Kỹ thuật Sử dụng

### 1. Data Pipeline (FiinQuantX)
- **Fetch_Trading_Data**: OHLCV + volume mua/bán chủ động
- **FiinIndicator**: Technical indicators (EMA, RSI, MACD, ADX, etc.)
- **TickerList**: VN30/VN100 universe
- **Adjusted pricing**: Điều chỉnh cổ tức/chia tách

### 2. Feature Engineering
- **Price features**: Returns, rolling statistics
- **Technical indicators**: 15+ indicators từ FiinQuantX
- **Volume features**: BU/SD ratio, OBV, VWAP
- **Volatility features**: ATR, Bollinger width
- **Regime features**: Market state indicators

### 3. Event-driven Labeling (Triple-barrier)
- **Volatility-scaled barriers**: TP = P₀(1 + k_tp × σ), SL = P₀(1 - k_sl × σ)
- **Vertical barrier**: N ngày maximum holding
- **Tie handling**: Ambiguous policy khi chạm cả TP và SL
- **Min return threshold**: Vùng chết cho neutral labels

### 4. Model Training
- **XGBoost**: Tree-based ensemble với early stopping
- **Walk-forward validation**: Time-series cross-validation
- **Class balancing**: Sample weights cho imbalanced labels
- **Hyperparameter tuning**: Optuna optimization

### 5. Evaluation Framework
- **Classification metrics**: Precision/Recall/F1 per class
- **Economic metrics**: Sharpe ratio, max drawdown, profit factor
- **Backtest simulation**: Event-driven exits với transaction costs

## 📋 Implementation Plan

### Phase 1: Data Infrastructure (1-2 ngày)
1. **Setup FiinQuantX connection**
   - Credentials management
   - Error handling cho API calls
   
2. **Data fetching pipeline**
   - Multi-ticker OHLCV retrieval
   - Technical indicators calculation
   - Data validation và quality checks

3. **Triple-barrier labeling**
   - Implementation từ README.md pseudocode
   - Volatility calculation (rolling std)
   - Label distribution analysis

### Phase 2: Feature Engineering (1 ngày)
1. **Technical indicators** (15+ features)
   - Trend: EMA, SMA, MACD, ADX
   - Momentum: RSI, Stochastic
   - Volatility: Bollinger, ATR, Supertrend
   - Volume: MFI, OBV, VWAP

2. **Advanced features**
   - Price momentum (1,5,10,20 days)
   - Volatility-of-volatility
   - Volume z-scores
   - Cross-asset correlations (VN-Index)

### Phase 3: Model Development (2 ngày)
1. **XGBoost implementation**
   - Multi-class classification (Buy/Hold/Sell)
   - Walk-forward validation
   - Feature importance analysis

2. **Hyperparameter optimization**
   - Grid search cho (N, k_tp, k_sl) trong labeling
   - XGBoost params: learning_rate, max_depth, subsample
   - Early stopping để tránh overfitting

### Phase 4: Evaluation & Backtesting (1 ngày)
1. **Model evaluation**
   - Classification report
   - Confusion matrix
   - ROC curves per class

2. **Economic backtesting**
   - Event-driven exits (matching labeling logic)
   - Transaction costs (0.15% mỗi chiều)
   - Portfolio metrics (Sharpe, Sortino, MDD)

## 🛠️ Technical Implementation Details

### Key Libraries
```python
# Core ML
import xgboost as xgb
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import classification_report

# Data processing  
import pandas as pd
import numpy as np
from FiinQuantX import FiinSession

# Optimization
import optuna
import yaml

# Visualization
import matplotlib.pyplot as plt
import seaborn as sns
```

### Model Configuration (XGBoost)
```yaml
xgboost:
  objective: "multi:softprob"
  num_class: 3
  learning_rate: 0.1
  max_depth: 6
  subsample: 0.8
  colsample_bytree: 0.8
  random_state: 42
  early_stopping_rounds: 50
```

### Labeling Configuration
```yaml
triple_barrier:
  N: 10                    # Vertical barrier (days)
  tp_k: 2.0               # Take profit multiplier
  sl_k: 1.0               # Stop loss multiplier
  vol_window: 20          # Volatility lookback
  min_ret: 0.002          # Minimum return threshold
  tie_policy: "ambiguous" # TP+SL tie handling
```

## 📈 Expected Outcomes

### Model Performance Targets
- **Accuracy**: >45% (random = 33% cho 3 classes)
- **Sharpe Ratio**: >1.0 trong backtest
- **Max Drawdown**: <15%
- **Hit Rate**: >50% cho Buy/Sell signals

### Key Deliverables
1. **Trained XGBoost model** với feature importance
2. **Processed dataset** với 30+ features
3. **Backtest report** với economic metrics
4. **Production pipeline** để realtime prediction

## 🚀 Next Steps

1. **Start với Phase 1**: Setup data pipeline
2. **Validate labeling**: Kiểm tra label distribution và quality
3. **Baseline model**: Simple XGBoost với default params
4. **Iterative improvement**: Feature selection + hyperparameter tuning
5. **Production deployment**: Realtime pipeline với FiinQuantX streaming

---

**Ưu điểm của approach này:**
- ✅ Sử dụng tối đa FiinQuantX capabilities
- ✅ Event-driven labeling realistic với trading practice
- ✅ Volatility-scaling cho stable labels across market regimes
- ✅ End-to-end pipeline từ raw data đến model deployment
- ✅ Economic validation thay vì chỉ statistical metrics</parameter>
</invoke>