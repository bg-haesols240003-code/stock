import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# 페이지 설정
st.set_page_config(page_title="주가 분석 대시보드", layout="wide")

st.title("📈 글로벌 IT 기업 최근 1년 주가 변동 분석")
st.markdown("삼성전자, SK하이닉스, 구글, MS, 애플의 최근 1년 주가 추이를 비교하고 분석합니다.")

# 티커 심볼 설정 (한국 주식은 .KS, 미국 주식은 그대로)
tickers = {
    "삼성전자": "005930.KS",
    "SK하이닉스": "000660.KS",
    "구글 (Alphabet)": "GOOGL",
    "마이크로소프트 (MS)": "MSFT",
    "애플 (Apple)": "AAPL"
}

# 날짜 설정 (최근 1년)
end_date = datetime.today()
start_date = end_date - timedelta(days=365)

# 데이터 수집 (캐싱을 통해 속도 향상)
@st.cache_data
def load_data(ticker_dict, start, end):
    df_list = []
    for name, ticker in ticker_dict.items():
        data = yf.download(ticker, start=start, end=end)
        if not data.empty:
            # 종가(Close) 기준 데이터 추출 및 재색인
            close_data = data['Close'].copy()
            close_data.name = name
            df_list.append(close_data)
    
    # 하나의 데이터프레임으로 병합
    full_df = pd.concat(df_list, axis=1)
    # 날짜 포맷 정리 (timezone 제거)
    full_df.index = full_df.index.date
    return full_df

with st.spinner("주식 데이터를 불러오는 중입니다..."):
    df = load_data(tickers, start_date, end_date)

# ----------------- UI 및 그래프 구현 -----------------

# 사이드바: 기업 선택 및 분석 방식
st.sidebar.header("⚙️ 설정")
selected_companies = st.sidebar.multiselect(
    "분석할 기업을 선택하세요",
    options=list(tickers.keys()),
    default=list(tickers.keys())
)

analysis_type = st.sidebar.radio(
    "그래프 표시 방식",
    ["실제 주가 (원화/달러 각각)", "누적 수익률 (%)"]
)

if not selected_companies:
    st.warning("조회할 기업을 최소 하나 이상 선택해 주세요.")
else:
    # 1. 실제 주가 그래프 (단위가 달라 두 개의 Y축 사용 혹은 분리 추천하나, 직관성을 위해 누적수익률과 함께 제공)
    if analysis_type == "실제 주가 (원화/달러 각각)":
        fig = go.Figure()
        
        # 한국 주식과 미국 주식의 단위 차이로 인해 이중 Y축 적용
        fig.set_subplots(specs=[[{"secondary_y": True}]])
        
        for company in selected_companies:
            is_krx = "삼성" in company or "하이닉스" in company
            
            fig.add_trace(
                go.Scatter(
                    x=df.index, 
                    y=df[company], 
                    name=f"{company} ({'₩' if is_krx else '$'})",
                    mode='lines'
                ),
                secondary_y=is_krx
            )
            
        fig.update_layout(
            title_text="최근 1년 주가 추이 (한국 기업-우측 Y축 / 미국 기업-좌측 Y축)",
            hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        fig.update_yaxes(title_text="미국 기업 주가 ($)", secondary_y=False)
        fig.update_yaxes(title_text="한국 기업 주가 (₩)", secondary_y=True)
        
    # 2. 누적 수익률 그래프 (기준점을 0%로 맞추어 직접 비교 가능)
    else:
        fig = go.Figure()
        
        for company in selected_companies:
            # 첫 거래일 가격 기준 누적 수익률 계산
            first_price = df[company].dropna().iloc[0]
            returns = ((df[company] - first_price) / first_price) * 100
            
            fig.add_trace(
                go.Scatter(x=df.index, y=returns, name=company, mode='lines')
            )
            
        fig.update_layout(
            title_text="최근 1년 누적 수익률 비교 (%)",
            xaxis_title="날짜",
            yaxis_title="수익률 (%)",
            hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )

    # 그래프 출력
    st.plotly_chart(fig, use_container_width=True)

    # ----------------- 간단한 데이터 통계량 요약 -----------------
    st.subheader("📊 주요 통계 요약")
    
    summary_data = []
    for company in selected_companies:
        comp_data = df[company].dropna()
        if not comp_data.empty:
            first_p = comp_data.iloc[0]
            last_p = comp_data.iloc[-1]
            total_return = ((last_p - first_p) / first_p) * 100
            currency = "₩" if "삼성" in company or "하이닉스" in company else "$"
            
            summary_data.append({
                "기업명": company,
                "1년 전 주가": f"{currency} {first_p:,.0f}" if currency=="₩" else f"{currency} {first_p:,.2f}",
                "현재 주가": f"{currency} {last_p:,.0f}" if currency=="₩" else f"{currency} {last_p:,.2f}",
                "최고가": f"{currency} {comp_data.max():,.0f}" if currency=="₩" else f"{currency} {comp_data.max():,.2f}",
                "최저가": f"{currency} {comp_data.min():,.0f}" if currency=="₩" else f"{currency} {comp_data.min():,.2f}",
                "최근 1년 수익률": f"{total_return:+.2f}%"
            })
            
    summary_df = pd.DataFrame(summary_data)
    st.dataframe(summary_df.set_index("기업명"), use_container_width=True)
