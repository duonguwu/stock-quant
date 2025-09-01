---
description: >-
  Mô tả cách sử dụng thư viện sau khi người dùng đã đăng nhập. Chi tiết được nêu
  ra ở cuối chương này.
---

# Hàm dữ liệu Lịch sử

## 5. Lấy dữ liệu có sẵn (lịch sử)

Mô tả cách sử dụng thư viện sau khi người dùng đã đăng nhập. Các ví dụ chi tiết được nêu ra ở cuối chương này.

```python
data = client.Fetch_Trading_Data(
    realtime = False, 
    tickers = tickers,
    fields = ['open', 'high', 'low', 'close', 'volume', 'bu','sd', 'fb', 'fs', 'fn'], 
    adjusted = True,
    by = by,
    period = 100
).get_data()
```

**Tham số: (Lưu ý:** period chỉ tồn tại khi không truyền from\_date và ngược lại). Và phải lựa chọn 1 trong 2 cách truyền này.

| Tên tham số | Mô tả                                                                                                                                        | Kiểu dữ liệu  | Mặc định | Bắt buộc       |
| ----------- | -------------------------------------------------------------------------------------------------------------------------------------------- | ------------- | -------- | -------------- |
| realtime    | Có đăng ký vào dữ liệu update liên tục hay không hay chỉ gọi dữ liệu lịch sử đến thời điểm mới nhất (True là có, False là không).            | bool          |          | Có.            |
| tickers     | Danh sách mã được viết in hoa.                                                                                                               | str hoặc list |          | Có.            |
| fields      | Các trường dữ liệu cần lấy. \['open','high','low','close','volume','bu','sd','fb','fs','fn'] ứng với Open, High, Low, Close, Volume, BU, SD. | list          |          | Có.            |
| adjusted    | Giá điều chỉnh hay chưa điều chỉnh (True là đã điều chỉnh và ngược lại).                                                                     | bool          | True     | Không.         |
| by          | Đơn vị thời gian(1m, 5m, 15m, 30m, 1h, 2h, 4h, 1d).                                                                                          | str           | 1M       | Không.         |
| period      | Số nến lịch sử gần nhất cần lấy.                                                                                                             | int           |          | Không.         |
| from\_date  | Mốc thời gian lấy dữ liệu xa nhất.                                                                                                           | str           | datetime |                |
| to\_date    | Mốc thời gian lấy dữ liệu gần nhất.                                                                                                          | str           | datetime | datetime.now() |
|             |                                                                                                                                              |               |          | Không.         |

Class nhận dữ liệu là Fetch\_Trading\_Data và 2 phương thức sau:

| Tên phương thức | Mô tả                                                                                              |
| --------------- | -------------------------------------------------------------------------------------------------- |
| get\_data()     | Nhận dữ liệu lasted nếu realtime = False hoặc bắt đầu kết nối và nhận dữ liệu với realtime = True. |

```python
### pseudocode
event = client.Fetch_Trading_Data(
    realtime=False,
    tickers=tickers,
    fields=['open', 'high', 'low', 'close', 'volume', 'bu','sd'], 
    adjusted=True,
    by='1m', 
    from_date='2024-11-28 09:00'
)

data=event.get_data()
print(data)
```



Dữ liệu có các thuộc tính:

| Tên thuộc tính | Mô tả                    | Kiểu dữ liệu |
| -------------- | ------------------------ | ------------ |
| ticker         | Tên mã.                  | str          |
| timestamp      | Thời gian giao dịch.     | int          |
| open           | Giá mở cửa.              | float        |
| low            | Giá thấp nhất.           | float        |
| high           | Giá cao nhất.            | float        |
| close          | Giá đóng cửa.            | float        |
| volume         | Khối lượng giao dịch.    | int          |
| bu             | Khối lượng mua chủ động. | int          |
| sd             | Khối lượng bán chủ động. | int          |
| fb             | Giá trị mua khối ngoại.  | int          |
| fs             | Giá trị bán khối ngoại.  | int          |
| fn             | Giá trị mua/bán ròng.    | int          |

* Ví dụ

```python
import pandas as pd
from FiinQuantX import FiinSession

username = 'REPLACE_WITH_YOUR_USER_NAME'
password = 'REPLACE_WITH_YOUR_PASS_WORD'

client = FiinSession(username=username, password=password).login()

tickers = ['HPG', 'SSI', 'VN30F1M', 'UPCOMINDEX']
    
data = client.Fetch_Trading_Data(
    realtime = False,
    tickers = tickers,    
    fields = ['open', 'high', 'low', 'close', 'volume', 'bu', 'sd', 'fb', 'fs', 'fn'],
    adjusted=True,
    by = '1m', 
    from_date='2024-11-28 09:00',
).get_data()

print(data)
```
