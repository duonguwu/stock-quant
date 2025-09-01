# Danh sách chỉ số TA

## **1. Trend Indicators (Chỉ báo xu hướng)**

### 1.1. **EMA (Exponential Moving Average)**

> **EMA** là đường trung bình di động được tính toán với trọng số, **gán mức độ quan trọng cao hơn cho dữ liệu giá gần hơn**. EMA phản ứng nhanh hơn với những thay đổi giá cả, giúp nhà đầu tư nắm bắt xu hướng thị trường một cách kịp thời.

```python
def ema(column: pandas.core.series.Series, window: int)
```



**Tham số**

| Tên tham số | Ý nghĩa                                                 | Kiểu dữ liệu  | Giá trị mặc định |
| ----------- | ------------------------------------------------------- | ------------- | ---------------- |
| column      | Cột dữ liệu (series) chứa các giá trị để tính toán EMA. | pandas.Series |                  |
| window      | Số lượng điểm dữ liệu sử dụng trong phép tính EMA.      | int           |                  |

Ví dụ:

```python
fi = client.FiinIndicator()
df['ema_5'] = fi.ema(df['close'], window = 5)
print(df)
```

### **1.2. SMA (Simple Moving Average)**

> SMA là đường trung bình di động đơn giản, là một chỉ báo được tính bằng cách **lấy trung bình cộng của giá trong một khoảng thời gian nhất định**.

```python
def sma(column: pandas.core.series.Series, window: int)
```



**Tham số**

| Tên tham số | Mô tả                                                   | Kiểu dữ liệu  | Giá trị mặc định |
| ----------- | ------------------------------------------------------- | ------------- | ---------------- |
| column      | Cột dữ liệu (series) chứa các giá trị để tính toán SMA. | pandas.Series |                  |
| window      | Số lượng điểm dữ liệu sử dụng trong phép tính SMA.      | int           |                  |



Ví dụ:

```python
fi = client.FiinIndicator()
df['sma_5'] = fi.sma(df['close'], window = 5)
print(df)
```



### **1.3. WMA (Weighted Moving Average)**

> WMA là đường trung bình tỷ trọng tuyến tính. Chỉ báo này sẽ nhạy cảm hơn và có biến động sát hơn so với các biến động của giá thị trường. WMA sử dụng trọng số khác nhau cho mỗi giá trị trong chuỗi dữ liệu. Trong đó, các trọng số cao nhất sẽ được gán với giá trị mới nhất và giảm dần cho đến giá trị cũ nhất. Chính đặc tính này đã khiến đường WMA trở lên nhạy cảm hơn và “có dữ liệu mịn hơn” so với các đường trung bình động SMA hay EMA.

```python
def wma(column: pandas.core.series.Series, window: int)
```

**Tham số**

| Tên tham số | Mô tả                                                   | Kiểu dữ liệu  | Giá trị mặc định |
| ----------- | ------------------------------------------------------- | ------------- | ---------------- |
| column      | Cột dữ liệu (series) chứa các giá trị để tính toán WMA. | pandas.Series |                  |
| window      | Số lượng điểm dữ liệu sử dụng trong phép tính WMA.      | int           |                  |

Ví dụ:

```python
fi = client.FiinIndicator()
df['wma'] = fi.wma(df['close'], window = 14)
print(df)
```

### **1.4. MACD (Moving Average Convergence Divergence)**

> MACD là một trong những công cụ phân tích kỹ thuật được sử dụng rộng rãi bởi các nhà giao dịch. MACD giúp đo lường động lượng, hướng và sức mạnh của một xu hướng giá.
>
> Cấu tạo:
>
> * Đường MACD: Sự khác nhau giữa đường EMA ngắn hạn (thường là 12 ngày) và đường EMA dài hạn (thường là 26 ngày).
> * Đường tín hiệu (Signal): Đường EMA của đường MACD (thường là 9 ngày).
> * Biểu đồ MACD (Histogram): Sự khác nhau giữa đường MACD và đường tín hiệu.

```python
def macd(column: pandas.core.series.Series, window_slow: int = 26, window_fast: int = 12)

def macd_signal(column: pandas.core.series.Series, window_slow: int = 26, window_fast: int = 12, window_sign: int = 9)

def macd_diff(column: pandas.core.series.Series, window_slow: int = 26, window_fast: int = 12, window_sign: int = 9)
```

**Tham số**

| Tên tham số  | Mô tả                                                                      | Kiểu dữ liệu  | Giá trị mặc định |
| ------------ | -------------------------------------------------------------------------- | ------------- | ---------------- |
| column       | Cột dữ liệu (series) chứa các giá trị để tính toán MACD.                   | pandas.Series |                  |
| window\_slow | Số lượng điểm dữ liệu sử dụng cho đường EMA dài hạn trong tính toán MACD.  | int           | 26               |
| window\_fast | Số lượng điểm dữ liệu sử dụng cho đường EMA ngắn hạn trong tính toán MACD. | int           | 12               |
| window\_sign | Số lượng điểm dữ liệu sử dụng cho đường EMA trong tính toán MACD Signal.   | int           | 9                |

Ví dụ:

```python
fi = client.FiinIndicator()
df['macd'] = fi.macd(df['close'], window_fast=12, window_slow=26)
df['macd_signal'] = fi.macd_signal(df['close'], window_fast=12, window_slow=26, window_sign=9)
df['macd_diff'] = fi.macd_diff(df['close'], window_fast=12, window_slow=26, window_sign=9)
print(df)
```



### **1.5. ADX (ADXIndicator)**

> ADX là công cụ chỉ báo giao động xác định độ mạnh yếu của xu hướng. Người ta thường dùng công cụ này để xác định thị trường đang đi ngang (thị trường sideway) hay đã bắt đầu xu hướng chưa. Ban đầu, chỉ báo này được sử dụng phổ biến trong thị trường hàng hoá, sau này được mở rộng sang nhiều thị trường tài chính khác như: Chứng khoán, forex, tiền điện tử.

```python
def adx(high: pandas.core.series.Series, low: pandas.core.series.Series, close: pandas.core.series.Series, window: int = 14)

def adx_neg(high: pandas.core.series.Series, low: pandas.core.series.Series, close: pandas.core.series.Series, window: int = 14)

def adx_pos(high: pandas.core.series.Series, low: pandas.core.series.Series, close: pandas.core.series.Series, window: int = 14)
```



**Tham số**

| Tên tham số | Mô tả                                                             | Kiểu dữ liệu  | Giá trị mặc định |
| ----------- | ----------------------------------------------------------------- | ------------- | ---------------- |
| low         | Cột dữ liệu chứa các giá trị cột giá thấp nhất để tính toán ADX . | pandas.Series |                  |
| high        | Cột dữ liệu chứa các giá trị cột giá cao nhất để tính toán ADX.   | pandas.Series |                  |
| close       | Cột dữ liệu chứa các giá trị cột giá đóng cửa để tính toán ADX.   | pandas.Series |                  |
| window      | Số lượng điểm dữ liệu sử dụng trong phép tính ADX.                | int           | 14               |

Ví dụ:

```python
fi = client.FiinIndicator()
df['adx'] = fi.adx(df['high'], df['low'], df['close'], window=14)
df['adx_neg'] = fi.adx_neg(df['high'], df['low'], df['close'], window=14)
df['adx_pos'] = fi.adx_pos(df['high'], df['low'], df['close'], window=14)
print(df)
```

### **1.6. PSAR (Parabolic Stop and Reverse)**

PSAR là một chỉ báo kỹ thuật do J. Welles Wilder Jr. phát triển, được sử dụng để xác định xu hướng giá và điểm đảo chiều trong giao dịch. PSAR nằm dưới giá khi xu hướng tăng và nằm trên giá khi xu hướng giảm, giúp nhà giao dịch xác định các mức hỗ trợ hoặc kháng cự. Khi giá vượt qua PSAR, xu hướng có thể đảo chiều. Chỉ báo này dễ sử dụng, đặc biệt hiệu quả trong thị trường có xu hướng mạnh, nhưng có thể tạo tín hiệu nhiễu trong thị trường đi ngang.

```python
def psar(self, high: pd.Series, low: pd.Series, close: pd.Series, step: float = 0.02, max_step: float = 0.2)
```

**Tham số:**

| Tên tham số | Mô tả                                                                                                                                                                                                                                                                         | Kiểu dữ liệu  | Mặc định |
| ----------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------- | -------- |
| high        | Cột dữ liệu chứa các giá trị cột giá cao nhất.                                                                                                                                                                                                                                | pandas.Series |          |
| low         | Cột dữ liệu chứa các giá trị cột giá thấp nhất.                                                                                                                                                                                                                               | pandas.Series |          |
| close       | Cột dữ liệu chứa các giá trị cột giá đóng cửa.                                                                                                                                                                                                                                | pandas.Series |          |
| step        | Hệ số gia tốc (Acceleration Factor - AF) khởi tạo trong quá trình tính toán.Step càng nhỏ -> PSAR sẽ phản ứng chậm hơn với thay đổi giá, phù hợp cho các thị trường ít biến động.Step lớn hơn -> PSAR nhạy hơn, dễ bắt kịp các thay đổi nhưng cũng có thể tạo tín hiệu nhiễu. | float         | 0.02     |
| max\_step   | Giá trị tối đa mà hệ số gia tốc (AF) có thể đạt được.                                                                                                                                                                                                                         | float         | 0.2      |

Ví dụ:

<pre class="language-python"><code class="lang-python">fi = client.FiinIndicator()
<strong>df['psar'] = fi.psar(df['high'], df['low'], df['close'], step=0.02, max_step=0.2)
</strong><strong>print(df)
</strong></code></pre>

### **1.7. Ichimoku (Ichimoku Kinko Hyo)**

Ichimoku là một chỉ báo kỹ thuật do Goichi Hosoda phát triển, giúp đánh giá xu hướng, mức hỗ trợ, kháng cự và cung cấp tín hiệu mua bán trong một biểu đồ duy nhất. Chỉ báo gồm năm thành phần chính: Tenkan-sen, Kijun-sen, Senkou Span A, Senkou Span B, và Chikou Span, tạo thành "đám mây" (Kumo) thể hiện động lực thị trường. Ichimoku đặc biệt hiệu quả trong các thị trường có xu hướng rõ ràng, giúp nhà giao dịch đưa ra quyết định dựa trên sự cân bằng giá.

```python
def ichimoku_a(self, high: pd.Series, low: pd.Series, close: pd.Series, window1: int = 9, window2: int = 26, window3: int = 52) -> pd.Series: ...
def ichimoku_b(self, high: pd.Series, low: pd.Series, close: pd.Series, window1: int = 9, window2: int = 26, window3: int = 52) -> pd.Series: ...
def ichimoku_base_line(self, high: pd.Series, low: pd.Series, close: pd.Series, window1: int = 9, window2: int = 26, window3: int = 52) -> pd.Series: ...
def ichimoku_conversion_line(self, high: pd.Series, low: pd.Series, close: pd.Series, window1: int = 9, window2: int = 26, window3: int = 52) -> pd.Series: ...
def ichimoku_lagging_line(self, high: pd.Series, low: pd.Series, close: pd.Series,
    window1: int = 9, window2: int = 26, window3: int = 52) -> pd.Series: ...
```

**Tham số**

| Tham số | Mô tả                                                                                                                  | Kiểu dữ liệu  | Mặc định |
| ------- | ---------------------------------------------------------------------------------------------------------------------- | ------------- | -------- |
| high    | Cột dữ liệu chứa các giá trị cột giá cao nhất.                                                                         | pandas.Series |          |
| low     | Cột dữ liệu chứa các giá trị cột giá thấp nhất.                                                                        | pandas.Series |          |
| close   | Cột chứa dữ liệu giá đóng cửa.                                                                                         | pandas.Series |          |
| window1 | Số lượng điểm dữ liệu sử dụng cho đường Conversion Line (Tenkan-sen).                                                  | int           | 9        |
| window2 | Số lượng điểm dữ liệu sử dụng cho đường Base Line (Kijun-sen) và để dịch các đường như Chikou Span và Senkou Span A/B. | int           | 26       |
| window3 | Số lượng điểm dữ liệu sử dụng cho đường Senkou Span B.                                                                 | int           | 52       |

Ví dụ:

```python
fi = client.FiinIndicator()
df['senkou_span_a'] = fi.ichimoku_a(df['high'], df['low'], df['close'], window1 = 9, window2 = 26, window3 = 52)
df['senkou_span_b'] = fi.ichimoku_b(df['high'], df['low'], df['close'], window1 = 9, window2 = 26, window3 = 52)
df['kijun_sen'] = fi.ichimoku_base_line(df['high'], df['low'], df['close'], window1 = 9, window2 = 26, window3 = 52) 
df['tenkan_sen'] = fi.ichimoku_conversion_line(df['high'], df['low'], df['close'], window1 = 9, window2 = 26, window3 = 52)
print(df)
```

### **1.8. CCI (Commodity Channel Index)**

CCI là một chỉ báo kỹ thuật được Donald Lambert phát triển dùng để đo lường độ lệch của giá so với giá trị trung bình trong một khoảng thời gian, giúp xác định điều kiện quá mua hoặc quá bán. Khi CCI vượt ngưỡng 100, giá có thể đang quá mua, và khi dưới -100, giá có thể đang quá bán. Chỉ báo này phù hợp để phát hiện xu hướng mới hoặc cảnh báo sự đảo chiều tiềm năng.

```python
def cci(self, high: pd.Series, low: pd.Series, close: pd.Series, window: int = 20, constant: float = 0.015) -> pd.Series: ...
```

**Tham số:**

| Tham số  | Mô tả                                                                         | Kiểu dữ liệu  | Mặc định |
| -------- | ----------------------------------------------------------------------------- | ------------- | -------- |
| high     | Cột dữ liệu chứa các giá trị cột giá cao nhất.                                | pandas.Series |          |
| low      | Cột dữ liệu chứa các giá trị cột giá thấp nhất.                               | pandas.Series |          |
| close    | Cột dữ liệu chứa các giá trị cột giá đóng cửa.                                | pandas.Series |          |
| window   | Số lượng điểm dữ liệu sử dụng cho đường SMA và Mean Deviation.                | int           | 20       |
| constant | Hằng số chuẩn hóa để đảm bảo giá trị CCI dao động trong một phạm vi xác định. | float         | 0.015    |

Ví dụ:

```python
fi = client.FiinIndicator()
df['cci'] = fi.cci(df['high'], df['low'], df['close'], window = 20, constant = 0.015)
print(df)
```

### **1.9. Aroon**

Aroon là một chỉ báo kỹ thuật do Tushar Chande phát triển, dùng để đo lường sức mạnh của xu hướng và xác định sự bắt đầu hoặc kết thúc của xu hướng. Chỉ báo gồm hai thành phần chính: Aroon-Up (theo dõi đỉnh cao nhất) và Aroon-Down (theo dõi đáy thấp nhất) trong một khoảng thời gian nhất định. Giá trị dao động từ 0 đến 100, với mức cao cho thấy xu hướng mạnh và mức thấp cho thấy sự yếu dần của xu hướng. Aroon đặc biệt hữu ích trong việc phát hiện các giai đoạn tích lũy hoặc đảo chiều trên thị trường.

<pre class="language-python"><code class="lang-python"><strong>def aroon(self, high: pd.Series, low: pd.Series, window: int = 25) -> pd.Series: ...
</strong>def aroon_up(self, high: pd.Series, low: pd.Series, window: int = 25) -> pd.Series: ... 
def aroon_down(self, high: pd.Series, low: pd.Series, window: int = 25) -> pd.Series: ...
</code></pre>

**Tham số:**

| Tham số | Mô tả                                                          | Kiểu dữ liệu  | Giá trị mặc định |
| ------- | -------------------------------------------------------------- | ------------- | ---------------- |
| high    | Cột dữ liệu chứa các giá trị cột giá cao nhất.                 | pandas.Series |                  |
| low     | Cột dữ liệu chứa các giá trị cột giá thấp nhất.                | pandas.Series |                  |
| window  | Số lượng điểm dữ liệu sử dụng cho đường SMA và Mean Deviation. | int           | 25               |

Ví dụ:

```python
fi = client.FiinIndicator()
df['aroon'] = fi.aroon(df['high'], df['low'], window: int = 25)
df['aroon_up'] = fi.aroon_up(df['high'], df['low'], window: int = 25)
df['aroon_down'] = fi.aroon_down(df['high'], df['low'], window: int = 25)
print(df)
```

### **1.10. Zig Zag**

Zig Zag là một chỉ báo phổ biến giúp lọc bỏ những biến động giá nhỏ để loại bỏ nhiễu dữ liệu và nhấn mạnh xu hướng. Các nhà giao dịch thường sử dụng Zig Zag để xác nhận xu hướng, xác định ngưỡng hỗ trợ và kháng cự tiềm năng và phát hiện mô hình. Chỉ báo này được hình thành bằng cách xác định các điểm cao và thấp cục bộ quan trọng theo thứ tự xen kẽ và kết nối chúng bằng các đường thẳng, bỏ qua tất cả các điểm dữ liệu khác khỏi đầu ra của chúng. Có một số cách để tính toán các điểm dữ liệu của Zig Zag và các điều kiện theo đó hướng của nó thay đổi. Tập lệnh này sử dụng các điểm xoay làm điểm dữ liệu, là các giá trị cao nhất hoặc thấp nhất trong một số thanh xác định trước và sau chúng. Hướng chỉ đảo ngược khi một điểm xoay mới hình thành lệch khỏi điểm Zig Zag cuối cùng theo hướng ngược lại với một lượng lớn hơn hoặc bằng một tỷ lệ phần trăm được chỉ định.

<pre class="language-python"><code class="lang-python"><strong>def zigzag(self, high: pd.Series, low: pd.Series, dev_threshold: float = 5.0, depth: int = 10) -> pd.Series: ...
</strong></code></pre>

**Tham số:**

| Tham số        | Mô tả                                                                      | Kiểu dữ liệu  | Giá trị mặc định |
| -------------- | -------------------------------------------------------------------------- | ------------- | ---------------- |
| high           | Cột dữ liệu chứa các giá trị cột giá cao nhất.                             | pandas.Series |                  |
| low            | Cột dữ liệu chứa các giá trị cột giá thấp nhất.                            | pandas.Series |                  |
| dev\_threshold | Độ lệch phần trăm tối thiểu từ một điểm trước khi đường ​ZigZag đổi hướng. | float         | 5.0              |
| depth          | Số thanh cần thiết để phát hiện điểm pivot.                                | int           | 10               |

Ví dụ:

```python
fi = client.FiinIndicator()
df['zigzag'] = fi.zigzag(df['high'], df['low'], dev_threshold = 5.0, depth = 10)
print(df)
```

## 2. Momentum Indicators (Chỉ báo động lượng)

### **2.1. RSI (Relative Strength Index)**

> RSI là một chỉ báo đo lường tốc độ và biên độ của biến động giá gần đây để đánh giá liệu một tài sản đang bị mua quá nhiều (overbought) hay bán quá nhiều (oversold).
>
> RSI được tính toán dựa trên giá đóng cửa trong một khoảng thời gian nhất định (thường là 14 ngày).
>
> Chỉ số này dao động trong khoảng từ 0 đến 100.
>
> * RSI trên 70: Là vùng quá mua, tài sản có thể đã tăng giá quá nhanh và có khả năng điều chỉnh giảm.
> * RSI dưới 30: Là vùng quá bán, tài sản có thể đã giảm giá quá sâu và có khả năng phục hồi.

```python
def rsi(column: pandas.core.series.Series, window: int = 14)
```



**Tham số**

| Tên tham số | Mô tả                                                   | Kiểu dữ liệu  | Giá trị mặc định |
| ----------- | ------------------------------------------------------- | ------------- | ---------------- |
| column      | Cột dữ liệu (series) chứa các giá trị để tính toán RSI. | pandas.Series |                  |
| window      | Số lượng điểm dữ liệu sử dụng trong phép tính RSI.      | int           | 14               |

**Ví dụ:**

```python
fi = client.FiinIndicator()
df['rsi'] = fi.rsi(df['close'], window=14)
print(df)
```



### **2.2. Stochastic**

> Stochastic Oscillator (Chỉ báo Dao động ngẫu nhiên) là một công cụ phân tích kỹ thuật hiệu quả, giúp đánh giá động lượng và khả năng đảo chiều của giá, xác định vùng mua/bán tiềm năng trên thị trường.
>
> Cấu tạo:
>
> * %K: Đường này so sánh giá đóng cửa hiện tại của chứng khoán với phạm vi giá cao nhất và thấp nhất trong một khoảng thời gian nhất định. Trên 80: Cho thấy chứng khoán có thể quá mua, khả năng điều chỉnh giá xuống. Dưới 20: Cho thấy chứng khoán có thể quá bán, khả năng phục hồi giá.
> * %D: Đường SMA của %K, giúp làm mượt mà các biến động ngắn hạn.

> Cả %K và %D đều dao động trong khoảng từ 0 đến 100.

```python
def stoch(high: pandas.core.series.Series, low: pandas.core.series.Series, close: pandas.core.series.Series, window: int = 14, smooth_window: int = 3)
```

```python

def stoch_signal(high: pandas.core.series.Series, low: pandas.core.series.Series, close: pandas.core.series.Series, window: int = 14, smooth_window: int = 3)
```



**Tham số**

| Tên tham số    | Mô tả                                                                                             | Kiểu dữ liệu  | Giá trị mặc định |
| -------------- | ------------------------------------------------------------------------------------------------- | ------------- | ---------------- |
| low            | Cột dữ liệu chứa các giá trị cột giá thấp nhất để tính toán Stochastic.                           | pandas.Series |                  |
| high           | Cột dữ liệu chứa các giá trị cột giá cao nhất để tính toán Stochastic.                            | pandas.Series |                  |
| close          | Cột dữ liệu chứa các giá trị cột giá đóng cửa để tính toán Stochastic.                            | pandas.Series |                  |
| window         | Số lượng điểm dữ liệu sử dụng trong phép tính Stochastic.                                         | int           | 14               |
| smooth\_window | Số lượng điểm dữ liệu sử dụng trong phép tính Stochastic Signal bằng cách lấy SMA của Stochastic. | int           | 3                |

Ví dụ:

```python
fi = client.FiinIndicator()
df['stoch'] = fi.stoch(df['high'], df['low'], df['close'], window=14)
df['stoch_signal'] = fi.stoch_signal(df['high'], df['low'], df['close'], window=14, smooth_window=3)
print(df)
```

## 3. Volatility Indicators (Chỉ báo biến động)

### **3.1. Bollinger Bands**

> Bollinger Bands (Dải Bollinger) là một công cụ phân tích kỹ thuật được phát triển bởi John Bollinger vào những năm 1980. Bollinger Bands giúp đo lường sự biến động (volatility) của giá và xác định mức giá cao/thấp tiềm năng trong một xu hướng.
>
> Cấu tạo:
>
> * Dải trung tâm (Centerline): Đường trung bình động (thường là đường SMA 20 ngày) của giá.
> * Dải trên (Upper Band): Số lần chênh lệch chuẩn nhất định (thường là 2) tính trên đường trung tâm, được cộng thêm vào giá trị của đường trung tâm.
> * Dải dưới (Lower Band): Số lần chênh lệch chuẩn nhất định (thường là 2) tính trên đường trung tâm, được trừ đi khỏi giá trị của đường trung tâm.

```python
def bollinger_hband(column: pandas.core.series.Series, window: int = 20, window_dev: int = 2)

def bollinger_lband(column: pandas.core.series.Series, window: int = 20, window_dev: int = 2)
```

**Tham số**

| Tên tham số | Mô tả                                                                                | Kiểu dữ liệu  | Giá trị mặc định |
| ----------- | ------------------------------------------------------------------------------------ | ------------- | ---------------- |
| column      | Cột dữ liệu chứa các giá trị để tính toán Bollinger Bands.                           | pandas.Series |                  |
| window      | Số lượng điểm dữ liệu sử dụng trong phép tính Bollinger Bands.                       | int           | 20               |
| window\_dev | Số lượng độ lệch chuẩn sử dụng để tính toán khoảng cách các dải của Bollinger Bands. | int           | 2                |

Ví dụ

<pre class="language-python"><code class="lang-python">fi = client.FiinIndicator()
df['bollinger_hband'] = fi.bollinger_hband(df['close'], window=20, window_dev=2)
<strong>df['bollinger_lband'] = fi.bollinger_lband(df['close'], window=20, window_dev=2)
</strong>print(df)
</code></pre>

### **3.2. Supertrend**

> Supertrend (siêu xu hướng) là một công cụ phân tích kỹ thuật được phát triển bởi nhà đầu tư Olivier Seban vào năm 2010. Supertrend sử dụng kết hợp các yếu tố như giá cả ATR (Average True Range - Biên độ dao động trung bình thực) và xu hướng hiện tại để xác định xu hướng chính của thị trường và các điểm đảo chiều tiềm năng.

```python
def supertrend(high: pandas.core.series.Series, low: pandas.core.series.Series, close: pandas.core.series.Series, window: int = 14, multiplier: float = 3.0)


def supertrend_hband(high: pandas.core.series.Series, low: pandas.core.series.Series, close: pandas.core.series.Series, window: int = 14, multiplier: float = 3.0)


def supertrend_lband(high: pandas.core.series.Series, low: pandas.core.series.Series, close: pandas.core.series.Series, window: int = 14, multiplier: float = 3.0)
```

**Tham số:**

| Tên tham số | Mô tả                                                                        | Kiểu dữ liệu  | Giá trị mặc định |
| ----------- | ---------------------------------------------------------------------------- | ------------- | ---------------- |
| high        | Cột dữ liệu chứa các giá trị cột giá cao nhất để tính toán Supertrend.       | pandas.Series |                  |
| low         | Cột dữ liệu chứa các giá trị cột giá thấp nhất để tính toán Supertrend.      | pandas.Series |                  |
| close       | Cột dữ liệu chứa các giá trị cột giá đóng cửa để tính toán Supertrend.       | pandas.Series |                  |
| window      | Số lượng điểm dữ liệu sử dụng trong phép tính Supertrend.                    | int           | 14               |
| multiplier  | Hệ số nhân dùng để điều chỉnh độ rộng của chỉ báo Supertrend so với mức giá. | float         | 3.0              |

Ví dụ:

```python
fi = client.FiinIndicator()
df['supertrend'] = fi.supertrend(df['high'], df['low'], df['close'], window=14)
df['supertrend_hband'] = fi.supertrend_hband(df['high'], df['low'], df['close'], window=14)
df['supertrend_lband'] = fi.supertrend_lband(df['high'], df['low'], df['close'], window=14)
print(df)
```

### **3.3. ATR (AverageTrueRange)**

> ATR là khoảng dao động trung bình thực tế. Đây là chỉ báo để đo lường những biến động của giá trong một khoảng thời gian nhất định.
>
> Chỉ báo được giới thiệu trong cuốn sách “Tư tưởng mới trong Hệ thống kỹ thuật Giao dịch” của J. Welles Wilder Jr vào năm 1978. Thông qua chỉ báo, nhà đầu tư có thể dự đoán mức giá dao động trong tương lai. Nhờ đó, nhà đầu tư có cơ sở để đặt điểm cắt lỗ và chốt lời hợp lý.
>
>

```python
def atr(high: pandas.core.series.Series, low: pandas.core.series.Series, close: pandas.core.series.Series, window: int = 14)
```



**Tham số:**

| Tên tham số | Mô tả                                                            | Kiểu dữ liệu  | Giá trị mặc định |
| ----------- | ---------------------------------------------------------------- | ------------- | ---------------- |
| high        | Cột dữ liệu chứa các giá trị cột giá cao nhất để tính toán ATR.  | pandas.Series |                  |
| low         | Cột dữ liệu chứa các giá trị cột giá thấp nhất để tính toán ATR. | pandas.Series |                  |
| close       | Cột dữ liệu chứa các giá trị cột giá đóng cửa để tính toán ATR.  | pandas.Series |                  |
| window      | Số lượng điểm dữ liệu sử dụng trong phép tính ATR.               | int           | 14               |

Ví dụ:

```python
fi = client.FiinIndicator()
df['atr'] = fi.atr(df['high'], df['low'], df['close'], window=14)
print(df)
```

## 4. Volume Indicators (Chỉ báo khối lượng)

### **4.1. MFI (Money Flow Index)**

> MFI là chỉ số phản ánh sức mạnh dòng tiền của một cổ phiếu trong một khoản thời gian nhất định, được phân tích dựa vào khối lượng giao dịch. Khoảng thời gian được xem xét theo ngày, tuần tháng, và thường tính toán theo giá trị 14 giai đoạn.
>
>

```python
def mfi(high: pandas.core.series.Series, low: pandas.core.series.Series, close: pandas.core.series.Series, volume: pandas.core.series.Series, window: int = 14)
```

**Tham số**

| Tên tham số | Mô tả                                                                   | Kiểu dữ liệu  | Giá trị mặc định |
| ----------- | ----------------------------------------------------------------------- | ------------- | ---------------- |
| high        | Cột dữ liệu chứa các giá trị cột giá cao nhất để tính toán MFI.         | pandas.Series |                  |
| low         | Cột dữ liệu chứa các giá trị cột giá thấp nhất để tính toán MFI.        | pandas.Series |                  |
| close       | Cột dữ liệu chứa các giá trị cột giá đóng cửa để tính toán MFI.         | pandas.Series |                  |
| volume      | Cột dữ liệu chứa các giá trị cột khối lượng giao dịch để tính toán MFI. | pandas.Series |                  |
| window      | Số lượng điểm dữ liệu sử dụng trong phép tính MFI.                      | int           | 14               |

Ví dụ:

```python
fi = client.FiinIndicator()
df['mfi'] = fi.mfi(df['high'], df['low'], df['close'], df['volume'], window=14)
print(df)
```

### **4.2. OBV (On Balance Volume)**

> OBV là chỉ báo khối lượng có chức năng đo lường khối lượng giao dịch tích lũy qua các phiên, từ đó cho thấy cổ phiếu đang có xu hướng được mua hay bán. Nếu phiên hôm nay là một phiên tăng giá thì khối lượng sẽ được cộng thêm vào chỉ số OBV. Ngược lại, khối lượng sẽ được trừ ra khi hôm nay là một phiên giao dịch giảm điểm.
>
>

```python
def obv(column: pandas.core.series.Series, volume: pandas.core.series.Series)
```

**Tham số**

| Tên tham số | Mô tả                                                                   | Kiểu dữ liệu  | Giá trị mặc định |
| ----------- | ----------------------------------------------------------------------- | ------------- | ---------------- |
| column      | Cột dữ liệu (series) chứa các giá trị về giá để tính toán OBV.          | pandas.Series |                  |
| volume      | Cột dữ liệu chứa các giá trị cột khối lượng giao dịch để tính toán OBV. | pandas.Series |                  |

Ví dụ:

```python
fi = client.FiinIndicator()
df['obv'] = fi.obv(df['close'], df['volume'])
print(df)
```

### **4.3. VWAP (Volume Weighted Adjusted Price)**

> **VWAP** là giá trung bình theo trọng số khối lượng, giá trung bình của một cổ phiếu tính theo tổng khối lượng giao dịch. VWAP được sử dụng để tính giá trung bình của một cổ phiếu trong một khoảng thời gian.
>
> Giá bình quân gia quyền theo khối lượng giúp so sánh giá hiện tại của cổ phiếu với giá chuẩn, giúp nhà đầu tư dễ dàng quyết định thời điểm tham gia và thoát khỏi thị trường. Ngoài ra, VWAP có thể hỗ trợ các nhà đầu tư xác định cách đầu tư của họ đối với một cổ phiếu và thực hiện chiến lược giao dịch phù hợp vào đúng thời điểm.
>
>

```python
def vwap(high: pandas.core.series.Series, low: pandas.core.series.Series, close: pandas.core.series.Series, volume: pandas.core.series.Series, window: int = 14)
```

**Tham số:**\


| Tên tham số | Mô tả                                                                    | Kiểu dữ liệu  | Giá trị mặc định |
| ----------- | ------------------------------------------------------------------------ | ------------- | ---------------- |
| high        | Cột dữ liệu chứa các giá trị cột giá cao nhất để tính toán VWAP.         | pandas.Series |                  |
| low         | Cột dữ liệu chứa các giá trị cột giá thấp nhất để tính toán VWAP.        | pandas.Series |                  |
| close       | Cột dữ liệu chứa các giá trị cột giá đóng cửa để tính toán VWAP.         | pandas.Series |                  |
| volume      | Cột dữ liệu chứa các giá trị cột khối lượng giao dịch để tính toán VWAP. | pandas.Series |                  |
| window      | Số lượng điểm dữ liệu sử dụng trong phép tính VWAP.                      | int           | 14               |

Ví dụ:

```python
fi = client.FiinIndicator()
df['vwap'] = fi.vwap(df['high'], df['low'], df['close'], df['volume'], window=14)
print(df)
```

## 5. Smart Money Concepts

### **5.1. Fair Value Gap (FVG)**

Là một vùng giá chưa được lấp đầy trên biểu đồ, xuất hiện khi có sự mất cân bằng giữa cung và cầu. · Nếu cây nến hiện tại là nến tăng (bullish), fvg xuất hiện khi đỉnh của nến trước thấp hơn đáy của nến sau. Nếu cây nến hiện tại là nến giảm (bearish), fvg xuất hiện khi đáy của nến trước cao hơn đỉnh của nến sau.

```python
def fvg(self, open: pd.Series, high: pd.Series, low: pd.Series, close: pd.Series, join_consecutive: bool = True) -> pd.Series: ...
    
def fvg_top(self, open: pd.Series, high: pd.Series, low: pd.Series, close: pd.Series, join_consecutive: bool = True) -> pd.Series: ...
    
def fvg_bottom(self, open: pd.Series, high: pd.Series, low: pd.Series, close: pd.Series, join_consecutive: bool = True) -> pd.Series: ...
    
def fvg_mitigatedIndex(self, open: pd.Series, high: pd.Series, low: pd.Series, close: pd.Series, join_consecutive: bool = True) -> pd.Series: ...
```

**Tham số**

| Tên tham số       | Mô tả                                                                                                                         | Kiểu dữ liệu  | Giá trị mặc định |
| ----------------- | ----------------------------------------------------------------------------------------------------------------------------- | ------------- | ---------------- |
| open              | Cột chứa giá mở cửa.                                                                                                          | pandas.Series |                  |
| high              | Cột chứa giá cao nhất.                                                                                                        | pandas.Series |                  |
| low               | Cột chứa giá thấp nhất.                                                                                                       | pandas.Series |                  |
| close             | Cột chứa giá đóng cửa.                                                                                                        | pandas.Series |                  |
| join\_consecutive | Nếu có nhiều khoảng (FVG) liên tiếp, chúng sẽ được gộp lại thành một, sử dụng mức cao nhất làm đỉnh và mức thấp nhất làm đáy. | bool          | True             |

Ví dụ:

```python
fi = client.FiinIndicator()
df['fvg'] = fi.fvg(df['open'],df['high'], df['low'], df['close'],join_consecutive=True)
print(df)
```



### **5.2. Swing Highs and Lows**

Đỉnh xoay (Swing High) xảy ra khi giá cao nhất của cây nến hiện tại là mức cao nhất trong một khoảng thời gian xác định trước và sau nó.

Đáy xoay (Swing Low) xảy ra khi giá thấp nhất của cây nến hiện tại là mức thấp nhất trong cùng khoảng thời gian đó.

```python
def swing_HL(self, open: pd.Series, high: pd.Series, low: pd.Series, close: pd.Series, swing_length: int = 50) -> pd.Series: ...
    
def swing_level(self, open: pd.Series, high: pd.Series, low: pd.Series, close: pd.Series, swing_length: int = 50)) -> pd.Series: ...
```

**Tham số**

| Tên tham số   | Mô tả                                                                | Kiểu dữ liệu  |    |
| ------------- | -------------------------------------------------------------------- | ------------- | -- |
| open          | Cột chứa giá mở cửa.                                                 | pandas.Series |    |
| high          | Cột chứa giá cao nhất.                                               | pandas.Series |    |
| low           | Cột chứa giá thấp nhất.                                              | pandas.Series |    |
| close         | Cột chứa giá đóng cửa.                                               | pandas.Series |    |
| swing\_length | Số lượng nến cần xét về trước và sau để xác định đỉnh hoặc đáy xoay. | int           | 50 |

Ví dụ:

```python
fi = client.FiinIndicator()
df['swing_HL'] = fi.swing_HL(df['open'],df['high'], df['low'], df['close'], swing_length = 50)
print(df)
```

### **5.3. Break of Structure (BOS) & Change of Character (CHoCH)**

BOS (Break of Structure): Khi giá phá vỡ cấu trúc xu hướng trước đó (tăng hoặc giảm), thể hiện sự thay đổi trong động lực thị trường.

ChoCH (Change of Character): Chỉ báo quan trọng thể hiện sự đảo chiều của xu hướng. CHoCH xảy ra khi xu hướng giảm chuyển sang tăng hoặc ngược lại.

```python
def break_of_structure(self, open: pd.Series, high: pd.Series, low: pd.Series, close: pd.Series, close_break: bool = True, swing_length: int = 50) -> pd.Series: ...
    
def chage_of_charactor(self, open: pd.Series, high: pd.Series, low: pd.Series, close: pd.Series, close_break: bool = True, swing_length: int = 50) -> pd.Series: ...
    
def bos_choch_level(self, open: pd.Series, high: pd.Series, low: pd.Series, close: pd.Series, close_break: bool = True, swing_length: int = 50) -> pd.Series: ...
    
def broken_index(self, open: pd.Series, high: pd.Series, low: pd.Series, close: pd.Series, close_break: bool = True, swing_length: int = 50) -> pd.Series: ...
```

**Tham số**

| Tên tham số   | Mô tả                                                                                               | Kiểu dữ liệu  | Mặc định |
| ------------- | --------------------------------------------------------------------------------------------------- | ------------- | -------- |
| open          | Cột chứa giá mở cửa.                                                                                | pandas.Series |          |
| high          | Cột chứa giá cao nhất.                                                                              | pandas.Series |          |
| low           | Cột chứa giá thấp nhất.                                                                             | pandas.Series |          |
| close         | Cột chứa giá đóng cửa.                                                                              | pandas.Series |          |
| close\_break  | Nếu True, xác nhận dựa trên giá đóng cửa của nến.Nếu False, xác nhận dựa trên mức cao/thấp của nến. | bool          | True     |
| swing\_length | Số lượng nến cần xét về trước và sau để xác định đỉnh hoặc đáy xoay.                                | int           | 50       |

Ví dụ:

<pre class="language-python"><code class="lang-python">fi = client.FiinIndicator()
df['break_of_structure'] = fi.break_of_structure(df['open'],df['high'], df['low'],df['close'],swing_length=50)
<strong>df['chage_of_charactor'] = fi.chage_of_charactor(df['open'],df['high'], df['low'],df['close'])
</strong>print(df)
</code></pre>

### **5.4. Order Blocks**

Vùng giá mà các tổ chức lớn đã đặt lệnh giao dịch, tạo ra những cú đẩy mạnh về giá. Khi giá quay lại vùng OB, đây thường là điểm vào lệnh tiềm năng.

```python
def ob(self, open: pd.Series, high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series, close_mitigation: bool = False, swing_length: int = 50) -> pd.Series: ...
    
def ob_top(self, open: pd.Series, high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series, close_mitigation: bool = False, swing_length: int = 50) -> pd.Series: ...
    
def ob_bottom(self, open: pd.Series, high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series, close_mitigation: bool = False, swing_length: int = 50) -> pd.Series: ...
    
def ob_volume(self, open: pd.Series, high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series, close_mitigation: bool = False, swing_length: int = 50) -> pd.Series: ...
    
def ob_mitigated_index(self, open: pd.Series, high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series, close_mitigation: bool = False, swing_length: int = 50) -> pd.Series: ...
    
def ob_percetage(self, open: pd.Series, high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series, close_mitigation: bool = False, swing_length: int = 50) -> pd.Series: ...
```

**Tham số**

| Tên tham số       | Mô tả                                                                                               | Kiểu dữ liệu  | Mặc định |
| ----------------- | --------------------------------------------------------------------------------------------------- | ------------- | -------- |
| open              | Cột chứa giá mở cửa.                                                                                | pandas.Series |          |
| high              | Cột chứa giá cao nhất.                                                                              | pandas.Series |          |
| low               | Cột chứa giá thấp nhất.                                                                             | pandas.Series |          |
| close             | Cột chứa giá đóng cửa.                                                                              | pandas.Series |          |
| volume            | Cột chứa khối lượng giao dịch.                                                                      | pandas.Series |          |
| close\_mitigation | Nếu True, xác nhận dựa trên giá đóng cửa của nến.Nếu False, xác nhận dựa trên mức cao/thấp của nến. | bool          | False    |
| swing\_length     | Số lượng nến cần xét.                                                                               | int           | 50       |

Ví dụ:

```python
fi = client.Indicator()
df['ob'] = fi.ob(df['open'],df['high'], df['low'],df['close'],df['volume'], close_mitigation = False, swing_length = 40)
df['ob_volume'] = fi.ob_volume(df['open'],df['high'], df['low'],df['close'],df['volume'])
print(df)
```

### **5.5. Liquidity**

Thanh khoản (Liquidity) xuất hiện khi có nhiều mức cao (highs) hoặc nhiều mức thấp (lows) nằm trong một phạm vi nhỏ, cho thấy sự tích lũy lệnh trong khu vực đó.

```python
def liquidity(self, open: pd.Series, high: pd.Series, low: pd.Series, close: pd.Series, range_percent: float = 0.01, swing_length: int = 50) -> pd.Series: ...
    
def liquidity_level(self, open: pd.Series, high: pd.Series, low: pd.Series, close: pd.Series, range_percent: float = 0.01, swing_length: int = 50) -> pd.Series: ...
    
def liquidity_end(self, open: pd.Series, high: pd.Series, low: pd.Series, close: pd.Series, range_percent: float = 0.01, swing_length: int = 50) -> pd.Series: ...
    
def liquidity_swept(self, open: pd.Series, high: pd.Series, low: pd.Series, close: pd.Series, range_percent: float = 0.01, swing_length: int = 50) -> pd.Series: ...
```

**Tham số**

| Tên tham số    | Mô tả                                                                | Kiểu dữ liệu  | Mặc định |
| -------------- | -------------------------------------------------------------------- | ------------- | -------- |
| open           | Cột chứa giá mở cửa.                                                 | pandas.Series |          |
| high           | Cột chứa giá cao nhất.                                               | pandas.Series |          |
| low            | Cột chứa giá thấp nhất.                                              | pandas.Series |          |
| close          | Cột chứa giá đóng cửa.                                               | pandas.Series |          |
| range\_percent | Phần trăm phạm vi giá được sử dụng để xác định thanh khoản.          | float         | 0.01     |
| swing\_length  | Số lượng nến cần xét về trước và sau để xác định đỉnh hoặc đáy xoay. | int           | 50       |

Ví dụ:

```python
// Some codepy

fi = client.FiinIndicator()
df['liquidity'] = fi.liquidity(df['open'],df['high'], df['low'],df['close'])
print(df)
```
