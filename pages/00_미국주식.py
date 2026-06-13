import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, timedelta

# 1. 날짜 설정 (최근 1년)
end_date = datetime.today()
start_date = end_date - timedelta(days=365)

# 2. 야후 파이낸스에서 테슬라(TSLA)와 애플(AAPL) 데이터 다운로드
tickers = ["TSLA", "AAPL"]
data = yf.download(tickers, start=start_date, end=end_date)

# 최신 yfinance 버전의 데이터 구조 대응 (Close 가격 추출)
if 'Close' in data.columns:
    close_data = data['Close']
else:
    close_data = data

# 3. Plotly를 이용한 그래프 그리기
fig = go.Figure()

# 테슬라 선 그래프 추가
fig.add_trace(go.Scatter(
    x=close_data.index, 
    y=close_data['TSLA'], 
    mode='lines', 
    name='Tesla (TSLA)',
    line=dict(width=2.5)
))

# 애플 선 그래프 추가
fig.add_trace(go.Scatter(
    x=close_data.index, 
    y=close_data['AAPL'], 
    mode='lines', 
    name='Apple (AAPL)',
    line=dict(width=2.5)
))

# 4. 레이아웃 및 디자인 꾸미기
fig.update_layout(
    title='🚀 테슬라 vs 애플 최근 1년 주가 변동 추이',
    xaxis_title='날짜',
    yaxis_title='주가 (USD $)',
    template='plotly_white',       # 깔끔한 흰색 배경 테마
    hovermode='x unified',         # 마우스를 올리면 같은 날짜의 두 주가를 동시에 표시
    legend=dict(
        orientation="h",           # 범례를 가로로 정렬
        yanchor="bottom", 
        y=1.02, 
        xanchor="right", 
        x=1
    )
)

# 5. 그래프를 브라우저에 표시
fig.show()
