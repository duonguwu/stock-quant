---
description: >-
  Những hàm được phát triển riêng cho FiinQuant giúp người dùng có thể dùng
  ngay, không cần tự phát triển bài toán.
---

# Hàm tính năng

### Hàm Rebalance

Bằng cách nhập giá trị có thể mua và mã index, thuật toán sẽ tính ra số lượng cổ phiếu cần mua để có tỷ lệ giống với tỷ lệ cổ phiếu trong rổ chỉ số index nhất. Ứng dụng trong giao dịch arbitrage, passive investment.

{% hint style="info" %}
Phương pháp luận hàm **Rebalance:**

Hàm **Rebalance** sử dụng dữ liệu công bố của Sở giao dịch chứng khoán về Tỷ lệ FreeFloat, Giới hạn tỷ trọng kết hợp với giá đóng cửa (close price) realtime của hệ thống FiinGroup.

**Tái cơ cấu** được thực hiện theo nguyên tắc tỷ lệ về **Khối lượng không thay đổi trong một danh mục**, do vậy để có thể bám theo (tracking) một chỉ số, người quản trị danh mục chỉ cần xây dựng bộ **danh mục có tỷ lệ về số lượng giữa các cổ phiếu giống với tỷ lệ về chỉ số** cần theo dõi, sẽ đảm bảo đạt được độ lệch (Tracking Error) thấp nhất.

Kết quả trả ra là **"Share to Buy"** dựa trên input đầu vào là **Budget (VND)** và **Ticker (Chỉ số)** cần **Rebalance**.
{% endhint %}

<figure><img src="https://3318188420-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2Fkme4XYjWbuM3iRJzUu9r%2Fuploads%2F8kk3fjlVjiUizlhgEhMa%2Fimage.png?alt=media&#x26;token=b7a46d2c-978f-4329-9d24-c80fc00120e0" alt="" width="375"><figcaption><p>Danh sách vã số lượng cần mua của mỗi mã cổ phiếu</p></figcaption></figure>

Danh sách các Index dùng cho hàm:

* VN30
* VN100
* VNX50
* VNMidcap
* VNFINSELECT
* VNDIAMOND
* VNFINLEAD

```python
from FiinQuantX import FiinSession

username = 'REPLACE_WITH_YOUR_USER_NAME'
password = 'REPLACE_WITH_YOUR_PASS_WORD'                     
                     
client = FiinSession(username=username, password=password).login()
df = client.Rebalance().get(Budget = 10000000000, Ticker = 'VN30')
print(df)
```

<figure><img src="https://3318188420-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2Fkme4XYjWbuM3iRJzUu9r%2Fuploads%2FDu0dn5InSXIxhkAsyraV%2Fimage.png?alt=media&#x26;token=74d54083-bf9f-4c19-be49-0bd27ca33c68" alt=""><figcaption></figcaption></figure>



### Hàm SimilarChart

{% hint style="info" %}
Cho phép người dùng tìm kiếm nhanh trong số lượng lớn mã cổ phiếu 5 mã có xu hướng giá gần nhất với mã cổ phiếu đang quan tâm.&#x20;
{% endhint %}

<figure><img src="https://3318188420-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2Fkme4XYjWbuM3iRJzUu9r%2Fuploads%2FMr2ApuZmHjmBMgtf5Hp0%2Fimage.png?alt=media&#x26;token=cf1a8c66-ba5e-4ecc-9a2f-41bda5fa764d" alt=""><figcaption><p>5 mã cổ phiếu có xu hướng gần nhất với mã ACB hiện tại </p></figcaption></figure>

```python
client.SimilarChart().plot(Ticker=Ticker, t1=t1, t2=t2)
```

**Tham số**

| Tên tham số | Mô tả                          | Kiểu dữ liệu | Giá trị mặc định |
| ----------- | ------------------------------ | ------------ | ---------------- |
| Ticker      | Mã cổ phiếu áp dụng            | Ticker       | Không có         |
| t1          | Thời điểm bắt đầu của cụm nến  | str          |                  |
| t2          | Thời điểm kết thúc của cụm nến | str          |                  |

```python
import pandas as pd
from FiinQuantX import FiinSession
import datetime
from datetime import datetime
from dateutil.relativedelta import relativedelta

username = 'REPLACE_WITH_YOUR_USER_NAME'
password = 'REPLACE_WITH_YOUR_PASS_WORD'

client = FiinSession(
    username=username,
    password=password
).login()

def user_input():
    default_t1 = (datetime.now() - relativedelta(months=1)).strftime("%Y-%m-%d")
    default_t2 = datetime.now().strftime("%Y-%m-%d")
    print("")
    print("Chào mừng đến hệ thống dự báo biểu đồ CHỨNG KHOÁN theo THỜI GIAN THỰC của FIINQUANT")
    print("")
    print("Giải thích cách tìm chart có đường giá tương đồng với đường giá thời điểm hiện tại:")
    print("")
    print("- Tìm kiếm tất cả các pattern nến của tất cả các ngày trong vòng x năm kể từ thời điểm hiện tại")
    print("- Tìm ngày có đường giá giống với ngày hiện tại nhất")
    print("")
    print("Hệ thống sẽ sử dụng các tham số mặc định sau:")
    print(f'- Thời điểm bắt đầu: {default_t1}')
    print(f'- Thời điểm kết thúc (là thời điểm hiện tại): {default_t2}')

    use_default = input("Bạn có muốn sử dụng các tham số mặc định không? (y/n): ").lower() == "y"

    if not use_default:
        t1 = input("Nhập ngày bắt đầu (ví dụ: 2024-05-10): ")
        t2 = input("Nhập thời điểm kết thúc (ví dụ: 2024-05-10): ")
    else:
        t1 = default_t1
        t2 = default_t2
    
    Ticker = input("Vui lòng nhập mã bạn muốn so tìm đường tương quan (ví dụ: VN30, VN30F1M, ACB): ")
    Ticker = Ticker.upper()    
    print("Đang tính toán, vui lòng đợi")
    client.SimilarChart().plot(Ticker=Ticker, t1=t1, t2=t2)

if __name__ == "__main__":
    user_input()
```

<figure><img src="https://3318188420-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2Fkme4XYjWbuM3iRJzUu9r%2Fuploads%2FvGf5mCaOxkI4r2pEJpsw%2Fimage.png?alt=media&#x26;token=9debf5de-ace2-426c-9c21-9009dd7344a8" alt=""><figcaption></figcaption></figure>

### Hàm FindDateCorrelation

{% hint style="info" %}
Sử dụng function này để tìm mối tương quan giữa dữ liệu ngày hôm nay và dữ liệu trong quá khứ cho một mã nhất định.
{% endhint %}

<figure><img src="https://3318188420-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2Fkme4XYjWbuM3iRJzUu9r%2Fuploads%2Funn2psxlKOHZxiPPZFt3%2Fimage.png?alt=media&#x26;token=b9569c87-dbf4-4b47-b9c1-be14e159a7fc" alt=""><figcaption><p>Ví dụ tìm kiếm tương quan cho VN30F1M trong 1 năm dữ liệu so với ngày hiện tại</p></figcaption></figure>

<pre class="language-python"><code class="lang-python">
 def intraday_Correlation(self, Ticker: Union[str, list[str]], Timeframe: str, 
                            t1: str = None, t2: str = None, method: str = "pearson correlation",
<strong>                            year: int = 1) -> None:
</strong></code></pre>

#### Tham số&#x20;

| Tham số     | Kiểu dữ liệu            | Mặc định | Giá trị mặc định        | Mô tả                                                                     |
| ----------- | ----------------------- | -------- | ----------------------- | ------------------------------------------------------------------------- |
| `Ticker`    | `Union[str, list[str]]` | Bắt buộc | Không có                | Mã chứng khoán hoặc danh sách mã chứng khoán cần phân tích.               |
| `Timeframe` | `str`                   | Bắt buộc | 1M                      | Khung thời gian của dữ liệu giao dịch nội ngày (ví dụ: "1m", "5m", "1h"). |
| `t1`        | `str`                   | Tùy chọn | 9am hoặc 13pm           | Thời gian bắt đầu (nếu cần).                                              |
| `t2`        | `str`                   | Tùy chọn | `None`                  | Thời gian kết thúc (nếu cần).                                             |
| `method`    | `str`                   | Tùy chọn | `"pearson correlation"` | Phương pháp đo khoảng cách (1: Euclidean, 2: DTW, 3: Pearson, 4: Cosine). |
| `year`      | `int`                   | Tùy chọn | `1`                     | Số năm dữ liệu quá khứ cần so sánh.                                       |



Copy đoạn code để chạy ví dụ trên&#x20;

```python

import pandas as pd
import datetime

from FiinQuantX import FiinSession
from datetime import datetime

username = 'REPLACE_WITH_YOUR_USER_NAME'
password = 'REPLACE_WITH_YOUR_PASS_WORD'
 
client = FiinSession(
    username=username,
    password=password
).login()

def user_input():
    default_timeframe = '1m'
    default_t1 = "09:00:00" if datetime.now().hour < 12 else "13:00:00"
    default_t2 = datetime.now().replace(microsecond=0).time().strftime("%H:%M:%S")
    default_method = "pearson correlation"
    default_year = 1
    print("")
    print("Chào mừng đến hệ thống dự báo biểu đồ CHỨNG KHOÁN theo THỜI GIAN THỰC của FIINQUANT")
    print("")
    print("Giải thích cách tìm top 5 ngày tương quan:")
    print("")
    print("- Tìm kiếm tất cả các pattern nến của tất cả các ngày trong vòng x năm kể từ thời điểm hiện tại")
    print("- Tìm 5 ngày có độ tương quan với ngày hiện tại nhất dựa trên các phương pháp tùy người chọn: Euclidean Distance, Pearson Correlation (mặc định), cosine")
    print("")
    print("Hệ thống sẽ sử dụng các tham số mặc định sau:")
    print(f"- Khung thời gian: {default_timeframe}")
    print(f"- Thời điểm bắt đầu: {default_t1}")
    print(f"- Thời điểm kết thúc (là thời điểm hiện tại): {default_t2}")
    print(f"- Phương pháp tính tương quan: {default_method}")
    print(f"- Số năm dữ liệu muốn quét kể từ thời điểm hiện tại: {default_year} năm")

    use_default = input("Bạn có muốn sử dụng các tham số mặc định không? (y/n): ").lower() == "y"

    if not use_default:
        timeframe = input("Nhập khung thời gian (ví dụ: 1m, 15m, 30m, 1h mặc định: 1m): ") or default_timeframe
        t1 = input("Nhập thời điểm bắt đầu (ví dụ: 09:00, 10:00, 11:00): ")
        t2 = input("Nhập thời điểm kết thúc (ví dụ: 13:00, 14:00, 15:00): ")
        
        print("Vui lòng lựa chọn phương pháp tính tương quan:")
        print("1. Pearson Correlation (mặc định)")
        print("2. Euclidean Distance")
        print("3. Cosine")
        print("4. Dynamic Time Wrapping")
        method = int(input("Lựa chọn của bạn (1/2/3): ")) or 1
        
        year = int(input("Nhập số năm dữ liệu muốn quét kể từ thời điểm hiện tại: ")) or 1
    else:
        timeframe = default_timeframe
        t1 = default_t1
        t2 = default_t2
        method = default_method
        year = default_year
    
    Ticker = input("Vui lòng nhập mã bạn muốn so tìm đường tương quan (ví dụ: VN30, VN30F1M, ACB): ")
    print("Đang tính toán, vui lòng đợi")
    client.FindDateCorrelation().intraday_Correlation(Ticker=Ticker, Timeframe=timeframe, t1=t1, t2=t2, method=method, year=year)


# Chạy chương trình
if __name__ == "__main__":
    user_input()

```

<figure><img src="https://3318188420-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2Fkme4XYjWbuM3iRJzUu9r%2Fuploads%2FhRFpkyFUMw2GWRsu5KS5%2Fimage.png?alt=media&#x26;token=ee29d075-12bf-4905-b7fd-361f632ef974" alt=""><figcaption><p>Output khi chạy đoạn code trên </p></figcaption></figure>

### Hàm SeasonalityPrice

{% hint style="info" %}
Hàm này dùng để vẽ tương quan thay đổi giá của 1 hay nhiều mã cổ phiếu trong một khoảng thời gian
{% endhint %}

```python
import pandas as pd
import numpy as np
from plotly import graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from FiinQuantX import FiinSession

username = 'REPLACE_WITH_YOUR_USER_NAME'
password = 'REPLACE_WITH_YOUR_PASS_WORD'

client = FiinSession(
    username=username,
    password=password
).login()

class SeasonalityPrice:
    def __init__(self, data, tickers):
        self.data = data
        self.data['timestamp'] = pd.to_datetime(self.data['timestamp'])
        self.tickers = []
        if isinstance(tickers, str):
            self.tickers = [tickers]
        elif isinstance(tickers, list):
            self.tickers = tickers
        else:
            self.tickers = [tickers]

    def monthly_seasonality(self):
        if len(self.tickers) > 1:
            raise ValueError("Only one ticker is supported for monthly seasonality")
        
        filtered_data = self.data.copy()
        filtered_data.set_index('timestamp', inplace=True)

        monthly_returns = filtered_data['close'].resample('M').last().pct_change() * 100
        monthly_seasonality = pd.DataFrame()
        monthly_seasonality['Month'] = monthly_returns.index.month
        monthly_seasonality['Year'] = monthly_returns.index.year
        monthly_seasonality['Returns'] = monthly_returns.values

        return monthly_seasonality
    
    
    def plot_seasonality(self):  
        if len(self.tickers) > 1:
            print("Tickers: ", self.tickers)

            raise ValueError("Only one ticker is supported for monthly seasonality")
        
        monthly_seasonality = self.monthly_seasonality()
        pivot_table = monthly_seasonality.pivot(index='Year', columns='Month', values='Returns').sort_index(ascending=True)
        monthly_averages = pivot_table.mean(axis=0).values.reshape(1, -1)  
        monthly_stdev = pivot_table.std(axis=0).values.reshape(1, -1)
        monthly_avg_plus_stdev = monthly_averages + monthly_stdev
        monthly_avg_minus_stdev = monthly_averages - monthly_stdev
        monthly_Sharpe_ratio = monthly_averages / monthly_stdev
        annotations = []
        for i, row in enumerate(pivot_table.values):
            for j, value in enumerate(row):
                annotations.append(
                    dict(
                        x=['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][j],
                        y=pivot_table.index[i],
                        text=f'{value:.2f}' if not np.isnan(value) else '',
                        showarrow=False,
                        font=dict(color='black' if abs(value) < 10 else 'white')
                    )
                )
        fig = go.Figure()

        fig.add_trace(go.Heatmap(
            z=pivot_table.values,
            x=['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
            y=pivot_table.index,  
            colorscale=[
                [0, 'darkred'],      
                [0.49, '#ff6666'],   
                [0.5, 'white'],      
                [0.51, '#99ff99'],   
                [1, 'darkgreen']     
            ],
            colorbar_title="Returns (%)",
            showscale=False,
            zmin=-20,   
            zmax=20,
        ))

        # Add the averages heatmap
        fig.add_trace(go.Heatmap(
            z=monthly_averages,
            x= ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
            y=['Avgs: '],
            colorscale=[
                [0, 'darkred'],      
                [0.49, '#ff6666'],   
                [0.5, 'white'],      
                [0.51, '#99ff99'],   
                [1, 'darkgreen']     
            ],
            showscale=False,
            showlegend=False,
            text=monthly_averages,
            texttemplate='%{z:.2f}%',
            yaxis='y2',  
            xaxis='x2', 
        ))

        fig.add_trace(go.Heatmap(
            z=monthly_stdev,
            x= ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
            y=['Stdev: '],
            colorscale=[
                [0, 'darkred'],      
                [0.49, '#ff6666'],   
                [0.5, 'white'],      
                [0.51, '#99ff99'],   
                [1, 'darkgreen']     
            ],
            text=monthly_stdev,
            texttemplate='%{z:.2f}%',
            showscale=False,
            showlegend=False,
            yaxis= 'y3',
            xaxis= 'x3',
        ))
        fig.add_trace(go.Heatmap(
            z=monthly_avg_plus_stdev,
            x=['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
            y=['+ 1 stdev: '],
            colorscale=[
                [0, 'darkred'],      
                [0.49, '#ff6666'],   
                [0.5, 'white'],      
                [0.51, '#99ff99'],   
                [1, 'darkgreen']     
            ],
            showscale=False,
            showlegend=False,
            text=monthly_avg_plus_stdev,
            texttemplate='%{z:.2f}%',
            yaxis='y4',
            xaxis='x4',
        ))

        # Add the avg - 1stdev heatmap
        fig.add_trace(go.Heatmap(
            z=monthly_avg_minus_stdev,
            x=['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
            y=[' -1 stdev: '],
            colorscale=[
                [0, 'darkred'],      
                [0.49, '#ff6666'],   
                [0.5, 'white'],      
                [0.51, '#99ff99'],   
                [1, 'darkgreen']     
            ],
            showscale=False,
            showlegend=False,
            text=monthly_avg_minus_stdev,
            texttemplate='%{z:.2f}%',
            yaxis='y5',
            xaxis='x5',
        ))

        fig.update_layout(
            title=f'Monthly Percentage Price Change for {self.tickers} (2018-2024)',
            xaxis=dict(domain=[0, 1], showticklabels=False),
            yaxis=dict(domain=[0.5, 1.0], title='Year', autorange='reversed'),  
            xaxis2=dict(domain=[0, 1], anchor='y2', matches='x', showticklabels=False),
            yaxis2=dict(domain=[0.35,0.45], autorange='reversed'), 
            xaxis3=dict(domain=[0, 1], anchor='y3', matches='x',showticklabels=False),
            yaxis3=dict(domain=[0.24,0.34], autorange='reversed'), 
            yaxis4=dict(domain=[0.13,0.23], autorange='reversed'), 
            xaxis4=dict(domain=[0, 1], anchor='y4', matches='x', showticklabels=False),
            yaxis5=dict(domain=[0.02,0.12], autorange='reversed'), 
            xaxis5=dict(domain=[0, 1], anchor='y5', matches='x', title='Month'),
            annotations=annotations,
        )

        fig.show()

        fig_sharpe = go.Figure()

        sharpe_values = monthly_Sharpe_ratio.flatten()
        colors = ['#ff9999' if x < 0 else '#66b3ff' if x < 1 else '#99ff99' for x in sharpe_values]

        fig_sharpe.add_trace(go.Bar(
            x=['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
            y=sharpe_values,
            marker_color=colors,
            name='Sharpe Ratio'
        ))

        fig_sharpe.update_layout(
            title=f'Monthly Sharpe Ratio for {self.tickers} (2018-2024)',
            xaxis=dict(title='Month'),
            yaxis=dict(title='Sharpe Ratio'),
            plot_bgcolor='white',
            paper_bgcolor='white',
            showlegend=False,
            bargap=0.2
        )

        fig_sharpe.show()


    def plot_average_sharpe(self):
        monthly_sharpe_ratios = {}
        average_sharpe_ratios = {}

        for ticker in self.tickers:
            # Filter data for the current ticker
            ticker_data = self.data[self.data['ticker'] == ticker]
            ticker_data['timestamp'] = pd.to_datetime(ticker_data['timestamp'])
            mask = (ticker_data['timestamp'] >= '2018-01-01') & (ticker_data['timestamp'] <= '2024-11-30')
            filtered_data = ticker_data[mask].copy()

            filtered_data.set_index('timestamp', inplace=True)
            monthly_returns = filtered_data['close'].resample('ME').last().pct_change() * 100

            # Calculate monthly averages and standard deviations
            monthly_averages = monthly_returns.groupby(monthly_returns.index.month).mean()
            monthly_stdev = monthly_returns.groupby(monthly_returns.index.month).std()

            # Calculate Sharpe ratio
            sharpe_ratios = (monthly_averages / monthly_stdev).values
            monthly_sharpe_ratios[ticker] = sharpe_ratios
            average_sharpe_ratios[ticker] = np.nanmean(sharpe_ratios) 

        # Find the ticker with the highest average Sharpe ratio
        highest_avg_sharpe_ticker = max(average_sharpe_ratios, key=average_sharpe_ratios.get)
        highest_avg_sharpe_value = average_sharpe_ratios[highest_avg_sharpe_ticker]

        # Create subplots
        fig = make_subplots(rows=1, cols=2, shared_yaxes=False, horizontal_spacing=0.1,
                            subplot_titles=("Monthly Sharpe Ratios", "Average Sharpe Ratios"))

        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        
        # Plot monthly Sharpe ratios
        for ticker, sharpe_values in monthly_sharpe_ratios.items():
            colors = ['#00FF00' if ticker == highest_avg_sharpe_ticker else '#ff9999' if value < 0 else '#66b3ff' if value < 1 else '#99ff99' for value in sharpe_values]
                    
            fig.add_trace(go.Bar(
                x=months,
                y=sharpe_values,
                marker_color=colors,
                name=f'Sharpe Ratio for {ticker}',
                width=0.15
            ), row=1, col=1)

        # Plot average Sharpe ratios
        avg_sharpe_values = list(average_sharpe_ratios.values())
        avg_colors = ['#00FF00' if ticker == highest_avg_sharpe_ticker else '#66b3ff' for ticker in tickers]
        
        fig.add_trace(go.Bar(
            x=tickers,
            y=avg_sharpe_values,
            marker_color=avg_colors,
            name='Average Sharpe Ratio',
            width=0.4
        ), row=1, col=2)

        # Add annotation for the highest average Sharpe ratio
        fig.add_annotation(
            x=highest_avg_sharpe_ticker, y=highest_avg_sharpe_value,
            text=f"Highest Avg Sharpe: {highest_avg_sharpe_ticker} ({highest_avg_sharpe_value:.2f})",
            showarrow=True,
            arrowhead=1,
            yshift=10,
            font=dict(size=12, color="black"),
            xref="x2", yref="y2"
        )

        fig.update_layout(
            title='Sharpe Ratios for Multiple Tickers (2018-2024)',
            xaxis=dict(title='Month'),
            yaxis=dict(title='Sharpe Ratio'),
            xaxis2=dict(title='Ticker'),
            yaxis2=dict(title='Average Sharpe Ratio', range=[0, max(avg_sharpe_values) * 1.2]),  # Scale y-axis
            plot_bgcolor='white',
            paper_bgcolor='white',
            showlegend=False,
            bargap=0.2
        )

        fig.show()


tickers = ['VCB', 'TPB', 'MBB','VIB','TCB', 'VPB', 'ACB', 'BID','CTG','EIB']

data = client.Fetch_Trading_Data(
    tickers=tickers,
    fields=['close'],
    adjusted=True,
    realtime=False,
    by='1d', 
    from_date='2018-01-01').get_data()
new_SeasonalityPrice = SeasonalityPrice(data, 'VCB')
new_SeasonalityPrice.plot_seasonality()

#Uncomment this to plot average sharpe ratio for multiple tickers
tickers = ['VCB', 'TPB', 'MBB','VIB','TCB', 'VPB', 'ACB', 'BID','CTG','EIB']
# new_SeasonalityPrice = SeasonalityPrice(data, tickers)
# new_SeasonalityPrice.plot_average_sharpe()
```



<figure><img src="https://3318188420-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2Fkme4XYjWbuM3iRJzUu9r%2Fuploads%2F0BiIK5VBr1xuK7Na5wSo%2FScreenshot%202025-02-18%20at%2010.21.14.png?alt=media&#x26;token=8d8b6505-64a2-4b4b-a01b-3dd7c6f8032b" alt=""><figcaption><p>Bảng thay đổi giá theo tháng của VCB</p></figcaption></figure>

<figure><img src="https://3318188420-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2Fkme4XYjWbuM3iRJzUu9r%2Fuploads%2FCrG4kj8dCZ6bX7tXHgv4%2FScreenshot%202025-02-18%20at%2010.22.25.png?alt=media&#x26;token=9a0de6fb-3381-4ed8-9758-7f182dc6fea4" alt=""><figcaption><p>Sharpe Ratio theo tháng </p></figcaption></figure>

### Hàm Theo dõi hủy lệnh

{% hint style="info" %}
Hàm theo dõi hủy lệnh theo nguyên tắc theo dõi giá theo từng bước giá. Xác định khối lượng được thêm hay bớt.
{% endhint %}

<pre class="language-python"><code class="lang-python">from FiinQuantX import FiinSession

username = "REPLACE_WITH_YOUR_USERNAME"
password = "REPLACE_WITH_YOUR_PASSWORD"

client = FiinSession(username=username, password=password).login()

order_book = client.OrderBook()
<strong>
</strong>ticker_config = {
    "VJC": {"min_volume": 100_000},
    "VNM": {"min_volume": 100_000},
    "VPB": {"min_volume": 100_000},
    "VRE": {"min_volume": 100_000}
}

def process_data(data: dict):
    print(data)

# Theo dõi hủy lệnh bất thường
order_book.track_order_book_changes(ticker_config=ticker_config, action="add", accumulate_window=60, callback=process_data)

</code></pre>

| **Tham số**         | **Kiểu dữ liệu** | **Mô tả**                                                                                                 |
| ------------------- | ---------------- | --------------------------------------------------------------------------------------------------------- |
| ticker\_config      | dict             | Từ điển chứa từng mã chứng khoán và ngưỡng khối lượng thay đổi (min\_volume) cần cảnh báo                 |
| side                | str              | 'bid', 'ask' hoặc 'all' – chỉ định hướng theo dõi                                                         |
| action              | str              | 'cancel', 'add' hoặc 'all' – chỉ định loại thay đổi lệnh muốn theo dõi                                    |
| accumulate\_window  | int              | Đơn vị giây. Cho phép user định nghĩa tần suất tính lại để cộng tổng các giá trị hủy lệnh.                |
| min\_action\_volume | int              | Khối lượng cổ phiếu hủy/thêm tối thiểu để được tính là 1 lệnh hủy/thêm. Phục vụ thống kê số lệnh hủy/thêm |

1. Theo dõi bám theo giá cố định:
   * Mỗi mã được theo dõi ở mức giá cụ thể: bid2.price hoặc ask2.price (tùy side) ngay tại thời điểm khởi đầu.
   * Trong quá trình theo dõi, chỉ quan sát khối lượng tại đúng mức giá đó.
2. Ngưng theo dõi khi giá vượt giới hạn số bước giá hiển thị (3 bước/10 bước):
   * Nếu mức giá ban đầu bị đẩy ra khỏi vùng nhìn thấy:
     * Với HOSE: ngoài 3 bước giá tốt nhất (ví dụ: từ _bid1 đến bid3_)
     * Với HNX/UPCoM: ngoài 10 bước giá tốt nhất
   * Hệ thống sẽ ngưng theo dõi ticker đó, nhằm tránh bị nhiễu (noise) do sự thay đổi không thực chất.
3. Xử lý giá bid1 / ask1:
   * Giá bid1 / ask1 sẽ được trừ khối lượng đã khớp để tránh nhầm lẫn là hủy lệnh, khi thực tế là do khớp lệnh.
4. Tính OTR:

$$
OTR = \frac{Số lượng lệnh (đặt, sửa, hủy)}{Số lượng giao dịch thực hiện}
$$

Kết quả:

<figure><img src="https://3318188420-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2Fkme4XYjWbuM3iRJzUu9r%2Fuploads%2FPGk3PjvyioAQ5tfdSE4W%2Fimage.png?alt=media&#x26;token=bca9e108-9ccf-4320-a893-beb170f01580" alt=""><figcaption></figcaption></figure>

***

#### Ứng dụng thực tế:

* Phát hiện các dấu hiệu thao túng lệnh như đẩy giả lệnh mua/bán rồi hủy ngay sau đó.
* Phát hiện đột biến lượng lệnh đặt mới bất thường tại các vùng nhạy cảm.
* Phân tích hành vi nhà đầu tư/cá mập trong thời gian thực.

