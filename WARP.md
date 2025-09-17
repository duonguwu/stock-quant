# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

This is a comprehensive Vietnamese stock signal classification system with two main approaches:
1. **ML-based Trading System** (`/src`): XGBoost model with triple-barrier labeling and technical indicators
2. **Rule-based TA System** (`/notebooks`): VSA/Wyckoff patterns with portfolio optimization

The system supports both **daily** and **15-minute** timeframes with specialized configurations for each.

## Key Architecture Components

### Data Pipeline Architecture
- **Data Fetcher**: Interfaces with FiinQuantX API for Vietnamese stock data
- **Feature Engineering**: 30+ technical indicators (EMA, RSI, MACD, ATR, etc.)
- **Triple-Barrier Labeling**: Event-driven labeling with volatility scaling for signal generation
- **Time Series Splitting**: Custom cross-validation for financial time series

### Model Training Architecture
- **XGBoost Trainer**: Multi-class classification (Buy/Hold/Sell) with hyperparameter optimization
- **Pipeline System**: End-to-end automated pipeline from raw data to trained models
- **Configuration-Driven**: YAML configs separate timeframes (daily vs 15m) and model parameters

### Backtesting Architecture  
- **Backtest Engine**: Portfolio simulation with transaction costs and holding periods
- **Performance Analysis**: Comprehensive metrics including Sharpe ratio, max drawdown, win rates
- **Multi-Strategy Support**: Different confidence thresholds and holding periods

### Real-time Application (`/app`)
- **FastAPI Dashboard**: WebSocket-based real-time signal streaming
- **Multi-Strategy Engine**: Parallel execution of different trading strategies
- **MongoDB Integration**: Signal persistence and historical analysis
- **Telegram Bot**: Premium signal alerts with rate limiting

## Essential Commands

### Setup and Environment
```bash
# Install dependencies
pip install -r requirements.txt

# Setup environment variables (required)
cp env.example .env
# Edit .env with your FiinQuantX credentials:
# FIIN_USERNAME=your_username  
# FIIN_PASSWORD=your_password
```

### Daily Timeframe ML Pipeline
```bash
# Complete pipeline (data + training)
python main.py

# Data pipeline only
python main.py --data-only

# Training only (requires existing data)
python main.py --training-only

# Debug mode
python main.py --log-level DEBUG

# Run backtesting (after training)
python backtest.py

# Custom backtest settings
python backtest.py --confidence 0.7 --holding-period 5
```

### 15-Minute Timeframe ML Pipeline
```bash
# Use 15-minute configurations (configs with _15m suffix)
python main.py --config-dir config  # Uses *_15m.yaml files

# Generate custom 15m backtest data
python run_custom_15m.py

# Run 15m backtesting
python backtest_15m.py --confidence 0.65 --holding-period-bars 36

# 15m with custom model
python backtest_15m.py --model models/xgboost_model_15m.pkl
```

### Rule-Based TA System (Notebooks)
```bash
# Quick start guide
cat notebooks/QUICK_START_TA.md

# Run stock screening
cd notebooks/Code && jupyter notebook Filter_stock.ipynb

# Run VSA/Wyckoff trading system
cd notebooks/Code && jupyter notebook Final_Algorithms.ipynb

# Full documentation  
cat notebooks/TA_RULE_BASED_GUIDE.md
```

### Real-Time Dashboard Application
```bash
# Start required services (Docker)
docker run -d --name mongo-container -p 27017:27017 mongo:latest
docker run -d --name redis-container -p 6379:6379 redis:7-alpine

# Development mode
cd app && uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Production mode
cd app && python main.py

# Access dashboard at http://localhost:8000
```

### Testing and Validation
```bash
# Run integration tests
python app/test_integration.py

# Test data pipeline components
python -m pytest src/tests/ -v

# Validate configurations
python -c "from src.utils.config_loader import config_loader; print('Config loaded successfully')"
```

## Configuration System

### Timeframe-Specific Configs
- **Daily**: `data_config.yaml`, `labeling_config.yaml`, `model_config.yaml`
- **15-minute**: `*_15m.yaml` variants with intraday-optimized parameters

### Key Configuration Differences
- **15m Labeling**: `vertical_barrier.days: 36` (bars, not calendar days)
- **15m Features**: Shorter periods (EMA 20/40/80 vs 50/100/200 for daily)
- **15m Model**: Higher regularization, fewer estimators due to more data

### Tickers Configuration
Default tickers are defined in configs, but can be customized:
- **Daily**: Broader universe of Vietnamese stocks
- **15m**: Limited to high-volume stocks: `['IJC', 'TDC', 'PRE', 'VLC', 'FMC', 'CTG', 'TNG', 'CSV', 'TDM', 'SJD', 'HDB', 'DRC', 'NT2', 'VPD']`

## Important File Locations

### Models and Results
- `models/`: Trained XGBoost models and scalers
- `models/model15/`: 15-minute specific models
- `results/`: Training metrics and feature importance
- `results/backtest/`: Backtesting results with auto-incrementing directories

### Data Directories
- `data/raw/`: Original data from FiinQuantX
- `data/processed/`: Labeled and featured data
- `data/final/`: Train/validation/test splits
- `data/backtest_data/`: Custom backtest datasets

### Logging
- `logs/pipeline.log`: Main pipeline logs
- `logs/backtest.log`: Backtesting logs  
- `logs/dashboard.log`: Real-time app logs

## Development Patterns

### Pipeline Pattern
All major operations follow the pipeline pattern with setup → run → cleanup phases:
```python
pipeline = DataPipeline(username, password)
pipeline.setup()
result = pipeline.run_data_pipeline(config)
```

### Configuration Loading
Always use the config loader for consistent YAML loading:
```python
from src.utils.config_loader import config_loader
config = config_loader.load_config("data_config_15m")
```

### Time Series Validation
Use proper time-based splits, never shuffle financial time series data:
```python
from src.utils.time_series_split import create_time_series_splits
cv_splits = create_time_series_splits(data, config)
```

### Model Persistence
Models are automatically versioned and saved with scalers:
```python
# Models saved to: models/xgboost_model_YYYYMMDD_HHMMSS.pkl
# Scalers saved to: models/feature_scaler_YYYYMMDD_HHMMSS.pkl
```

## Performance Considerations

### 15-Minute Timeframe
- Higher memory usage due to ~26x more data points
- Increased regularization to prevent overfitting
- Reduced hyperparameter search space for faster iteration
- Lower transaction costs (0.05% vs 0.1% for daily)

### Backtesting
- Results auto-increment: `results/backtest/backtest_N/`
- Each run preserves configuration in `config.md`
- Charts and summaries automatically generated

### Real-time Application
- WebSocket connections auto-reconnect with exponential backoff
- MongoDB indexes optimized for time-series queries
- Redis caching for real-time performance
- Telegram rate limiting (30 minutes per ticker)

## Troubleshooting

### Common Issues
1. **FiinQuantX Authentication**: Check `.env` credentials, API limits
2. **15m Data Limits**: FiinQuantX only provides ~92 days of 15m history
3. **Memory Issues**: Reduce ticker universe or timeframe window for 15m
4. **Model Not Found**: Run training pipeline first with appropriate config
5. **MongoDB Connection**: Ensure Docker container is running on port 27017

### Debug Commands
```bash
# Check environment
python -c "import os; print(os.getenv('FIIN_USERNAME'))"

# Validate data fetch
python -c "from src.data.data_fetcher import create_data_fetcher; print('Data fetcher OK')"

# Test model loading
python -c "import pickle; pickle.load(open('models/xgboost_model.pkl', 'rb')); print('Model loads OK')"
```