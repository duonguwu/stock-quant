---
description: Danh sách các hàm chuyên dùng để tính hiệu suất
---

# Phân tích

1. Hàm diff

Mục đích: Dùng để **tính hiệu giữa giá trị hiện tại và giá trị trong quá khứ** của một chuỗi thời gian (time series), theo một khoảng trễ (lag) xác định.

Cấu trúc hàm: diff(x, obs=1)

Các tham số

<table><thead><tr><th width="84">Tham số</th><th>Kiểu dữ liệu</th><th>Mô tả</th></tr></thead><tbody><tr><td>x</td><td>Series</td><td>Chuỗi thời gian (giá, lợi suất...) đầu vào</td></tr><tr><td>obs</td><td>int, str hoặc Window</td><td>Độ trễ: số quan sát để tính hiệu. Có thể là:<br>- <code>int</code>: số quan sát, ví dụ: <code>1</code>, <code>5</code><br>- <code>str</code>: khoảng thời gian, ví dụ <code>'3d'</code> (3 ngày), <code>'1w'</code> (1 tuần), <code>'1m'</code> (1 tháng)<br>- <code>Window</code>: đối tượng cửa sổ từ <code>FiinQuantX.timeseries.helper.Window</code></td></tr></tbody></table>

Ý nghĩa toán học: Hàm này tính

$$
R_t = X_t - X_{t - obs}
$$

Trong đó:

* $$X_t$$: giá trị tại thời điểm hiện tại
* $$X_{t - obs}$$: giá trị tại thời điểm trước đó `obs` quan sát
* $$R_t$$: hiệu (return thô, không phải phần trăm)

Giá trị trả về:

* `Series`: chuỗi thời gian dạng `pandas.Series` với timestamp và hiệu tương ứng.

Ví dụ mẫu tính **hiệu giữa giá trị hiện tại và giá trị của 1 tuần trước** của mã HPG cho dữ liệu từ 25/06/2024 - 25/06/2025:

<pre class="language-python"><code class="lang-python">import pandas as pd
<strong>
</strong><strong>from FiinQuantX import FiinSession
</strong>from FiinQuantX.timeseries.analysis import diff
from datetime import datetime
from dateutil.relativedelta import relativedelta

username = "REPLACE_WITH_YOUR_USERNAME"
password = "REPLACE_WITH_YOUR_PASSWORD"

client = FiinSession(
    username=username,
    password=password
).login()

# Lấy dữ liệu HPG trong vòng 1 năm đổ lại
data = client.Fetch_Trading_Data(
    realtime=False,
    tickers=["HPG"],
    fields=["close"],
    adjusted=True,
    by="1d",
    from_date=(datetime.now() - relativedelta(years=1)).strftime("%Y-%m-%d")
).get_data()

# Copy data sang biến df để tránh ảnh hưởng đến dữ liệu gốc
df = data.copy()
df = df[["timestamp", "close"]]

# Biến df từ dataframe thành Series với Index là timestamp
df["timestamp"] = pd.to_datetime(df["timestamp"])
df.set_index("timestamp", inplace=True)

# Tính hiệu suất trong vòng 1 tuần
diff_series = diff(df["close"], obs="1w")

# Ghép vào dataframe ban đầu
data["one_week_change"] = df.index.map(diff_series)
print(data)
</code></pre>

Kết quả trả ra (code chạy tại ngày 25/06/2025)

```
    ticker  timestamp         close    1_week_change
0   HPG     2024-06-25 00:00  28700.0            NaN
1   HPG     2024-06-26 00:00  28900.0            NaN
2   HPG     2024-06-27 00:00  28850.0            NaN
3   HPG     2024-06-28 00:00  28300.0            NaN
4   HPG     2024-07-01 00:00  28350.0            NaN
..  ...     ...      ...          ...            ...
245 HPG     2025-06-19 00:00  26900.0          100.0
246 HPG     2025-06-20 00:00  27000.0          600.0
247 HPG     2025-06-23 00:00  26850.0          100.0
248 HPG     2025-06-24 00:00  27000.0          150.0
249 HPG     2025-06-25 00:00  27200.0           50.0
```
