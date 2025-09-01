# Stock Signal Classification System

**Đội thi DataStorm**

| Thành viên | SBD | Email | Trường |
|------------|-------|-------|---------|
| Nguyễn Dương | B0261 | duongnguyen4823@gmail.com | Trường Đại học Công nghệ thông tin, ĐHQG TP.HCM |
| Nguyễn Hữu Kiên | B0118 | kiennh22414@st.uel.edu.vn | Trường Đại học Kinh tế - Luật, ĐHQG TP. HCM |
| Phan Nguyễn Tường Vy | B0111 | phannguyentuongvy972004@gmail.com | Trường Đại học Tôn Đức Thắng |


---

Hệ thống phân loại tín hiệu giao dịch chứng khoán sử dụng Machine Learning với FiinQuantX.

## Khởi chạy nhanh

```bash
# Cài đặt dependencies
pip install -r requirements.txt

# Thiết lập credentials
cp env.example .env
# Edit .env file với credentials thực

# Chạy toàn bộ pipeline
python main.py

# Chạy backtesting (sau khi train model)
python backtest.py
```

## Tính năng chính

- **Event-driven Labeling**: Triple-barrier method với volatility scaling
- **Technical Indicators**: 30+ chỉ báo từ FiinQuantX (EMA, RSI, MACD, ATR, etc.)
- **XGBoost Model**: Với hyperparameter optimization và time-series CV
- **Automated Pipeline**: Từ raw data đến trained model
- **Comprehensive Backtesting**: Đánh giá hiệu suất với VN-Index benchmark

## Cấu trúc dự án

```
stock-quant/
├── config/           # Cấu hình YAML
├── src/              # Source code
├── data/             # Datasets (raw/processed/final)
├── models/           # Trained models 
├── results/          # Training results
└── main.py           # Entry point
```

## Tài liệu tham khảo

- **[SETUP.md](SETUP.md)**: Hướng dẫn setup nhanh cho người mới
- **[DOCUMENTATION.md](DOCUMENTATION.md)**: Chi tiết kỹ thuật và pipeline architecture
- **[Q&A.md](Q&A.md)**: Hỏi đáp chi tiết về hệ thống và troubleshooting
- **[BACKTEST_GUIDE.md](BACKTEST_GUIDE.md)**: Hướng dẫn backtesting và đánh giá hiệu suất
- **[planning.md](planning.md)**: Kế hoạch phát triển và technical approach
