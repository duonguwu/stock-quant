# Hàm nối dữ liệu Realtime và lịch sử

## 6. Nối dữ liệu lịch sử và thời gian thực

Cơ chế hoạt động của hàm nối dữ liệu lịch sử và realtime:

* Tại thời điểm người dùng gọi lần đầu, thư viện sẽ lấy dữ liệu lịch sử phù hợp với timeframe người dùng gọi.
* Khi thông số realtime = True, thư viện sẽ kết nối dữ liệu qua websocket, và cập nhật data theo thời gian thực (realtime), các timeframe tiếp theo sẽ được tổng hợp từ dữ liệu realtime.

{% hint style="warning" %}
**Cảnh báo:** Do các timeframe được cập nhật tiếp theo thời gian thực, vì vậy việc duy trì kết nối ổn định sẽ đảm bảo dữ liệu được tổng hợp chính xác nhất. Đối với kết nối realtime, khuyến khích người dùng sử dụng đường truyền qua mạng có dây (LAN) và đường internet ổn định.

**Trường hợp cần đồng bộ với data từ server,** user có thể xây dựng cơ chế gọi lại hàm khi cần để lấy lại dữ liệu lịch sử tổng hợp trên server.&#x20;
{% endhint %}

Lưu ý: Do có một độ trễ nhỏ giữa server và phía thư viện nên khi thực thi code nối dữ liệu realtime, người dùng sẽ cần phải chờ một chút để dữ liệu được đồng bộ và chính xác.

Lưu ý: Khi truyền period ở chế độ realtime = True, period là số nến lịch sử. Tức là ví dụ ở lần gọi đầu tiên với period = 100 thì sẽ là 100 nến gần nhất, với nến thứ 100 là nến realtime vẫn đang được cập nhật. Và khi sang các nến khác thì dữ liệu trả về sẽ nhiều hơn 100.

```python
event = client.Fetch_Trading_Data(
    realtime = True, 
    tickers = tickers,
    fields = ['open','high','low','close','volume','bu','sd'], 
    by = by,
    callback = callback, 
    adjusted = True,
    period = 100,
    wait_for_full_timeFrame = False
)
```

**Tham số: (Lưu ý:** period chỉ tồn tại khi không truyền from\_date và ngược lại)

| Tên tham số                | Mô tả                                                                                                                             | Kiểu dữ liệu  | Mặc định | Bắt buộc       |
| -------------------------- | --------------------------------------------------------------------------------------------------------------------------------- | ------------- | -------- | -------------- |
| realtime                   | Có đăng ký vào dữ liệu update liên tục hay không hay chỉ gọi dữ liệu lịch sử đến thời điểm mới nhất (True là có, False là không). | bool          |          | Có.            |
| tickers                    | Danh sách mã được viết in hoa.                                                                                                    | str hoặc list |          | Có.            |
| fields                     | Các trường dữ liệu cần lấy. \['open','high','low','close','volume','bu','sd'] ứng với Open, High, Low, Close, Volume, BU, SD.     | list          |          | Có.            |
| adjusted                   | Giá điều chỉnh hay chưa điều chỉnh (True là đã điều chỉnh và ngược lại).                                                          | bool          | True     | Không.         |
| callback                   | Là hàm do người dùng tự định nghĩa để thao tác với dữ liệu.                                                                       | function      |          | Có.            |
| by                         | Đơn vị thời gian(1m, 5m, 15m, 30m, 1h, 2h, 4h, 1d).                                                                               | str           | 1M       | Không.         |
| period                     | Số nến lịch sử gần nhất cần lấy.                                                                                                  | int           |          | Không.         |
| from\_date                 | Mốc thời gian lấy dữ liệu xa nhất.                                                                                                | str           | datetime |                |
| to\_date                   | Mốc thời gian lấy dữ liệu gần nhất.                                                                                               | str           | datetime | datetime.now() |
| wait\_for\_full\_timeFrame | Chờ hết nến mới gọi callback hay khôngTrue là chờ hết cây nến.False là cập nhật liên tục.                                         | bool          | False.   | Không.         |
|                            |                                                                                                                                   |               |          |                |

**Hàm callback**

Là phương thức do người dùng tự định nghĩa để thao tác với dữ liệu, sẽ được truyền vào khi khởi tạo đối tượng nhận dữ liệu như là một đối số. Phương thức này sẽ có dạng như sau:

```python
### pseudocode

## callback_function
def name_of_callback(data: BarDataUpdate):
    ## do something

event = client.Fetch_Trading_Data(
    realtime=True,
    tickers=tickers,
    fields = ['open','high','low','close','volume','bu','sd'], 
    adjusted=True,
    callback=name_of_callback,
    by='1M', 
    from_date='2024-11-28 09:00'
)

event.get_data()
```



Dữ liệu cổ phiếu có các thuộc tính:

| Tên thuộc tính | Mô tả                   | Kiểu dữ liệu |
| -------------- | ----------------------- | ------------ |
| ticker         | Tên mã.                 | str          |
| timestamp      | Thời gian giao dịch.    | int          |
| open           | Giá mở cửa.             | float        |
| low            | Giá thấp nhất.          | float        |
| high           | Giá cao nhất.           | float        |
| close          | Giá đóng cửa.           | float        |
| volume         | Khối lượng giao dịch.   | int          |
| bu             | Khối lượng mua.         | int          |
| sd             | Khối lượng bán.         | int          |
| fb             | Giá trị bán khối ngoại. | int          |
| fs             | Giá trị mua khối ngoại. | int          |
| fn             | Giá trị mua/bán ròng.   | int          |

Ví dụ

* Trường hợp 1: Sử dụng from\_date

Copy

```python
import time
import pandas as pd
from FiinQuantX import FiinSession, BarDataUpdate

username = 'REPLACE_WITH_YOUR_USER_NAME'
password = 'REPLACE_WITH_YOUR_PASS_WORD'

client = FiinSession(username=username, password=password).login()

tickers = ['HPG', 'SSI', 'VNM', 'VIC', 'VRE']

def onUpdate(data: BarDataUpdate):
    print(data.to_dataFrame())
    print('-------------Callback-------------')
    
event = client.Fetch_Trading_Data(
    realtime = True,
    tickers = tickers,    
    fields = ['open','high','low','close','volume','bu','fn'],
    by = '1m', 
    callback = onUpdate, 
    from_date='2024-11-28 09:00',
    wait_for_full_timeFrame = False
)

event.get_data()

try:
    while not event._stop:
        time.sleep(1)
except KeyboardInterrupt:
    print("KeyboardInterrupt received, stopping...")
    event.stop()
```

* Trường hợp 2: Sử dụng period

Copy

```python
import time
import pandas as pd
from FiinQuantX import FiinSession, BarDataUpdate

username = 'REPLACE_WITH_YOUR_USER_NAME'
password = 'REPLACE_WITH_YOUR_PASS_WORD'

client = FiinSession(username=username, password=password).login()

tickers = ['HPG', 'SSI', 'VN30', 'VN30F1M', 'VRE']

def onUpdate(data: BarDataUpdate):
    print(data.to_dataFrame())
    print('-------------Callback-------------')
    
event = client.Fetch_Trading_Data(
    realtime = True,
    tickers = tickers,    
    fields = ['open', 'high', 'low', 'close', 'volume', 'bu'],
    by = '1m', 
    period = 10,
    callback = onUpdate, 
    wait_for_full_timeFrame=False
)

event.get_data()
time.sleep(3600)
event.stop()
#Ví dụ chạy 1 giờ rồi ngưng.
```



| Tên phương thức | Mô tả                                                                                              |
| --------------- | -------------------------------------------------------------------------------------------------- |
| get\_data()     | Nhận dữ liệu lasted nếu realtime = False hoặc bắt đầu kết nối và nhận dữ liệu với realtime = True. |
| stop( )         | Dừng kết nối.                                                                                      |
