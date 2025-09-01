# Hàm dữ liệu Realtime

Mô tả cách sử dụng thư viện sau khi người dùng đã đăng nhập. Các ví dụ chi tiết được nêu ra ở cuối chương này.

```python
Events = client.Trading_Data_Stream(tickers = tickers, callback = callback)
```

**Tham số**

<table><thead><tr><th>Tên tham số</th><th width="187">Mô tả</th><th>Kiểu dữ liệu</th><th>Bắt buộc</th></tr></thead><tbody><tr><td>tickers</td><td>Tên mã , bao gồm mã chứng khoán, mã chỉ số, mã phái sinh và mã chứng quyền. Các mã này được viết in hoa.</td><td><p>str hoặc list</p><p><br></p></td><td>Có</td></tr><tr><td>callback</td><td>Là hàm do người dùng tự định nghĩa để thao tác với dữ liệu.</td><td>function</td><td>Có</td></tr></tbody></table>

Class nhận dữ liệu là Trading\_Data\_Stream, có 2 phương thức sau:

<figure><img src="https://3318188420-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2Fkme4XYjWbuM3iRJzUu9r%2Fuploads%2F9d370Vba9Vx8mVLcNLw0%2Fimage.png?alt=media&#x26;token=f871c40b-d6b5-4319-879f-02d2e24adfcd" alt=""><figcaption></figcaption></figure>

**Hàm callback**

Là phương thức do người dùng tự định nghĩa để thao tác với dữ liệu, sẽ được truyền vào khi khởi tạo đối tượng nhận dữ liệu như là một đối số. Phương thức này sẽ có dạng như sau:

```python
//pseudocode
//callback_function
def name_of_callback(data: RealTimeData):
    //do something

Events = client.Trading_Data_Stream(tickers = ['ticker_1','ticker_2',,,'ticker_n'], callback = name_of_callback)
Events.start()
# tickers can include ticker, coveredwarrant, index and derivative.
Events = client.Trading_Data_Stream(tickers = ['ticker_1','ticker_2',,,'ticker_n'], callback = name_of_callback)
Events.start()
```

RealTimeData có các phương thức và thuộc tính sau:\


| Tên phương thức của object dữ liệu | Mô tả                                                                                                                  |
| ---------------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| to\_dataFrame( )                   | Trả về tất cả các thuộc tính của dữ liệu thay vì một thuộc tính riêng lẻ, được lưu trữ dưới dạng một Pandas DataFrame. |

**Dữ liệu RealTimeData có các thuộc tính:**

| Tên cột                | Mô tả                                         | Kiểu dữ liệu |
| ---------------------- | --------------------------------------------- | ------------ |
| Ticker                 | Tên mã.                                       | str          |
| TotalMatchVolume       | Tổng khối lượng.                              | int          |
| MarketStatus           | Trạng thái thị trường.                        | str          |
| TradingDate            | Thời gian.                                    | str          |
| ComGroupCode           | Mã chỉ số.                                    | str          |
| Reference              | Giá trị tham chiếu.                           | float        |
| Open                   | Giá Open.                                     | float        |
| Close                  | Giá Close.                                    | float        |
| High                   | Giá High.                                     | float        |
| Low                    | Giá Low.                                      | float        |
| Change                 | Giá trị thay đổi so với tham chiếu.           | float        |
| ChangePercent          | Phần trăm giá trị thay đổi so với tham chiếu. | float        |
| MatchVolume            | Khối lượng khớp lệnh.                         | int          |
| MatchValue             | Giá trị khớp lệnh.                            | float        |
| TotalMatchValue        | Tổng giá trị khớp lệnh.                       | float        |
| TotalBuyTradeVolume    | Tổng khối lượng mua vào.                      | int          |
| TotalSellTradeVolume   | Tổng khối lượng bán ra.                       | int          |
| TotalDealVolume        | Tổng khối lượng khớp lệnh thỏa thuận.         | int          |
| TotalDealValue         | Tổng giá trị khớp lệnh thỏa thuận.            | float        |
| ForeignBuyVolumeTotal  | Tổng khối lượng mua ngoại từ đầu ngày.        | int          |
| ForeignBuyValueTotal   | Tổng giá trị mua ngoại từ đầu ngày.           | float        |
| ForeignSellVolumeTotal | Tổng khối lượng bán ngoại từ đầu ngày.        | int          |
| ForeignSellValueTotal  | Tổng giá trị bán ngoại từ đầu ngày.           | float        |
| Bu                     | Khối lượng mua chủ động.                      | int          |
| Sd                     | Khối lượng bán chủ động.                      | int          |

Ví dụ về dữ liệu khớp lệnh (RealTimeData):

```python
import pandas as pd
import time

from FiinQuantX import FiinSession, RealTimeData

username = 'REPLACE_WITH_YOUR_USER_NAME'
password = 'REPLACE_WITH_YOUR_PASS_WORD'

client = FiinSession(username=username, password=password).login()

tickers = ['HPG','VNINDEX','VN30F1M']

def onTickerEvent(data: RealTimeData):
    print('----------------')
    print(data.to_dataFrame())
    # data.to_dataFrame().to_csv('callback.csv', mode='a', header=True)
Events = client.Trading_Data_Stream(tickers=tickers, callback = onTickerEvent)
Events.start()

try:
    while not Events._stop: 
        time.sleep(1)
except KeyboardInterrupt:
    print("KeyboardInterrupt received, stopping...")
    Events.stop()
```
