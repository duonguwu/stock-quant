# Hàm phân tích cơ bản

## 8. Hàm báo cáo tài chính

Mô tả cách sử dụng thư viện sau khi người dùng đã đăng nhập. Các ví dụ chi tiết được nêu ra ở cuối chương này.

```python
fs_dict = client.FundamentalAnalysis().get_financeStatement(
    tickers=tickers,
    statement=statement,
    years=years,
    quarters=quarters,
    audited=True,
    type=type,
    fields=fields
)
```

**Tham số:**

| Tên tham số | Mô tả                                                                                                                                                                                                                                                                         | Kiểu dữ liệu  | Mặc định | Bắt buộc |
| ----------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------- | -------- | -------- |
| tickers     | Danh sách mã được viết in hoa.                                                                                                                                                                                                                                                | str hoặc list |          | Có       |
| statement   | Loại báo cáo tài chính, là 1 trong 3 giá trị ‘balancesheet’, ‘incomestatement’, ‘cashflow’, hoặc ‘full’ là lấy hết. Nếu muốn lấy nhiều loại báo cáo tài chính thì liệt kê list các loại ra.                                                                                   | str           |          | Có       |
| years       | Năm của kỳ báo cáo, có thể chọn nhiều năm bằng cách liệt kê list các năm ra                                                                                                                                                                                                   | list\[int]    |          | Có       |
| quarters    | Quý của kỳ báo cáo, nếu không truyền mặc định lấy báo cáo tài chính của năm dựa trên tham số year, có thể chọn nhiều quý bằng cách liệt kê list các quý ra                                                                                                                    | list\[int]    | None     | Không    |
| audited     | Kiểm toán hay chưa (True là đã kiểm toán, False là chưa kiểm toán).                                                                                                                                                                                                           | bool          |          | Có       |
| type        | 1 trong 2 giá trị (‘consolidated’ hoặc ‘separate’). 'consolidated' là báo cáo tài chính hợp nhất, 'separate' là báo cáo tài chính công ty mẹ                                                                                                                                  | str           |          | Có       |
| fields      | Trường dữ liệu cần lấy (không truyền sẽ lấy hết). Biến fields có thể truyền theo dạng đường dẫn phân cấp cách nhau bằng dấu chấm ('Assets'.'CurrentAssets' – Lấy phần Tài sản ngắn hạn trong báo cáo tài chính) hoặc truyền thẳng sections là node cần lấy ('CurrentAssets'). | str           | None     | Không    |

Class nhận dữ liệu là FundamentalAnalysis và có phương thức nhận dữ liệu là get\_financeStatement()

```python
### pseudocode
import json

fs_dict = client.FundamentalAnalysis().get_financeStatement(
    tickers=tickers,
    statement="balancesheet",
    years=[2024],
    quarters=[4],
    audited=True,
    type="consolidated"
)

print(json.dumps(fs_dict, indent=4))
```

* Ví dụ lấy dữ liệu full bảng cân đối kế toán của báo cáo tài chính hợp nhất đã kiểm toán quý 4 năm 2024 của mã HPG&#x20;

```python
import json

from FiinQuantX import FiinSession

username = 'REPLACE_WITH_YOUR_USER_NAME'
password = 'REPLACE_WITH_YOUR_PASS_WORD'

client = FiinSession(username=username, password=password).login()

tickers = ['HPG']

fs_dict = client.FundamentalAnalysis().get_financeStatement(
    tickers=tickers,
    statement="balancesheet",
    years=[2024],
    quarters=[4],
    audited=True,
    type="consolidated"
)

print(json.dumps(fs_dict, indent=4))
```

* Ví dụ lấy dữ liệu phần TỔNG TÀI SẢN thuộc bảng cân đối kế toán của báo cáo tài chính hợp nhất đã kiểm toán quý 4 năm 2024 của mã HPG

```python
import json

from FiinQuantX import FiinSession

username = 'REPLACE_WITH_YOUR_USER_NAME'
password = 'REPLACE_WITH_YOUR_PASS_WORD'

client = FiinSession(username=username, password=password).login()

tickers = ['HPG']

fs_dict = client.FundamentalAnalysis().get_financeStatement(
    tickers=tickers,
    statement="balancesheet",
    years=[2024],
    quarters=[4],
    audited=True,
    type="consolidated",
    fields=["Assets"]
)

print(json.dumps(fs_dict, indent=4))
```

* Ví dụ lấy dữ liệu phần TÀI SẢN NGẮN HẠN nằm trong phần TỔNG TÀI SẢN thuộc bảng cân đối kế toán của báo cáo tài chính hợp nhất đã kiểm toán quý 4 năm 2024 của mã HPG

```python
import json

from FiinQuantX import FiinSession

username = 'REPLACE_WITH_YOUR_USER_NAME'
password = 'REPLACE_WITH_YOUR_PASS_WORD'

client = FiinSession(username=username, password=password).login()

tickers = ['HPG']

fs_dict = client.FundamentalAnalysis().get_financeStatement(
    tickers=tickers,
    statement="balancesheet",
    years=[2024],
    quarters=[4],
    audited=True,
    type="consolidated",
    fields=["CurrentAssets"]
)

print(json.dumps(fs_dict, indent=4))
```

## 9. Hàm chỉ số báo cáo tài chính

Mô tả cách sử dụng thư viện sau khi người dùng đã đăng nhập. Các ví dụ chi tiết được nêu ra ở cuối chương này.

```python
fi_dict = client.FundamentalAnalysis().get_ratios(
    tickers=tickers,
    TimeFilter=TimeFilter,
    LatestYear=LatestYear,
    NumberOfPeriod=NumberOfPeriod,
    Consolidated=Consolidated
)
```

**Tham số:**

| Tên tham số    | Mô tả                                                                                                                                                                                                                             | Kiểu dữ liệu  | Mặc định | Bắt buộc |
| -------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------- | -------- | -------- |
| tickers        | Danh sách mã được viết in hoa.                                                                                                                                                                                                    | str hoặc list |          | Có       |
| TimeFilter     | Xem theo năm hoặc quý, truyền 1 trong 2 giá trị "Yearly" hoặc "Quarterly"                                                                                                                                                         | str           |          | Có       |
| LatestYear     | Năm gần nhất muốn xem báo cáo                                                                                                                                                                                                     | int           |          | Có       |
| NumberOfPeriod | Số kỳ muốn xem báo cáo                                                                                                                                                                                                            | int           |          | Có       |
| Consolidated   | <ul><li>True: Chỉ số của báo cáo hợp nhấy</li><li>False: Chỉ số của báo cáo công ty mẹ</li></ul>                                                                                                                                  | bool          |          | Có       |
| Fields         | Trường dữ liệu cần lấy (không truyền sẽ lấy hết). Biến fields có thể truyền theo dạng đường dẫn phân cấp cách nhau bằng dấu chấm (ProfitabilityRatio'.'ROA' – Lấy chỉ số ROA) hoặc truyền thẳng sections là node cần lấy ('ROA'). | str           | None     | Không    |

Class nhận dữ liệu là FundamentalAnalysis và có phương thức nhận dữ liệu là get\_ratios()

```python
### pseudocode
import json

fs_dict = client.FundamentalAnalysis().get_ratios(
    tickers=tickers,
    TimeFilter="Quarterly",
    LatestYear=2025,
    NumberOfPeriod=2,
    Consolidated=True
)

print(json.dumps(fs_dict, indent=4))
```

* Ví dụ lấy dữ liệu full chỉ số báo cáo tài chính hợp nhất của 4 quý trong năm 2024 của mã HPG

```python
import json

from FiinQuantX import FiinSession

username = 'REPLACE_WITH_YOUR_USER_NAME'
password = 'REPLACE_WITH_YOUR_PASS_WORD'

client = FiinSession(username=username, password=password).login()

tickers = ['HPG']

fi_dict = client.FundamentalAnalysis().get_ratios(
    tickers=tickers,
    TimeFilter="Quarterly",
    LatestYear=2024,
    NumberOfPeriod=4,
    Consolidated=True
)

print(json.dumps(fi_dict, indent=4))
```

* &#x20;Ví dụ lấy dữ liệu nhóm chỉ số báo cáo tài chính KHẢ NĂNG SINH LỢI dựa trên báo cáo tài chính hợp nhất của 4 quý năm 2024 của mã HPG

```python
import json

from FiinQuantX import FiinSession

username = 'REPLACE_WITH_YOUR_USER_NAME'
password = 'REPLACE_WITH_YOUR_PASS_WORD'

client = FiinSession(username=username, password=password).login()

tickers = ['HPG']

fi_dict = client.FundamentalAnalysis().get_ratios(
    tickers=tickers,
    TimeFilter="Quarterly",
    LatestYear=2024,
    NumberOfPeriod=4,
    Consolidated=True,
    Fields=["ProfitabilityRatio"]
)

print(json.dumps(fi_dict, indent=4))
```

* Ví dụ lấy dữ liệu chỉ số ROA thuộc nhóm chỉ số báo cáo tài chính KHẢ NĂNG SINH LỢI dựa trên báo cáo tài chính hợp của 4 quý năm 2024 của mã HPG

```python
import json

from FiinQuantX import FiinSession

username = 'REPLACE_WITH_YOUR_USER_NAME'
password = 'REPLACE_WITH_YOUR_PASS_WORD'

client = FiinSession(username=username, password=password).login()

tickers = ['HPG']

fi_dict = client.FundamentalAnalysis().get_ratios(
    tickers=tickers,
    TimeFilter="Quarterly",
    LatestYear=2024,
    NumberOfPeriod=4,
    Consolidated=True,
    Fields=["ProfitabilityRatio.ROA"]
)

print(json.dumps(fi_dict, indent=4))
```

