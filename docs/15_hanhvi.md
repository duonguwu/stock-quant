---
description: >-
  Nhóm hàm liên quan đến thống kê hiệu suất của cổ phiếu trước và sau thời điểm
  nghỉ lễ hoặc 1 ngày bất kỳ trong tháng qua các năm
---

# Hàm thời vụ hành vi

Cấu trúc hàm: seasonality(ticker, event=None, month=None, day=None, before=5, after=5, period=10)

Các tham số

<table><thead><tr><th width="99">Tham số</th><th width="113">Kiểu dữ liệu</th><th>Mô tả</th></tr></thead><tbody><tr><td>ticker</td><td>str</td><td>Mã cổ phiếu muốn theo dõi thời vụ hành vi.</td></tr><tr><td>event</td><td>str</td><td>Sự kiện muốn theo dõi hiệu suất của cổ phiếu trước và sau sự kiện, có thể bỏ trổng. Nếu bỏ trống buộc phải điều tham số month và day. Nếu không bỏ trống chỉ được phép điền 1 trong 5 sự kiện sau: new_year_eve, tet_holiday, commemoration_day, liberation_day, independence_day. </td></tr><tr><td>month</td><td>int</td><td>Có thể bỏ trống, nếu bỏ trống buộc phải điền tham số event. Nếu không bỏ trống điền tháng muốn chọn (từ 1 đến 12)</td></tr><tr><td>day</td><td>int</td><td>Có thể bỏ trống, nếu bỏ trống buộc phải điền tham số event. Nếu không bỏ trống điền ngày muốn chọn</td></tr><tr><td>before</td><td>int</td><td>Số phiến trước ngày nghỉ lễ hoặc ngày bất kỳ muốn thống kê. Mặc định là 5</td></tr><tr><td>after</td><td>int</td><td>Số phiến sau ngày nghỉ lễ hoặc ngày bất kỳ muốn thống kê. Mặc định là 5</td></tr><tr><td>period</td><td>int</td><td>Số năm muốn thống kê. Mặc định là 10</td></tr></tbody></table>

Giá trị trả về: Danh sách phân tích gồm các thông tin sau

* Số năm tăng, số năm giảm
* Tỷ suất sinh lời trung bình
* Trung vị
* Biến động (Std Dev)
* Hiệu suất sinh lời cao nhất
* Hiệu suất sinh lời thấp nhất

Ví dụ về việc phân tích hiệu suất 5 ngày trước và sau Ngày Quốc Khánh của VNINDEX trong vòng 10 năm

```python
from FiinQuantX import FiinSession

username = "REPLACE_WITH_YOUR_USERNAME"
password = "REPLACE_WITH_YOUR_PASSWORD"

client = FiinSession(
    username=username,
    password=password
).login()

client.seasonality(ticker="VNINDEX", event="independence_day")
```

Kết quả trả ra cho ví dụ chạy tại ngày 25/06/2025

```
📈 Seasonality Analysis của mã VNINDEX trước và sau Ngày Quốc Khánh (5 ngày trước / 5 ngày sau):
- Tăng: 4 năm | Giảm: 6 năm
- Tỷ suất sinh lời trung bình: -0.30%
- Trung vị: -0.39%
- Biến động (Std Dev): 1.61%
- Lớn nhất: +1.75%
- Nhỏ nhất: -2.41%
```
