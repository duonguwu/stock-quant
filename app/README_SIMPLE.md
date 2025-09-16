# 🚀 Simple Trading Dashboard

Ứng dụng đơn giản cho trading signals với multiple confidence levels và live chart.

## ✨ Features

- 📊 **Real-time Data**: Lấy dữ liệu từ FiinQuantX hoặc mock data
- 🎯 **Multiple Confidence Levels**: Hiển thị signals với các mức confidence khác nhau (0.3 - 0.8)
- 📈 **Live Chart**: VN-Index chart với Chart.js
- 🔧 **Feature Engineering**: 600 bars để tính chỉ báo kỹ thuật
- 🤖 **Model Inference**: Support real model hoặc mock model
- 📱 **Responsive Design**: Dashboard đẹp, dễ theo dõi

## 🚀 Quick Start

### 1. Install Dependencies
```bash
cd app
pip install -r requirements_simple.txt
```

### 2. Run Application
```bash
python run.py
```

### 3. Access Dashboard
- Dashboard: http://localhost:8000
- API Docs: http://localhost:8000/docs

## 📁 Structure

```
app/
├── main.py              # FastAPI app chính
├── data_fetcher.py      # Lấy dữ liệu từ FiinQuantX
├── feature_engine.py    # Tính toán chỉ báo kỹ thuật  
├── model_inference.py   # Model inference với multiple confidence
├── templates/
│   ├── dashboard.html   # Dashboard template
│   └── error.html       # Error template
├── run.py              # Script chạy app
└── requirements_simple.txt
```

## 🎯 Multiple Confidence Levels

Dashboard hiển thị predictions với 6 mức confidence:
- **30%**: Nhiều signals, độ tin cậy thấp
- **40%**: Cân bằng signals và confidence  
- **50%**: Mức trung bình
- **60%**: Ít signals hơn, tin cậy cao hơn
- **70%**: Rất selective
- **80%**: Cực kỳ conservative

## 📊 Data Flow

1. **Startup**: Load 600 bars historical data
2. **Feature Engineering**: Tính toán chỉ báo kỹ thuật
3. **Model Inference**: Predict với multiple confidence levels
4. **Real-time Update**: Update mỗi 15 phút
5. **Dashboard**: Hiển thị results và live chart

## 🔧 Configuration

### FiinQuantX Connection
Để sử dụng real data, set environment variables:
```bash
export TRADING_FIIN_USERNAME="your_username"
export TRADING_FIIN_PASSWORD="your_password"
```

### Model Path
App tự động tìm model trong:
- `models/xgboost_model.pkl`
- `models/model15/xgboost_model.pkl`
- `../results/xgboost_model_15m.pkl`

## 🌟 Key Advantages

1. **Self-contained**: Không phụ thuộc folder khác
2. **Simple**: Ít dependencies, dễ setup
3. **Flexible**: Hoạt động với/không có real data
4. **Visual**: Dashboard đẹp với live chart
5. **Multiple Models**: So sánh confidence levels

## 📈 API Endpoints

- `GET /`: Dashboard chính
- `GET /api/market/status`: Market status
- `GET /api/predictions`: Current predictions
- `GET /api/vnindex`: VN-Index chart data
- `GET /api/backtest`: Historical backtest data

## 🎨 Dashboard Features

- **VN-Index Card**: Giá trị và thay đổi hiện tại
- **Latest Bars**: 15m bars mới nhất cho các tickers
- **Confidence Matrix**: So sánh multiple confidence levels
- **Live Chart**: VN-Index real-time chart
- **Signal Lists**: Chi tiết signals cho từng confidence level

Ứng dụng hoàn toàn mới, đơn giản và hiệu quả! 🎉 