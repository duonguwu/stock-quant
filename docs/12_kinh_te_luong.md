---
description: >-
  Các hàm xác định mối quan hệ giữa các tập mã chứng khoán dựa trên các chỉ số
  kinh tế lượng như annualize, beta, tương quan, max-drawdown, sharpe ratio,
  volatility, v.v.
---

# Kinh tế lượng

### 1. Hàm Annualize

Mục đích: chuyển đổi chuỗi thời gian các giá trị (ví dụ: lợi suất) thành giá trị thường niên (annualized), dựa trên tần suất quan sát trong chuỗi thời gian đó.

Cấu trúc hàm: annualize(x)

Trong đó:

* **x**: `Series` — chuỗi thời gian (TimeSeries - Series có index là dạng datetime) các giá trị như lợi suất, biến động (volatility), hoặc bất kỳ số liệu nào cần annualize.
* **Return**: `Series` — chuỗi thời gian đã được annualize.

Cơ chế:

* Tự động **ước lượng tần suất mẫu (sample frequency)** của chuỗi `x`, ví dụ: hàng ngày, hàng tuần, hàng tháng,...
* Sau đó tính **hệ số annualization** phù hợp và áp dụng công thức:

$$
Y_t = X_t . \sqrt{F}
$$

* Trong đó:
  * $$Y_t$$ là giá trị thường niên tại thời điểm 𝑡
  * $$X_t$$ là giá trị gốc tại thời điểm 𝑡
  * F là hệ số annualization (Annualization Factor)

Bảng hệ số annualization

| Kỳ quan sát          | Hệ số annualization (F) |
| -------------------- | ----------------------- |
| Daily (hàng ngày)    | 252                     |
| Weekly (hàng tuần)   | 52                      |
| Bi-Weekly            | 26                      |
| Monthly (hàng tháng) | 12                      |
| Quarterly (quý)      | 4                       |
| Annually (năm)       | 1                       |

Hàm này thường được dùng khi bạn có chuỗi thời gian là **returns hoặc volatility**, và bạn muốn:

* So sánh lợi suất thường niên giữa các cổ phiếu
* Tính độ biến động thường niên (annualized volatility)
* Chuẩn hóa dữ liệu để đưa vào mô hình tài chính

Nếu `returns(prices)` là chuỗi lợi suất hàng ngày, thì `annualized_returns` sẽ là lợi suất thường niên.

Lưu ý:

* Hàm `annualize()` sử dụng phương pháp **nhận diện tự động** tần suất dữ liệu (bằng cách đo khoảng cách giữa các `timestamp`) — bạn không cần cung cấp thông tin này.
* Trong thực tế, công thức annualization được dùng phổ biến nhất để **annualize volatility** (vì bản chất biến động cần được chuẩn hóa theo thời gian).

Ví dụ mẫu tính annualize return và annualize volatility của mã cổ phiếu HPG trong vòng 1 năm từ 24/06/2024 - 24/06/2025:

<pre class="language-python"><code class="lang-python">import pandas as pd

from FiinQuantX import FiinSession
from FiinQuantX.timeseries.econometrics import annualize
from datetime import datetime
from dateutil.relativedelta import relativedelta

<strong>username = "REPLACE_WITH_YOUR_USERNAME"
</strong>password = "REPLACE_WITH_YOUR_PASSWORD"

client = FiinSession(
    username=username,
    password=password
).login()

# Lấy dữ liệu giá đóng cửa 1 năm EOD của HPG
data = client.Fetch_Trading_Data(
    realtime=False,
    tickers="HPG",
    fields=["close"],
    adjusted=True,
    by="1d",
    from_date=(datetime.now() - relativedelta(years=1)).strftime("%Y-%m-%d")
).get_data()

# tính daily return
data["daily_return"] = data["close"] / data["close"].shift(1) - 1

# Đưa timestamp về dạng index để dùng trong hàm annyalize
data["timestamp"] = pd.to_datetime(data["timestamp"])
data.set_index("timestamp", inplace=True)

# Tính annualize returns
data["annualized_return"] = annualize(data["daily_return"])
print(data)
</code></pre>

Kết quả trả ra (code chạy tại ngày 25/06/2025)

```
 timestamp  ticker    close  daily_return  annualized_return
 2024-06-25 HPG       28700.0         NaN                NaN
 2024-06-26 HPG       28900.0    0.006969           0.110624
 2024-06-27 HPG       28850.0   -0.001730          -0.027465
 2024-06-28 HPG       28300.0   -0.019064          -0.302634
 2024-07-01 HPG       28350.0    0.001767           0.028047
 ...        ...           ...         ...                ...
 2025-06-18 HPG       27150.0    0.011173           0.177369
 2025-06-19 HPG       26900.0   -0.009208          -0.146174
 2025-06-20 HPG       27000.0    0.003717           0.059013
 2025-06-23 HPG       26850.0   -0.005556          -0.088192
 2025-06-24 HPG       27000.0    0.005587           0.088684
```

Biểu đồ minh họa (tuỳ chọn)

```python
import matplotlib.pyplot as plt

data = data.reset_index()
fig, ax1 = plt.subplots(figsize=(12, 6))

ax2 = ax1.twinx()
ax1.plot(data['timestamp'], data['close'], 'b-', label='Close Price')
ax2.plot(data['timestamp'], data['annualized_return'], 'g-', label='Annualized Return')

ax1.set_xlabel('Ngày')
ax1.set_ylabel('Giá đóng cửa (VND)', color='b')
ax2.set_ylabel('Lợi suất năm hoá (%)', color='g')
plt.title('Giá đóng cửa (VND) & Lợi suất năm hoá (%) của HPG của HPG')
plt.grid(True)
plt.show()
```

<figure><img src="https://3318188420-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2Fkme4XYjWbuM3iRJzUu9r%2Fuploads%2Fx6KUAQEbcDha5FfZOjzz%2FFigure_1.png?alt=media&#x26;token=6c2c27bc-306c-4e33-9092-588eed656b28" alt=""><figcaption></figcaption></figure>

### 2. Hàm Beta

Mục đích: Dùng để tính **rolling beta** giữa một chuỗi giá (hoặc lợi suất) và một chỉ số tham chiếu (benchmark), thường dùng để đo **mức độ nhạy cảm (rủi ro hệ thống)** của một cổ phiếu so với thị trường chung.

Cấu trúc hàm: beta(x, b, w=, prices=True)

Tham số:

<table><thead><tr><th width="82">Tham số</th><th width="174">Kiểu dữ liệu</th><th>Ý nghĩa</th></tr></thead><tbody><tr><td>x</td><td>Series</td><td>Chuỗi giá hoặc lợi suất của tài sản cần phân tích (ví dụ: cổ phiếu)</td></tr><tr><td>b</td><td>Series</td><td>Chuỗi giá hoặc lợi suất của benchmark (ví dụ: VNINDEX)</td></tr><tr><td>w</td><td>Window, int hoặc str</td><td>Kích thước cửa sổ rolling, ví dụ <code>Window(22, 10)</code> hoặc <code>'1m'</code>, <code>'1d'</code></td></tr><tr><td>prices</td><td>bool</td><td>Nếu <code>True</code>, <code>x</code> và <code>b</code> là chuỗi <strong>giá</strong>, sẽ được nội suy thành <strong>lợi suất</strong>; nếu <code>False</code>, bạn đã đưa vào lợi suất sẵn</td></tr></tbody></table>

Kiểu dữ liệu trả về: Trả về `Series` với chỉ số thời gian chứa giá trị beta được tính theo từng rolling window.

Công thức:

* Giả sử:
  * $$X_t$$ và $$b_t$$ là giá tài sản và benchmark tại thời điểm t
  * Tính lợi suất đơn giản:

$$
R_t = \frac{X_t}{X_t - 1} - 1
$$

$$
S_t = \frac{b_t}{b_t - 1} - 1
$$

* Thì:

$$
\beta_{t} = \frac{Cov(R_t, S_t)}{Var(S_t)}
$$

* Với mỗi cửa sổ `w`, beta được tính bằng **covariance giữa R và S chia cho variance của S**.

Hàm này thường được dùng để:

* Phân tích độ nhạy của cổ phiếu so với chỉ số thị trường (ví dụ: HPG so với VNINDEX)
* Phục vụ mô hình hóa rủi ro, CAPM, Alpha/Beta analysis

Lưu ý:

* Nếu bạn truyền vào chuỗi giá thì nhớ để `prices=True` để FiinQuant tự tính return.
* Nếu bạn đã tự tính return trước, hãy để `prices=False` để tránh tính toán sai.
* Đảm bảo `x` và `b` phải khớp thời gian (`index` phải trùng).

Ví dụ mẫu tính rolling beta trong vòng 22 ngày gần nhất từ 03/06/2025 - 25/06/2025 của HPG so với VNINDEX trên tập dữ liệu 1 năm từ 25/05/2024 - 25/06/2025:

```python
import pandas as pd
from FiinQuantX import FiinSession
from FiinQuantX.timeseries.econometrics import beta
from FiinQuantX.timeseries.helper import Window
from datetime import datetime
from dateutil.relativedelta import relativedelta

username = "REPLACE_WITH_YOUR_USERNAME"
password = "REPLACE_WITH_YOUR_PASSWORD"

client = FiinSession(
    username=username,
    password=password
).login()

# Lấy dữ liệu giá đóng cửa 1 năm EOD của HPG và VNINDEX
data = client.Fetch_Trading_Data(
    realtime=False,
    tickers=["HPG","VNINDEX"],
    fields=["close"],
    adjusted=True,
    by="1d",
    from_date=(datetime.now() - relativedelta(years=1)).strftime("%Y-%m-%d")
).get_data()

# Pivot theo ticker để tách riêng từng mã
data_pivot = data.pivot(index="timestamp", columns="ticker", values="close")

# Lấy Series
hpg_series = data_pivot["HPG"]
vnindex_series = data_pivot["VNINDEX"]

# Tính rolling beta 22 ngày
rolling_beta = beta(hpg_series, vnindex_series, w=Window(22), prices=True)

# Ghép 3 series vào thành 1 dataframe
df_hpg = hpg_series.rename("HPG").reset_index().rename(columns={"index": "timestamp"})
df_hsg = vnindex_series.rename("VNINDEX").reset_index().rename(columns={"index": "timestamp"})
df_corr = rolling_beta.rename("rolling_beta").reset_index().rename(columns={"index": "timestamp"})

df_merged = pd.merge(df_hpg, df_hsg, on="timestamp", how="outer")
df_merged = pd.merge(df_merged, df_corr, on="timestamp", how="outer")

df_merged = df_merged.sort_values("timestamp").reset_index(drop=True)
print(df_merged)
```

Kết quả trả ra (code chạy tại ngày 25/06/2025)

<pre><code><strong>     timestamp         HPG      VNINDEX  rolling_beta
</strong>0    2024-06-25 00:00  28700.0  1256.56           NaN
1    2024-06-26 00:00  28900.0  1261.24           NaN
2    2024-06-27 00:00  28850.0  1259.09           NaN
3    2024-06-28 00:00  28300.0  1245.32           NaN
4    2024-07-01 00:00  28350.0  1254.56           NaN
..                ...      ...      ...           ...
244  2025-06-18 00:00  27150.0  1346.83      0.189324
245  2025-06-19 00:00  26900.0  1352.04      0.220260
246  2025-06-20 00:00  27000.0  1349.35      0.211598
247  2025-06-23 00:00  26850.0  1358.18      0.136014
248  2025-06-24 00:00  27000.0  1366.77      0.142753
</code></pre>

Biểu đồ minh họa (tuỳ chọn)

```python
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# Chuẩn hóa giá trị
df_merged['timestamp'] = pd.to_datetime(df_merged['timestamp'])
df_merged['HPG_norm'] = (df_merged['HPG'] - df_merged['HPG'].min()) / (df_merged['HPG'].max() - df_merged['HPG'].min())
df_merged['VNINDEX_norm'] = (df_merged['VNINDEX'] - df_merged['VNINDEX'].min()) / (df_merged['VNINDEX'].max() - df_merged['VNINDEX'].min())

fig, ax1 = plt.subplots(figsize=(14, 6))

# Trục y bên trái: giá HPG và VNINDEX
ax1.plot(df_merged['timestamp'], df_merged['HPG_norm'], label='HPG (normalized)', color='blue')
ax1.plot(df_merged['timestamp'], df_merged['VNINDEX_norm'], label='VNINDEX (normalized)', color='green', linestyle='--')
ax1.set_ylabel('Normalized Price', color='black')
ax1.legend(loc='upper left')
ax1.grid(True)

# Format x-axis
ax1.xaxis.set_major_locator(mdates.AutoDateLocator())
ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
fig.autofmt_xdate(rotation=45)  # Rotate labels for readability

# Trục y bên phải: rolling beta
ax2 = ax1.twinx()
ax2.plot(df_merged['timestamp'], df_merged['rolling_beta'], label='Rolling Beta', color='red', alpha=0.6)
ax2.set_ylabel('Rolling Beta', color='red')
ax2.legend(loc='upper right')

plt.title('Diễn biến HPG, VNINDEX và Rolling Beta theo thời gian')
plt.tight_layout()
plt.show()
```

<figure><img src="https://3318188420-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2Fkme4XYjWbuM3iRJzUu9r%2Fuploads%2FLztYMej9RP0cu0aTj0IS%2FFigure_1.png?alt=media&#x26;token=5e1d7674-e72c-4b41-985d-92c525691b33" alt=""><figcaption></figcaption></figure>

### 3. Hàm Correlation

Mục đích: Dùng để **tính hệ số tương quan trượt (rolling correlation)** giữa hai chuỗi thời gian giá hoặc lợi suất trong tài chính.

Cấu trúc hàm: correlation(x, y, w=, type\_=SeriesType.PRICES)

Tham số:

<table><thead><tr><th width="82">Tham số</th><th width="174">Kiểu dữ liệu</th><th>Ý nghĩa</th></tr></thead><tbody><tr><td>x</td><td>Series</td><td>Chuỗi thời gian thứ nhất (giá hoặc lợi suất)</td></tr><tr><td>y</td><td>Series</td><td>Chuỗi thời gian thứ hai (giá hoặc lợi suất)</td></tr><tr><td>w</td><td>Window, int hoặc str</td><td>Kích thước cửa sổ trượt (rolling window)<br>Ví dụ: <code>Window(22, 10)</code> là dùng cửa sổ 22 phiên và bỏ qua 10 phiên đầu để "ramp-up".<br>Nếu dùng <code>str</code>, có thể là <code>'1m'</code> (1 tháng), <code>'1d'</code> (1 ngày)...</td></tr><tr><td>type_</td><td>SeriesType.PRICES (mặc định) hoặc SeriesType.RETURNS</td><td>Xác định đầu vào là giá hay lợi suất</td></tr></tbody></table>

Ý nghĩa toán học: Hàm tính hệ số tương quan Pearson giữa hai chuỗi lợi suất (hoặc giá được chuyển thành lợi suất) trong cửa sổ trượt `w`.

Công thức:

$$
\rho_t = \frac{\sum_{i=t-w+1}^t (R_i - \overline{R})(S_i - \overline{S})}{(N-1).\sigma_{R}.\sigma_{S}}
$$

Trong đó:

* $$R_i = \frac{X_i}{X_i - 1}$$: lợi suất từ chuỗi `x` nếu input là giá.
* $$S_i = \frac{Y_i}{Y_i - 1}$$: lợi suất từ chuỗi `y` nếu input là giá.
* Nếu input đã là lợi suất thì dùng trực tiếp $$R_i = X_i$$, $$S_i = Y_i$$.
* $$\overline{R}$$, $$\overline{S}$$: trung bình mẫu trong mỗi cửa sổ.
* $$\sigma_{R}$$, $$\sigma_{S}$$: độ lệch chuẩn mẫu trong mỗi cửa sổ.

Giá trị trả về:

* Một `Series` chứa hệ số tương quan qua từng thời điểm ttt, tương ứng với mỗi cửa sổ trượt.
* Có thể dùng để đánh giá mối quan hệ đồng biến/nghịch biến theo thời gian.

Ví dụ mẫu tính rolling correlation trong vòng 22 ngày gần nhất từ 03/06/2025 - 25/06/2025 của HPG và HSG trên tập dữ liệu 1 năm từ 25/05/2024 - 25/06/2025:

<pre class="language-python"><code class="lang-python">import pandas as pd
from FiinQuantX import FiinSession
from FiinQuantX.timeseries.econometrics import correlation
from FiinQuantX.timeseries.helper import Window
<strong>from datetime import datetime
</strong>from dateutil.relativedelta import relativedelta

username = "REPLACE_WITH_YOUR_USERNAME"
password = "REPLACE_WITH_YOUR_PASSWORD"

client = FiinSession(
    username=username,
    password=password
).login()

# Lấy dữ liệu giá đóng cửa 1 năm EOD của HPG và HSG
data = client.Fetch_Trading_Data(
    realtime=False,
    tickers=["HPG","HSG"],
    fields=["close"],
    adjusted=True,
    by="1d",
    from_date=(datetime.now() - relativedelta(years=1)).strftime("%Y-%m-%d")
).get_data()

# Pivot theo ticker để tách riêng từng mã
data["timestamp"] = pd.to_datetime(data["timestamp"])
pivot_data = data.pivot(index="timestamp", columns="ticker", values="close")

# Lấy Series
series_HPG = pivot_data["HPG"]
series_HSG = pivot_data["HSG"]

# Tính rolling correlation 22 ngày
corr = correlation(series_HPG, series_HSG, w=22)

# Ghép 3 series vào thành 1 dataframe
df_hpg = series_HPG.rename("HPG").reset_index().rename(columns={"index": "timestamp"})
df_hsg = series_HSG.rename("HSG").reset_index().rename(columns={"index": "timestamp"})
df_corr = corr.rename("correlation").reset_index().rename(columns={"index": "timestamp"})

df_merged = pd.merge(df_hpg, df_hsg, on="timestamp", how="outer")
df_merged = pd.merge(df_merged, df_corr, on="timestamp", how="outer")

df_merged = df_merged.sort_values("timestamp").reset_index(drop=True)
print(df_merged)
</code></pre>

Kết quả trả ra (code chạy tại ngày 25/06/2025)

```
   timestamp   HPG      HSG       correlation
0  2025-01-24  26550.0  16954.42          NaN
1  2025-02-03  26400.0  17100.16          NaN
2  2025-02-04  26850.0  17391.64          NaN
3  2025-02-05  26800.0  17391.64          NaN
4  2025-02-06  26800.0  17245.90          NaN
..        ...      ...       ...          ...
95 2025-06-19  26900.0  16750.00     0.674208
96 2025-06-20  27000.0  16600.00     0.661541
97 2025-06-23  26850.0  16350.00     0.667212
98 2025-06-24  27000.0  16750.00     0.655733
99 2025-06-25  27200.0  16750.00     0.668507
```

Biểu đồ minh họa (tuỳ chọn)

```python
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# Chuẩn hóa giá HPG và HSG (min-max normalization)
df_merged['timestamp'] = pd.to_datetime(df_merged['timestamp'])
df_merged['HPG_norm'] = (df_merged['HPG'] - df_merged['HPG'].min()) / (df_merged['HPG'].max() - df_merged['HPG'].min())
df_merged['HSG_norm'] = (df_merged['HSG'] - df_merged['HSG'].min()) / (df_merged['HSG'].max() - df_merged['HSG'].min())

fig, ax1 = plt.subplots(figsize=(14, 6))

# Plot HPG và HSG đã chuẩn hóa
ax1.plot(df_merged['timestamp'], df_merged['HPG_norm'], label='HPG (normalized)', color='blue')
ax1.plot(df_merged['timestamp'], df_merged['HSG_norm'], label='HSG (normalized)', color='green')
ax1.set_ylabel('Normalized Price', color='black')
ax1.legend(loc='upper left')
ax1.grid(True)

# Format thời gian
ax1.xaxis.set_major_locator(mdates.AutoDateLocator())
ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
fig.autofmt_xdate(rotation=45)

# Trục y phải: correlation
ax2 = ax1.twinx()
ax2.plot(df_merged['timestamp'], df_merged['correlation'], label='Rolling Correlation (HPG-HSG)', color='red', linestyle='--')
ax2.set_ylabel('Correlation', color='red')
ax2.legend(loc='upper right')

plt.title('Giá HPG & HSG (chuẩn hóa) và hệ số tương quan theo thời gian')
plt.tight_layout()
plt.show()
```

<figure><img src="https://3318188420-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2Fkme4XYjWbuM3iRJzUu9r%2Fuploads%2FxRmRCHJugbrlJHNmRgna%2FFigure_1.png?alt=media&#x26;token=140cc34d-e61d-4ecf-b8ab-4655a0b89a3e" alt=""><figcaption></figcaption></figure>

### 4. Hàm Max Drawdown

Mục đích: Hàm này **tính mức sụt giảm lớn nhất** từ đỉnh đến đáy trong một cửa sổ trượt (rolling window).

* Nếu trong 1 khoảng thời gian (window), giá cổ phiếu rơi từ đỉnh 100 xuống đáy 80, thì drawdown là `(80 - 100)/100 = -0.2`. Hàm trả về `0.2` (giá trị dương).

Cấu trúc hàm: max\_drawdown(x, w=\<gs\_quant.timeseries.helper.Window object>)

Tham số:

<table><thead><tr><th width="83">Tham số</th><th width="175">Kiểu dữ liệu</th><th>Ý nghĩa</th></tr></thead><tbody><tr><td>x</td><td>Series</td><td>Chuỗi thời gian giá (có thể là giá đóng cửa cổ phiếu, NAV quỹ đầu tư, v.v.).</td></tr><tr><td>w</td><td>Window, int hoặc str</td><td>Cửa sổ trượt dùng để tính drawdown: Window(22, 10) - 22 phiên, bỏ qua 10 phiên đầu để “làm nóng” (ramp-up), int - số lượng quan sát (ví dụ <code>20</code> là 20 phiên), str - kiểu chuỗi ngày như <code>'1m'</code>, <code>'1w'</code>, <code>'22d'</code>,... Nếu không truyền <code>w</code>, hàm sẽ tính drawdown cho toàn bộ chuỗi.</td></tr></tbody></table>

Cách hoạt động:

* Với mỗi cửa sổ `w`, hàm:
  * Tìm **đỉnh cao nhất** trong cửa sổ đó.
  * Tìm **đáy thấp nhất sau đỉnh**.
  * Tính drawdown = `(đáy - đỉnh)/đỉnh` và lấy trị tuyệt đối.

Kết quả trả về:

* Kiểu: `Series`
  * Chuỗi thời gian các giá trị drawdown lớn nhất (theo rolling window).
  * Giá trị nằm trong `[0, 1]`, biểu diễn mức sụt giảm lớn nhất trong mỗi khoảng thời gian.

Ví dụ mẫu tính rolling max drawdown với cửa sổ 22 phiên cho mã cổ phiếu HPG trên tập dữ liệu 1 năm (25/06/2024 - 25/06/2025).

```python
from FiinQuantX import FiinSession
from FiinQuantX.timeseries.econometrics import max_drawdown
from FiinQuantX.timeseries.helper import Window
from datetime import datetime
from dateutil.relativedelta import relativedelta

username = "REPLACE_WITH_YOUR_USERNAME"
password = "REPLACE_WITH_YOUR_PASSWORD"

client = FiinSession(
    username=username,
    password=password
).login()

# Lấy dữ liệu giá đóng cửa 1 năm EOD của HPG
data = client.Fetch_Trading_Data(
    realtime=False,
    tickers=["HPG"],
    fields=["close"],
    adjusted=True,
    by="1d",
    from_date=(datetime.now() - relativedelta(years=1)).strftime("%Y-%m-%d")
).get_data()

data.set_index("timestamp", inplace=True)

# Tính rolling max drawdown 22 phiên, bỏ qua 10 phiên đầu (ramp-up)
drawdown_series = max_drawdown(data['close'], w=Window(22, 10))

# Gộp kết quả vào DataFrame ban đầu
data['max_drawdown_22'] = drawdown_series
print(data)
```

Kết quả trả về

```
timestamp           ticker    close  max_drawdown_22
2024-06-25 00:00    HPG     28700.0              NaN
2024-06-26 00:00    HPG     28900.0              NaN
2024-06-27 00:00    HPG     28850.0              NaN
2024-06-28 00:00    HPG     28300.0              NaN
2024-07-01 00:00    HPG     28350.0              NaN
...                 ...         ...              ...
2025-06-19 00:00    HPG     26900.0        -0.022945
2025-06-20 00:00    HPG     27000.0        -0.022945
2025-06-23 00:00    HPG     26850.0        -0.022945
2025-06-24 00:00    HPG     27000.0        -0.022945
2025-06-25 00:00    HPG     27200.0        -0.022945
```

Biểu đồ minh họa (tuỳ chọn)

```python
import matplotlib.pyplot as plt

data[['close', 'max_drawdown_22']].plot(subplots=True, figsize=(12, 6), title=['Close Price', 'Max Drawdown (22 days)'])
plt.tight_layout()
plt.show()
```

<figure><img src="https://3318188420-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2Fkme4XYjWbuM3iRJzUu9r%2Fuploads%2FtLyjxKNLQlgHo4BWC3en%2FFigure_1.png?alt=media&#x26;token=9bfe460c-5459-4df1-b906-ef1bb891fc35" alt=""><figcaption></figcaption></figure>

### 5. Hàm Volatility

Mục đích: Dùng để **tính độ biến động (volatility) thực tế đã xảy ra** của một chuỗi giá tài sản, **theo kiểu rolling (trượt)** và được **chuẩn hóa theo năm (annualized)**.

Cấu trúc hàm: volatility(x, w=, returns\_type=Returns.SIMPLE)

Tham số:

<table><thead><tr><th width="85">Tham số</th><th width="104">Kiểu dữ liệu</th><th>Ý nghĩa</th></tr></thead><tbody><tr><td>x</td><td>Series</td><td>Chuỗi giá theo thời gian (Time series of prices).</td></tr><tr><td>w</td><td>Window / int / str</td><td>Kích thước cửa sổ trượt (rolling window):<br>– Ví dụ: <code>Window(22, 10)</code> là tính trên cửa sổ 22 phiên, bỏ qua 10 phiên đầu để "ramp-up".<br>– Có thể dùng kiểu chuỗi <code>"1m"</code> (1 tháng), <code>"10d"</code> (10 ngày)...<br>– Nếu không chỉ rõ, hàm tính trên toàn bộ chuỗi.</td></tr><tr><td>returns_type</td><td>Returns</td><td>Kiểu lợi suất cần dùng:<br>– <code>Returns.SIMPLE</code>: lợi suất đơn giản <span class="math">R_t = \frac{X_t}{X_{t - 1}} - 1</span><br>– <code>Returns.LOGARITHMIC</code>: lợi suất log tự nhiên <span class="math">R_t = \log({X_t}) - \log({X_{t - 1}})</span><br>– <code>Returns.ABSOLUTE</code>: thay đổi tuyệt đối <span class="math">R_t = X_t - X_{t - 1}</span></td></tr></tbody></table>

Ý nghĩa kết quả: Hàm trả về một chuỗi `Series` – biểu diễn **độ biến động hàng năm (annualized volatility)** của giá tài sản qua các cửa sổ thời gian đã chỉ định.

Công thức tính:

$$
Y_t = \sqrt{\frac{1}{N - 1}\sum_{i=t-w+1}^t(R_i - \overline{R})^2} * \sqrt{252} * 100
$$

Trong đó:

* $$R_i$$ là lợi suất tại thời điểm $$i$$ (dựa trên `returns_type`).
* $$\overline{R}$$ là trung bình lợi suất trong cửa sổ $$w$$.
* Nhân với $$\sqrt{252}$$ để annualize (giả định 252 ngày giao dịch trong năm).
* Nhân với 100 để ra dạng phần trăm (%).



Ví dụ mẫu tính rolling volatility với cửa sổ 22 phiên cho mã cổ phiếu HPG trên tập dữ liệu 1 năm (25/06/2024 - 25/06/2025).

```python
from FiinQuantX import FiinSession
from FiinQuantX.timeseries.econometrics import volatility
from FiinQuantX.timeseries.helper import Window
from datetime import datetime
from dateutil.relativedelta import relativedelta

username = "REPLACE_WITH_YOUR_USERNAME"
password = "REPLACE_WITH_YOUR_PASSWORD"

client = FiinSession(
    username=username,
    password=password
).login()

# Lấy dữ liệu giá đóng cửa 1 năm EOD của HPG
data = client.Fetch_Trading_Data(
    realtime=False,
    tickers=["HPG"],
    fields=["close"],
    adjusted=True,
    by="1d",
    from_date=(datetime.now() - relativedelta(years=1)).strftime("%Y-%m-%d")
).get_data()

data["timestamp"] = pd.to_datetime(data["timestamp"])
data.set_index("timestamp", inplace=True)
data["vol_series_rampup"] = volatility(data["close"], w=Window(10, 5))
print(data)
```

Kết quả trả về:

<pre><code><strong>timestamp     ticker      close  vol_series_rampup
</strong>2024-06-26    HPG     24082.370                NaN
2024-06-27    HPG     24040.705                NaN
2024-06-28    HPG     23582.390                NaN
2024-07-01    HPG     23624.055                NaN
2024-07-02    HPG     23915.710                NaN
...           ...           ...                ...
2025-06-20    HPG     22499.100          19.390249
2025-06-23    HPG     22374.105          19.581153
2025-06-24    HPG     22499.100          19.349245
2025-06-25    HPG     22665.760          19.047278
2025-06-26    HPG     22800.000          14.427419
</code></pre>

Biểu đồ minh họa (tuỳ chọn)

```python
import matplotlib.pyplot as plt

# Biểu đồ với 2 trục y
fig, ax1 = plt.subplots(figsize=(12, 5))

# Trục y bên trái: giá
ax1.plot(data.index, data['close'], label='Giá đóng cửa', color='blue')
ax1.set_ylabel('Giá cổ phiếu', color='blue')
ax1.tick_params(axis='y', labelcolor='blue')

# Trục y bên phải: volatility
ax2 = ax1.twinx()
ax2.plot(data["vol_series_rampup"].index, data["vol_series_rampup"], label='Volatility (10 phiên)', color='red')
ax2.set_ylabel('Volatility (% annualized)', color='red')
ax2.tick_params(axis='y', labelcolor='red')

# Hoàn thiện biểu đồ
plt.title('Giá HPG và Volatility tính theo rolling 10 phiên')
fig.tight_layout()
plt.grid(True)
plt.show()
```

<figure><img src="https://3318188420-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2Fkme4XYjWbuM3iRJzUu9r%2Fuploads%2FABlxkF5jFClsxOCKfKUi%2FFigure_1.png?alt=media&#x26;token=b6729b78-f877-472c-ab2d-a2b41c266984" alt=""><figcaption></figcaption></figure>
