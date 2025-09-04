# Hướng dẫn Setup nhanh

## Bước 1: Cài đặt dependencies

```bash
pip install -r requirements.txt
```

## Bước 2: Thiết lập credentials FiinQuantX

```bash
# Copy template
cp env.example .env

# Edit file .env (dùng text editor bất kỳ)
nano .env
# hoặc
code .env
```

Thay đổi trong file `.env`:
```
FIIN_USERNAME=your_actual_username
FIIN_PASSWORD=your_actual_password
```

## Bước 3: Test connection

```bash
python -c "
from dotenv import load_dotenv
import os
load_dotenv()
print('Username:', os.getenv('FIIN_USERNAME'))
print('Password: [HIDDEN]' if os.getenv('FIIN_PASSWORD') else 'Not set')
"
```

## Bước 4: Chạy pipeline

**Test với data nhỏ:**
```bash
python main.py --data-only
```

**Chạy full pipeline:**
```bash
python main.py
```

## Troubleshooting

### Lỗi: "FiinQuantX credentials not found"
- Kiểm tra file `.env` có tồn tại không
- Kiểm tra username/password có đúng không
- Kiểm tra không có space thừa trong file .env

### Lỗi: "Module not found"
```bash
pip install -r requirements.txt
```

### Lỗi: Memory/Performance
- Giảm số tickers trong `config/data_config.yaml`
- Thay đổi `start_date` gần hơn (ít data hơn)

## Config nhanh cho người mới

**File `config/data_config.yaml` - Theo dõi 5 cổ phiếu:**
```yaml
data:
  universe: null
  custom_tickers: ["VCB", "HPG", "VIC", "VNM", "TCB"]
  start_date: "2023-01-01"
```

**File `config/model_config.yaml` - Training nhanh:**
```yaml
model:
  training:
    n_estimators: 100  # Giảm từ 1000
hyperopt:
  enabled: false       # Tắt hyperparameter tuning
  n_trials: 10        # Giảm từ 100
```

## Expected Runtime

- **Data pipeline**: 5-15 phút
- **Training (no hyperopt)**: 2-5 phút  
- **Training (with hyperopt)**: 30-60 phút
- **Total**: 10-75 phút tùy config 