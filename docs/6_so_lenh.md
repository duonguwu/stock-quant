# Hàm dữ liệu sổ lệnh

## 7. Dữ liệu chi tiết về các bước giá trong từng sổ lệnh tại thời gian thực

Mô tả cách sử dụng thư viện sau khi người dùng đã đăng nhập. Các ví dụ chi tiết được nêu ra ở cuối chương này.

```python
event = client.BidAsk(tickers = tickers, callback = callback)
```

**Tham số**

<table><thead><tr><th>Tên tham số</th><th width="187">Mô tả</th><th>Kiểu dữ liệu</th><th>Bắt buộc</th></tr></thead><tbody><tr><td>tickers</td><td>Tên mã , bao gồm mã chứng khoán, mã chỉ số, mã phái sinh và mã chứng quyền. Các mã này được viết in hoa.</td><td><p>str hoặc list</p><p><br></p></td><td>Có</td></tr><tr><td>callback</td><td>Là hàm do người dùng tự định nghĩa để thao tác với dữ liệu.</td><td>function</td><td>Có</td></tr></tbody></table>

Class nhận dữ liệu là BidAsk, có 2 phương thức sau:

<figure><img src="https://3318188420-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2Fkme4XYjWbuM3iRJzUu9r%2Fuploads%2F9d370Vba9Vx8mVLcNLw0%2Fimage.png?alt=media&#x26;token=f871c40b-d6b5-4319-879f-02d2e24adfcd" alt=""><figcaption></figcaption></figure>

**Hàm callback**

Là phương thức do người dùng tự định nghĩa để thao tác với dữ liệu, sẽ được truyền vào khi khởi tạo đối tượng nhận dữ liệu như là một đối số. Phương thức này sẽ có dạng như sau:

```
//pseudocode
//callback_function
def name_of_callback(data: BidAskData):
    //do something

event = client.BidAsk(tickers = ['ticker_1','ticker_2',,,'ticker_n'], callback = name_of_callback)
event.start()
# tickers can include ticker, coveredwarrant, index and derivative.
event = client.BidAsk(tickers = ['ticker_1','ticker_2',,,'ticker_n'], callback = name_of_callback)
evente.start()
```

BidAskData có các phương thức và thuộc tính sau:

| Tên phương thức của object dữ liệu | Mô tả                                                                                                                  |
| ---------------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| to\_dataFrame( )                   | Trả về tất cả các thuộc tính của dữ liệu thay vì một thuộc tính riêng lẻ, được lưu trữ dưới dạng một Pandas DataFrame. |

**Dữ liệu BidAskData có các thuộc tính:**

<table><thead><tr><th width="163">Tên cột</th><th width="500">Mô tả</th><th>Kiểu dữ liệu</th></tr></thead><tbody><tr><td>ComGroupCode</td><td>Mã chỉ số.</td><td>str</td></tr><tr><td>StockType</td><td>Loại chứng khoán.</td><td>str</td></tr><tr><td>Ticker</td><td>Tên mã.</td><td>str</td></tr><tr><td>TradingDate</td><td>Thời gian.</td><td>str</td></tr><tr><td>Timestamp</td><td>Thời gian (làm tròn về giây).</td><td>str</td></tr><tr><td>Spread</td><td>Best1Ask - Best1Bid.</td><td>float</td></tr><tr><td>SpreadDelta</td><td>Spread tick hiện tại - Spread tick trước.</td><td>float</td></tr><tr><td>DepthImbalance</td><td>TotalBidVolume / (TotalBidVolume + TotalAskVolume).</td><td>float</td></tr><tr><td>TotalBuyTradeVolume</td><td>Tổng khối lượng giao dịch mua.</td><td>int</td></tr><tr><td>TotalSellTradeVolum</td><td>Tổng khối lượng giao dịch bán.</td><td>int</td></tr><tr><td>TotalBidVolume</td><td>Tổng khối lượng đặt mua.</td><td>int</td></tr><tr><td>TotalAskVolume</td><td>Tổng khối lượng đặt bán.</td><td>int</td></tr><tr><td>Best1Bid</td><td>Bước giá mua 1.</td><td>float</td></tr><tr><td>Best2Bid</td><td>Bước giá mua 2.</td><td>float</td></tr><tr><td>Best3Bid</td><td>Bước giá mua 3.</td><td>float</td></tr><tr><td>Best4Bid</td><td>Bước giá mua 4.</td><td>float</td></tr><tr><td>Best5Bid</td><td>Bước giá mua 5.</td><td>float</td></tr><tr><td>Best6Bid</td><td>Bước giá mua 6.</td><td>float</td></tr><tr><td>Best7Bid</td><td>Bước giá mua 7.</td><td>float</td></tr><tr><td>Best8Bid</td><td>Bước giá mua 8.</td><td>float</td></tr><tr><td>Best9Bid</td><td>Bước giá mua 9.</td><td>float</td></tr><tr><td>Best10Bid</td><td>Bước giá mua 10.</td><td>float</td></tr><tr><td>Best1Ask</td><td>Bước giá bán 1.</td><td>float</td></tr><tr><td>Best2Ask</td><td>Bước giá bán 2.</td><td>float</td></tr><tr><td>Best3Ask</td><td>Bước giá bán 3.</td><td>float</td></tr><tr><td>Best4Ask</td><td>Bước giá bán 4.</td><td>float</td></tr><tr><td>Best5Ask</td><td>Bước giá bán 5.</td><td>float</td></tr><tr><td>Best6Ask</td><td>Bước giá bán 6.</td><td>float</td></tr><tr><td>Best7Ask</td><td>Bước giá bán 7.</td><td>float</td></tr><tr><td>Best8Ask</td><td>Bước giá bán 8.</td><td>float</td></tr><tr><td>Best9Ask</td><td>Bước giá bán 9.</td><td>float</td></tr><tr><td>Best10Ask</td><td>Bước giá bán 10.</td><td>float</td></tr><tr><td>Best1BidVolume</td><td>Khối lượng đặt mua bước giá mua 1.</td><td>int</td></tr><tr><td>Best2BidVolume</td><td>Khối lượng đặt mua bước giá mua 2.</td><td>int</td></tr><tr><td>Best3BidVolume</td><td>Khối lượng đặt mua bước giá mua 3.</td><td>int</td></tr><tr><td>Best4BidVolume</td><td>Khối lượng đặt mua bước giá mua 4.</td><td>int</td></tr><tr><td>Best5BidVolume</td><td>Khối lượng đặt mua bước giá mua 5.</td><td>int</td></tr><tr><td>Best6BidVolume</td><td>Khối lượng đặt mua bước giá mua 6.</td><td>int</td></tr><tr><td>Best7BidVolume</td><td>Khối lượng đặt mua bước giá mua 7.</td><td>int</td></tr><tr><td>Best8BidVolume</td><td>Khối lượng đặt mua bước giá mua 8.</td><td>int</td></tr><tr><td>Best9BidVolume</td><td>Khối lượng đặt mua bước giá mua 9.</td><td>int</td></tr><tr><td>Best10BidVolume</td><td>Khối lượng đặt mua bước giá mua 10.</td><td>int</td></tr><tr><td>Best1AskVolume</td><td>Khối lượng đặt bán bước giá bán 1.</td><td>int</td></tr><tr><td>Best2AskVolume</td><td>Khối lượng đặt bán bước giá bán 2.</td><td>int</td></tr><tr><td>Best3AskVolume</td><td>Khối lượng đặt bán bước giá bán 3.</td><td>int</td></tr><tr><td>Best4AskVolume</td><td>Khối lượng đặt bán bước giá bán 4.</td><td>int</td></tr><tr><td>Best5AskVolume</td><td>Khối lượng đặt bán bước giá bán 5.</td><td>int</td></tr><tr><td>Best6AskVolume</td><td>Khối lượng đặt bán bước giá bán 6.</td><td>int</td></tr><tr><td>Best7AskVolume</td><td>Khối lượng đặt bán bước giá bán 7.</td><td>int</td></tr><tr><td>Best8AskVolume</td><td>Khối lượng đặt bán bước giá bán 8.</td><td>int</td></tr><tr><td>Best9AskVolume</td><td>Khối lượng đặt bán bước giá bán 9.</td><td>int</td></tr><tr><td>Best10AskVolume</td><td>Khối lượng đặt bán bước giá bán 10.</td><td>int</td></tr><tr><td>BidPriceDelta1</td><td>Chênh lệch bước giá mua 1 tick hiện tại với tick trước.</td><td>float</td></tr><tr><td>BidPriceDelta2</td><td>Chênh lệch bước giá mua 2 tick hiện tại với tick trước.</td><td>float</td></tr><tr><td>BidPriceDelta3</td><td>Chênh lệch bước giá mua 3 tick hiện tại với tick trước.</td><td>float</td></tr><tr><td>BidPriceDelta4</td><td>Chênh lệch bước giá mua 4 tick hiện tại với tick trước.</td><td>float</td></tr><tr><td>BidPriceDelta5</td><td>Chênh lệch bước giá mua 5 tick hiện tại với tick trước.</td><td>float</td></tr><tr><td>BidPriceDelta6</td><td>Chênh lệch bước giá mua 6 tick hiện tại với tick trước.</td><td>float</td></tr><tr><td>BidPriceDelta7</td><td>Chênh lệch bước giá mua 7 tick hiện tại với tick trước.</td><td>float</td></tr><tr><td>BidPriceDelta8</td><td>Chênh lệch bước giá mua 8 tick hiện tại với tick trước.</td><td>float</td></tr><tr><td>BidPriceDelta9</td><td>Chênh lệch bước giá mua 9 tick hiện tại với tick trước.</td><td>float</td></tr><tr><td>BidPriceDelta10</td><td>Chênh lệch bước giá  mua 10 tick hiện tại với tick trước.</td><td>float</td></tr><tr><td>AskPriceDelta1</td><td>Chênh lệch bước giá bán 1 tick hiện tại với tick trước.</td><td>float</td></tr><tr><td>AskPriceDelta2</td><td>Chênh lệch bước giá bán 2 tick hiện tại với tick trước.</td><td>float</td></tr><tr><td>AskPriceDelta3</td><td>Chênh lệch bước giá bán 3 tick hiện tại với tick trước.</td><td>float</td></tr><tr><td>AskPriceDelta4</td><td>Chênh lệch bước giá bán 4 tick hiện tại với tick trước.</td><td>float</td></tr><tr><td>AskPriceDelta5</td><td>Chênh lệch bước giá bán 5 tick hiện tại với tick trước.</td><td>float</td></tr><tr><td>AskPriceDelta6</td><td>Chênh lệch bước giá bán 6 tick hiện tại với tick trước.</td><td>float</td></tr><tr><td>AskPriceDelta7</td><td>Chênh lệch bước giá bán 7 tick hiện tại với tick trước.</td><td>float</td></tr><tr><td>AskPriceDelta8</td><td>Chênh lệch bước giá bán 8 tick hiện tại với tick trước.</td><td>float</td></tr><tr><td>AskPriceDelta9</td><td>Chênh lệch bước giá bán 9 tick hiện tại với tick trước.</td><td>float</td></tr><tr><td>AskPriceDelta10</td><td>Chênh lệch bước giá bán 10 tick hiện tại với tick trước.</td><td>float</td></tr><tr><td>BidVolumeDelta1</td><td>Chênh lệch khối lượng bước giá mua 1 tick hiện tại với tick trước.</td><td>int</td></tr><tr><td>BidVolumeDelta2</td><td>Chênh lệch khối lượng bước giá mua 2 tick hiện tại với tick trước.</td><td>int</td></tr><tr><td>BidVolumeDelta3</td><td>Chênh lệch khối lượng bước giá mua 3 tick hiện tại với tick trước.</td><td>int</td></tr><tr><td>BidVolumeDelta4</td><td>Chênh lệch khối lượng bước giá mua 4 tick hiện tại với tick trước.</td><td>int</td></tr><tr><td>BidVolumeDelta5</td><td>Chênh lệch khối lượng bước giá mua 5 tick hiện tại với tick trước.</td><td>int</td></tr><tr><td>BidVolumeDelta6</td><td>Chênh lệch khối lượng bước giá mua 6 tick hiện tại với tick trước.</td><td>int</td></tr><tr><td>BidVolumeDelta7</td><td>Chênh lệch khối lượng bước giá mua 7 tick hiện tại với tick trước.</td><td>int</td></tr><tr><td>BidVolumeDelta8</td><td>Chênh lệch khối lượng bước giá mua 8 tick hiện tại với tick trước.</td><td>int</td></tr><tr><td>BidVolumeDelta9</td><td>Chênh lệch khối lượng bước giá mua 9 tick hiện tại với tick trước.</td><td>int</td></tr><tr><td>BidVolumeDelta10</td><td>Chênh lệch khối lượng bước giá mua 10 tick hiện tại với tick trước.</td><td>int</td></tr><tr><td>AskVolumeDelta1</td><td>Chênh lệch khối lượng bước giá bán 1 tick hiện tại với tick trước.</td><td>int</td></tr><tr><td>AskVolumeDelta2</td><td>Chênh lệch khối lượng bước giá bán 2 tick hiện tại với tick trước.</td><td>int</td></tr><tr><td>AskVolumeDelta3</td><td>Chênh lệch khối lượng bước giá bán 3 tick hiện tại với tick trước.</td><td>int</td></tr><tr><td>AskVolumeDelta4</td><td>Chênh lệch khối lượng bước giá bán 4 tick hiện tại với tick trước.</td><td>int</td></tr><tr><td>AskVolumeDelta5</td><td>Chênh lệch khối lượng bước giá bán 5 tick hiện tại với tick trước.</td><td>int</td></tr><tr><td>AskVolumeDelta6</td><td>Chênh lệch khối lượng bước giá bán 6 tick hiện tại với tick trước.</td><td>int</td></tr><tr><td>AskVolumeDelta7</td><td>Chênh lệch khối lượng bước giá bán 7 tick hiện tại với tick trước.</td><td>int</td></tr><tr><td>AskVolumeDelta8</td><td>Chênh lệch khối lượng bước giá bán 8 tick hiện tại với tick trước.</td><td>int</td></tr><tr><td>AskVolumeDelta9</td><td>Chênh lệch khối lượng bước giá bán 9 tick hiện tại với tick trước.</td><td>int</td></tr><tr><td>AskVolumeDelta10</td><td>Chênh lệch khối lượng bước giá bán 10 tick hiện tại với tick trước.</td><td>int</td></tr><tr><td>VWAPBid</td><td>Mức giá trung bình mà người mua sẵn sàng trả.</td><td>float</td></tr><tr><td>VWAPAsk</td><td>Mức giá trung bình mà người bán sẵn sàng chấp nhận.</td><td>float</td></tr><tr><td>VWAPBidSpread</td><td>Hiệu số giữa giá mua tốt nhất (Best1Bid) và VWAP Bid.</td><td>float</td></tr><tr><td>VWAPAskSpread</td><td>Hiệu số giữa VWAP Ask và giá bán tốt nhất (Best1Ask).</td><td>float</td></tr><tr><td>VWAPBidAskSpread</td><td>Chênh lệch giữa VWAP Ask và VWAP Bid.</td><td>float</td></tr><tr><td>OrderFlowImbalance</td><td>VWAPBidSpread/ (VWAPBidSpread + VWAPAskSpread).</td><td>float</td></tr></tbody></table>

Ví dụ về dữ liệu sổ lệnh (BidAskData):

<pre class="language-python"><code class="lang-python"><strong>from FiinQuantX import FiinSession, BidAskData
</strong><strong>
</strong>import pandas as pd
import time

username = 'REPLACE_WITH_YOUR_USER_NAME'
password = 'REPLACE_WITH_YOUR_PASS_WORD'

client = FiinSession(username=username, password=password).login()

tickers = ['HPG','VNINDEX','VN30F1M']

def onTickerEvent(data: BidAskData):
    print('----------------')
    print(data.to_dataFrame())

Events = client.BidAsk(tickers=tickers, callback = onTickerEvent)
Events.start()

try:
    while not Events._stop: 
        time.sleep(1)
except KeyboardInterrupt:
    print("KeyboardInterrupt received, stopping...")
    Events.stop()
</code></pre>
