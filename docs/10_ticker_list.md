---
description: Hàm gọi ra danh sách ticker tùy vào tên INDEX do người dùng truyền vào
---

# Hàm gọi danh sách ticker

### Hàm TickerList

Bằng cách nhập vào tên INDEX (Ví dụ: VN30, VN100, VNINDEX, HNXINDEX, v.v.) hàm sẽ trả ra 1 danh sách các mã thuộc INDEX đó, điều này sẽ thuận tiện cho người dùng muốn gọi dữ liệu lịch sử của các mã thuộc cùng 1 rổ INDEX.

Code mẫu:

```python
from FiinQuantX import FiinSession

username = "REPLACE_WITH_YOUR_USERNAME"
password = "REPLACE_WITH_YOUR_PASSWORD"

client = FiinSession(username=username, password=password).login()

tickers =client.TickerList(ticker="VN30")
print(tickers)
```

Kết quả trả ra:

\['ACB', 'BID', 'BCM', 'BVH', 'CTG', 'FPT', 'GAS', 'HDB', 'HPG', 'LPB', 'MBB', 'MSN', 'MWG', 'VHM', 'PLX', 'SAB', 'SSB', 'SHB', 'SSI', 'STB', 'TCB', 'TPB', 'VCB', 'VIB', 'VIC', 'VJC', 'VNM', 'GVR', 'VPB', 'VRE']

Ví dụ về việc lấy dữ liệu OHLCV lịch sử của các mã thuộc rổ VN30:

```python
from FiinQuantX import FiinSession

username = "REPLACE_WITH_YOUR_USERNAME"
password = "REPLACE_WITH_YOUR_PASSWORD"

client = FiinSession(username=username, password=password).login()

tickers =client.TickerList(ticker="VN30")

data = client.Fetch_Trading_Data(
    realtime=False,
    tickers=tickers,
    fields=["open","high","low","close","volume"],
    adjusted=True,
    by="1d",
    from_date="2025-06-18"
).get_data()

print(data)
```
