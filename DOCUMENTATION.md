# Stock Signal Classification System

Hệ thống phân loại tín hiệu giao dịch chứng khoán sử dụng Machine Learning với FiinQuantX.

## Mục tiêu

Xây dựng mô hình ML để dự đoán tín hiệu giao dịch (Buy/Hold/Sell) dựa trên:
- Event-driven labeling với triple-barrier method
- Technical indicators từ FiinQuantX
- XGBoost classifier với hyperparameter optimization

## Cấu trúc dự án

```
stock-quant/
├── config/                     # File cấu hình YAML
│   ├── data_config.yaml        # Cấu hình data & features
│   ├── labeling_config.yaml    # Cấu hình triple-barrier
│   └── model_config.yaml       # Cấu hình XGBoost
├── src/                        # Source code
│   ├── data/                   # Data processing modules
│   ├── models/                 # ML models
│   ├── utils/                  # Utilities
│   └── pipeline/               # End-to-end pipelines
├── data/                       # Datasets
│   ├── raw/                    # Raw OHLCV data
│   ├── processed/              # Features + labels
│   └── final/                  # Train/val/test splits
├── models/                     # Trained models
├── results/                    # Training results
└── main.py                     # Entry point
```

## Cài đặt

### 1. Requirements

```bash
pip install -r requirements.txt
```

### 2. Cấu hình FiinQuantX

**Cách 1: Sử dụng file .env (Khuyến nghị)**

```bash
# Copy file template
cp env.example .env

# Edit file .env với credentials thực
# FIIN_USERNAME=your_actual_username
# FIIN_PASSWORD=your_actual_password
```

**Cách 2: Environment variables**

```bash
export FIIN_USERNAME="your_username"
export FIIN_PASSWORD="your_password"
```

**Lưu ý bảo mật:**
- File `.env` đã được thêm vào `.gitignore`
- Không commit credentials lên Git
- Sử dụng `env.example` làm template

## Hướng dẫn sử dụng

### 1. Chạy toàn bộ pipeline

```bash
python main.py
```

Pipeline sẽ thực hiện:
1. Lấy dữ liệu OHLCV từ FiinQuantX
2. Tính toán technical indicators 
3. Áp dụng triple-barrier labeling
4. Feature engineering
5. Train XGBoost model
6. Đánh giá và lưu kết quả

### 2. Chạy riêng từng phase

**Chỉ xử lý dữ liệu:**
```bash
python main.py --data-only
```

**Chỉ training (cần có dữ liệu sẵn):**
```bash
python main.py --training-only
```

**Debug mode:**
```bash
python main.py --log-level DEBUG
```

### 3. Cấu hình tùy chỉnh

Chỉnh sửa các file trong thư mục `config/`:

**data_config.yaml** - Cấu hình dữ liệu:
- `universe`: VN30, VN100 hoặc custom tickers
- `start_date`, `end_date`: Khoảng thời gian
- `technical_indicators`: Các chỉ báo kỹ thuật

**labeling_config.yaml** - Cấu hình labeling:
- `vertical_barrier.days`: Thời gian giữ tối đa
- `barriers.tp_k`, `barriers.sl_k`: Hệ số TP/SL
- `volatility.window`: Cửa sổ tính volatility

**model_config.yaml** - Cấu hình XGBoost:
- `xgboost.*`: Tham số XGBoost
- `hyperopt.enabled`: Bật/tắt hyperparameter tuning
- `cross_validation.*`: Thiết lập CV

## Pipeline chi tiết

### Flow Diagram - Luồng xử lý files

```
[Start] python main.py
    ↓
[Config Loader] → Load YAML configs
    ↓
[Data Fetcher] → FiinQuantX API
    ↓                   ↓
[Raw Data] → data/raw/trading_data.csv (OHLCV + BU/SD)
    ↓
[Triple-barrier] → Apply event-driven labeling
    ↓                   ↓  
[Labeled Data] → data/processed/labeled_data.csv (+ labels)
    ↓
[Feature Engineer] → Calculate 30+ indicators  
    ↓                   ↓
[Featured Data] → data/processed/featured_data.csv (+ features)
    ↓
[Data Cleaner] → Handle missing values, outliers
    ↓                   ↓
[Final Dataset] → data/final/final_dataset.csv
    ↓
[Data Splitter] → Time-based train/val/test
    ↓                   ↓
[Split Files] → data/final/train_data.csv
                      → data/final/val_data.csv  
                      → data/final/test_data.csv
    ↓
[XGBoost Trainer] → Train model with hyperopt
    ↓                   ↓
[Trained Model] → models/xgboost_model.pkl
                → models/feature_scaler.pkl
    ↓
[Evaluator] → Test model performance
    ↓                   ↓
[Results] → results/model_metrics.json
          → results/feature_importance.csv
    ↓
[End] → Model ready for prediction
```

### Phase 1: Data Pipeline

1. **Data Fetching**: Lấy OHLCV + volume mua/bán chủ động từ FiinQuantX
2. **Triple-barrier Labeling**: Tạo nhãn Buy/Hold/Sell
3. **Feature Engineering**: Tính toán 30+ technical indicators
4. **Data Cleaning**: Xử lý missing values, outliers
5. **Data Splitting**: Chia train/val/test theo thời gian

#### Luồng tạo feature
```mermaid
flowchart TD
    A[OHLCV Data: OHLCV + BU/SD] --> B[Feature Engineering (FiinQuantX)]

    %% Trend
    B --> C[Trend Indicators]
    C --> C1[EMA (5,10,20,50)]
    C --> C2[SMA (10,20,50)]
    C --> C3[MACD, MACD Signal, MACD Diff]
    C --> C4[ADX]

    %% Momentum
    B --> D[Momentum Indicators]
    D --> D1[RSI (14)]
    D --> D2[Stochastic, Stoch Signal]
    D --> D3[ROC (5,10,20)]
    D --> D4[Cumulative Returns (5d,10d,20d)]
    D --> D5[Price Rank (20d,50d)]

    %% Volatility
    B --> E[Volatility Indicators]
    E --> E1[Bollinger Bands (upper, lower, width, position)]
    E --> E2[ATR, ATR Ratio]
    E --> E3[Rolling Volatility]
    E --> E4[Volatility of Volatility]

    %% Volume
    B --> F[Volume Indicators]
    F --> F1[MFI]
    F --> F2[VWAP, VWAP Ratio]
    F --> F3[OBV]
    F --> F4[Volume SMA, Volume Ratio, Volume Z-score]
    F --> F5[BU/SD Ratio, Net Active Volume, Active Volume Ratio]

    %% Price-based
    B --> G[Price-based Features]
    G --> G1[Returns (1d,5d,10d,20d)]
    G --> G2[High-Low Ratio]
    G --> G3[Close-Open Ratio]
    G --> G4[Gap]

    %% Regime
    B --> H[Market Regime Features]
    H --> H1[Trend Regime (SMA trend window)]
    H --> H2[Volatility Regime (Low/Med/High vol bins)]

    %% Final output
    C & D & E & F & G & H --> Z[Final Feature Set\n~57-60 features]
```

### Phase 2: Training Pipeline

1. **Data Preparation**: Scaling, encoding
2. **Hyperparameter Optimization**: Optuna với time-series CV
3. **Model Training**: XGBoost với class balancing
4. **Evaluation**: Classification metrics + feature importance
5. **Model Persistence**: Lưu model và scaler

### File Dependencies Flow

```
main.py
├── src/utils/config_loader.py → Load configs
├── src/pipeline/data_pipeline.py
│   ├── src/data/data_fetcher.py → FiinQuantX API
│   ├── src/data/labeling.py → Triple-barrier  
│   └── src/data/feature_engineering.py → Indicators
└── src/pipeline/training_pipeline.py
    ├── src/models/xgboost_trainer.py → XGBoost
    └── src/utils/time_series_split.py → CV splits
```

## Triple-barrier Method

Phương pháp event-driven labeling:

```
Entry tại thời điểm t với giá P_t:
├── Take Profit (TP): P_t × (1 + k_tp × σ_t)
├── Stop Loss (SL): P_t × (1 - k_sl × σ_t)  
└── Vertical Barrier: Tối đa N ngày
```

**Label logic:**
- Chạm TP trước → Label = +1 (Buy)
- Chạm SL trước → Label = -1 (Sell)
- Hết thời gian → Label = sign(return) hoặc 0 (Hold)

## Features

### Technical Indicators (FiinQuantX)
- **Trend**: EMA, SMA, MACD, ADX
- **Momentum**: RSI, Stochastic
- **Volatility**: Bollinger Bands, ATR
- **Volume**: MFI, OBV, VWAP

### Price Features
- Returns (1, 5, 10, 20 ngày)
- Rolling volatility
- Volume ratios và z-scores
- Active trading (BU/SD từ FiinQuantX)

### Market Regime
- Trend regime (trên/dưới MA dài hạn)
- Volatility regime (thấp/trung bình/cao)

## Kết quả

Sau khi chạy, kết quả được lưu trong:

- `results/model_metrics.json`: Metrics tổng hợp
- `results/feature_importance.csv`: Độ quan trọng features
- `models/xgboost_model.pkl`: Trained model
- `models/feature_scaler.pkl`: Fitted scaler

### Đánh giá Model

**Classification Metrics:**
- Accuracy, Precision, Recall, F1-score
- Confusion matrix
- ROC-AUC

**Feature Importance:**
- Top features ảnh hưởng đến dự đoán
- SHAP values (planned)

## Performance Targets

- **Accuracy**: >45% (random = 33% cho 3 classes)
- **Macro F1**: >0.4
- **Feature count**: 30-50 features
- **Training time**: <30 phút trên CPU

## Troubleshooting

### Lỗi thường gặp

1. **FiinQuantX login failed**
   - Kiểm tra username/password
   - Verify account permissions

2. **Insufficient data**
   - Tăng lookback period trong config
   - Giảm technical indicator windows

3. **Memory issues**
   - Giảm số tickers trong universe
   - Tăng missing value threshold

4. **Poor model performance**
   - Adjust triple-barrier parameters
   - Enable hyperparameter optimization
   - Check feature correlation

### Debug Mode

```bash
python main.py --log-level DEBUG
```

Logs được lưu trong `logs/pipeline.log`.

## Tùy chỉnh nâng cao

### 1. Thêm Features mới

Chỉnh sửa `src/data/feature_engineering.py`:

```python
def add_custom_features(self, data):
    # Thêm features tùy chỉnh
    data['custom_indicator'] = ...
    return data
```

### 2. Thay đổi Model

Thay thế XGBoost trong `src/models/`:

```python
from sklearn.ensemble import RandomForestClassifier

class CustomTrainer:
    def create_model(self):
        return RandomForestClassifier(...)
```

### 3. Custom Labeling

Modify `src/data/labeling.py` để thay đổi logic labeling.

## Road Map

- Realtime prediction pipeline
- Backtesting với transaction costs
- Meta-labeling (2-stage model)
- SHAP interpretability
- Web dashboard

## Liên hệ & Hỗ trợ

- Documentation: Xem thêm trong thư mục `docs/`
- Issues: Tạo GitHub issue
- Configs: Tham khảo `config/` folder 
