# Stock Signal Classification System

**Đội thi DataStorm**

| Thành viên | SBD | Email | Trường |
|------------|-------|-------|---------|
| Nguyễn Dương | B0261 | duongnguyen4823@gmail.com | Trường Đại học Công nghệ thông tin, ĐHQG TP.HCM |
| Nguyễn Hữu Kiên | B0118 | kiennh22414@st.uel.edu.vn | Trường Đại học Kinh tế - Luật, ĐHQG TP. HCM |
| Phan Nguyễn Tường Vy | B0111 | phannguyentuongvy972004@gmail.com | Trường Đại học Tôn Đức Thắng |


---

Hệ thống phân loại tín hiệu giao dịch chứng khoán với **2 approach chính**:

## 🎯 Tính năng chính

### 1. **ML-based Trading System** (Primary)
- **Event-driven Labeling**: Triple-barrier method với volatility scaling
- **Technical Indicators**: 30+ chỉ báo từ FiinQuantX (EMA, RSI, MACD, ATR, etc.)
- **XGBoost Model**: Với hyperparameter optimization và time-series CV
- **Automated Pipeline**: Từ raw data đến trained model
- **Comprehensive Backtesting**: Đánh giá hiệu suất với VN-Index benchmark

### 2. **Rule-based TA System** (Alternative)
- **VSA/Wyckoff Patterns**: Volume Spread Analysis với 8 pattern chính
- **Portfolio Optimization**: Quadratic programming với ràng buộc risk-return
- **Multi-timeframe Analysis**: Tín hiệu từ daily data với T+2 constraints
- **Dynamic Rebalancing**: Tối ưu trọng số danh mục theo market regime

### 3. **Stock Screening System** (Supporting)
- **Fundamental Filtering**: Market cap, EPS growth, PE/PB ratios
- **Sector Analysis**: PE comparison theo ngành ICB
- **Growth vs Defensive**: Phân loại cổ phiếu theo investment style
- **Multi-year Screening**: Lọc cổ phiếu cho 2020-2024

## 🚀 Khởi chạy nhanh

```bash
# Cài đặt dependencies
pip install -r requirements.txt

# Thiết lập credentials
cp env.example .env
# Edit .env file với credentials thực

# Chạy ML-based pipeline
python main.py

# Chạy backtesting (sau khi train model)
python backtest.py

# Chạy custom backtest với rule-based
python run_custom_backtest.py
```

## 📊 Cấu trúc dự án

```
stock-quant/
├── config/           # Cấu hình YAML
│   ├── data_config.yaml        # ML data & features
│   ├── labeling_config.yaml    # Triple-barrier config
│   └── model_config.yaml       # XGBoost config
├── src/              # ML-based system
│   ├── data/         # Data processing
│   ├── models/       # XGBoost trainer
│   ├── backtesting/  # Backtest engine
│   └── pipeline/     # End-to-end pipelines
├── notebooks/        # Rule-based & Screening
│   ├── Code/
│   │   ├── Filter_stock.ipynb      # Stock screening
│   │   └── Final_Algorithms.ipynb  # VSA/Wyckoff TA
│   └── Data/         # Historical data
├── data/             # Datasets (raw/processed/final)
├── models/           # Trained models 
├── results/          # Training & backtest results
└── main.py           # Entry point
```

## 🔄 Workflow tổng thể

### Phase 1: Stock Screening
```mermaid
flowchart TD
    A[Historical Data 2020-2024] --> B[Fundamental Screening]
    B --> C[Market Cap > 1B VND]
    C --> D[EPS Growth > 0]
    D --> E[PE < Sector Average]
    E --> F[PB 1-2, ROE > 15%]
    F --> G[Volume > 100k]
    G --> H[Top 5 Stocks/Year]
    H --> I[Growth vs Defensive Classification]
```

### Phase 2: ML-based Trading
```mermaid
flowchart TD
    A[Screened Stocks] --> B[Data Fetching - FiinQuantX]
    B --> C[Triple-barrier Labeling]
    C --> D[Feature Engineering - 30+ indicators]
    D --> E[XGBoost Training]
    E --> F[Hyperparameter Optimization]
    F --> G[Model Evaluation]
    G --> H[Backtesting]
```

### Phase 3: Rule-based Trading
```mermaid
flowchart TD
    A[Screened Stocks] --> B[VSA/Wyckoff Pattern Detection]
    B --> C[Signal Generation - RSI + Volume]
    C --> D[Portfolio Optimization - QP]
    D --> E[Risk Management - T+2]
    E --> F[Backtesting - Per-ticker]
    F --> G[Performance vs VNINDEX]
```

## 📈 Kết quả đạt được

### Stock Screening (2020-2024)
- **2020**: 21 cổ phiếu đạt tiêu chí
- **2021**: 22 cổ phiếu (Growth: IJC, TDC, PRE | Defensive: VLC, FMC)
- **2022**: 16 cổ phiếu (Growth: CTG, TNG, CSV | Defensive: TDM, SJD)
- **2023**: 13 cổ phiếu (Growth: CTG, HDB, DRC | Defensive: NT2, VPD)
- **2024**: 11 cổ phiếu (Growth: CTG, MBB, ACB | Defensive: QNS, MSH)

### Rule-based Backtest (2023)
- **Portfolio Return**: 15.57%
- **VNINDEX Return**: 8.24%
- **Outperformance**: +7.33%
- **Max Drawdown**: 5.62%
- **Win Rate**: 60.78%

## 🛠️ Tài liệu tham khảo

- **[SETUP.md](SETUP.md)**: Hướng dẫn setup nhanh cho người mới
- **[DOCUMENTATION.md](DOCUMENTATION.md)**: Chi tiết kỹ thuật ML pipeline
- **[TRADING_SYSTEMS.md](TRADING_SYSTEMS.md)**: So sánh ML vs Rule-based approaches
- **[Q&A.md](Q&A.md)**: Hỏi đáp chi tiết về hệ thống và troubleshooting
- **[BACKTEST_GUIDE.md](BACKTEST_GUIDE.md)**: Hướng dẫn backtesting và đánh giá hiệu suất
- **[planning.md](planning.md)**: Kế hoạch phát triển và technical approach

## 🎯 Performance Targets

### ML System
- **Accuracy**: >45% (random = 33% cho 3 classes)
- **Macro F1**: >0.4
- **Feature count**: 30-50 features

### Rule-based System  
- **Annual Return**: 15-25%
- **Sharpe Ratio**: >1.0
- **Max Drawdown**: <10%
- **Win Rate**: >55%

## 🔧 Cấu hình nâng cao

### ML System
Chỉnh sửa `config/` files:
- `data_config.yaml`: Tickers, timeframes, indicators
- `labeling_config.yaml`: Triple-barrier parameters
- `model_config.yaml`: XGBoost hyperparameters

### Rule-based System
Chỉnh sửa trong notebooks:
- VSA pattern thresholds
- Portfolio optimization constraints
- Risk management rules

## 📊 Monitoring & Evaluation

- **Real-time**: Model performance tracking
- **Backtesting**: Historical validation
- **Risk Metrics**: Drawdown, Sharpe, Sortino
- **Benchmark**: VNINDEX comparison
