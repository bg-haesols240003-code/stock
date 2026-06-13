import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# 페이지 설정
st.set_page_config(page_title="Global Tech Stock Dashboard", layout="wide", page_icon="⚡")

# 스타일링 CSS
st.markdown("""
    <style>
    .main-title { font-size: 2.5rem; font-weight: 800; color: #1E293B; margin-bottom: 0.5rem; }
    .sub-title { font-size: 1.1rem; color: #64748B; margin-bottom: 2rem; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">⚡ 글로벌 테크 기업 주가 분석 대시보드</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">테슬라, 삼성전자, SK하이닉스, 구글, MS, 애플의 최근 1년 주가 추이를 비교합니다.</div>', unsafe_allow_html=True)

# 분석할 티커 목록
tickers = {
    "테슬라 (Tesla)": "TSLA",
    "삼성전자": "005930.KS",
    "SK하이닉스": "000660.KS",
    "구글 (Alphabet)": "GOOGL",
    "마이크로소프트 (MS)": "MSFT",
    "애플 (Apple)": "AAPL"
}

# 최근 1년 날짜 계산
end_date = datetime.today()
start_date = end_date - timedelta(days=365)

# 데이터 캐싱 처리
@st.cache_data
def load_stock_data(ticker_dict, start, end):
    df_list = []
    for name, ticker in ticker_dict.items():
        try:
            data = yf.download(ticker, start=start, end=end)
            if not data.empty:
                if isinstance(data.columns, pd.MultiIndex):
                    close_data = data['Close'][ticker].copy()
                else:
                    close_data = data['Close'].copy()
                
                close_series = pd.Series(close_data.values.flatten(), index=close_data.index, name=name)
                df_list.append(close_series)
        except Exception as e:
            continue
            
    if not df_list:
        return pd.DataFrame()
        
    full_df = pd.concat(df_list, axis=1).sort_index()
    full_df.index = pd.to_datetime(full_df.index).date
    return full_df

with st.spinner("최신 시장 데이터를 동기화하는 중..."):
    df = load_stock_data(tickers, start_date, end_date)

# ----------------- 사이드바 설정 -----------------
st.sidebar.header("⚙️ 대시보드 컨트롤 필터")

available_companies = []
for comp in tickers.keys():
    if comp in df.columns:
        available_companies.append(comp)

if df.empty or not available_companies:
    st.error("⚠️ 데이터를 불러오지 못했습니다. 잠시 후 다시 시도하거나 앱을 Reboot 해주세요.")
else:
    # 💡 multiselect와 radio 함수의 인자 지정 및 괄호 닫기를 한 줄씩 명확하게 정돈했습니다.
    selected_companies = st.sidebar.multiselect(
        label="시각화할 기업 선택",
        options=available_companies,
        default=available_companies
    )

    analysis_type = st.sidebar.radio(
        label="차트 스타일 선택",
        options=["상대 플랫 비교 (누적 수익률 %)", "원시 데이터 추이 (원화/달러 구분)"]
    )

    # ----------------- 상단 핵심 메트릭 -----------------
    if selected_companies:
        st.markdown("### 📌 기업별 최근 요약")
        
        valid_companies = []
        for comp in selected_companies:
            if comp in df.columns:
                valid_companies.append(comp)
        
        if valid_companies:
            cols = st.columns(len(valid_companies))
            for i, company in enumerate(valid_companies):
                comp_data = df[company].dropna()
                if len(comp_data) >= 2:
                    current_price = float(comp_data.iloc[-1])
                    prev_price = float(comp_data.iloc[-2])
                    delta_price = current_price - prev_price
                    delta_percent = (delta_price / prev_price) * 100
                    
                    currency = "₩" if ("삼성" in company or "하이닉스" in company) else "$"
                    display_value = f"{currency} {current_price:,.0f}" if currency == "₩" else f"{currency} {current_price:,.2f}"
                    
                    with cols[i]:
                        st.metric(
                            label=company,
                            value=display_value,
                            delta=f"{delta_percent:+.2f}% (전일 대비)"
                        )
        st.markdown("---")

        # ----------------- 인터랙티브 Plotly 차트 -----------------
        if analysis_type == "상대 플랫 비교 (누적 수익률 %)":
            fig = go.Figure()
            for company in valid_companies:
                comp_data = df[company].dropna()
                if not comp_data.empty:
                    first_price = float(comp_data.iloc[0])
                    returns = ((comp_data - first_price) / first_price) * 100
                    fig.add_trace(go.Scatter(x=comp_data.index, y=returns, name=company, mode='lines', line=dict(width=2.5)))
                
            fig.update_layout(
                title="🎯 최근 1년 누적 수익률 비교 (동일 기준점 %)",
                xaxis_title="날짜",
                yaxis_title="수익률 (%)",
                hovermode="x unified",
                template="plotly_white",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
        else:
            fig = go.Figure()
            fig.set_subplots(specs=[[{"secondary_y": True}]])
            
            has_krx = any("삼성" in c or "하이닉스" in c for c in valid_companies)
            has_us = any("삼성" not in c and "하이닉스" not in c for c in valid_companies)
            
            for company in valid_companies:
                comp_data = df[company].dropna()
                if not comp_data.empty:
                    is_krx = "삼성" in company or "하이닉스" in company
                    fig.add_trace(
                        go.Scatter(x=comp_data.index, y=comp_data, name=company, mode='lines', line=dict(width=2.5)),
                        secondary_y=is_krx
                    )
                
            fig.update_layout(
                title="📊 실제 주가 추이 (이중 축 적용)",
                hovermode="x unified",
                template="plotly_white",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            if has_us:
                fig.update_yaxes(title_text="미국 기업 주가 ($)", secondary_y=False)
            if has_krx:
                fig.update_yaxes(title_text="한국 기업 주가 (₩)", secondary_y=True)

        st.plotly_chart(fig, use_container_width=True)

        # ----------------- 데이터 테이블 상세 분석 -----------------
        st.markdown("### 📋 상세 스탯 리포트")
        
        summary_data = []
        for company in valid_companies:
            comp_data = df[company].dropna()
            if not comp_data.empty:
                first_p = float(comp_data.iloc[0])
                last_p = float(comp_data.iloc[-1])
                total_return = ((last_p - first_p) / first_p) * 100
                currency = "₩" if "삼성" in company or "하이닉스" in company else "$"
                
                summary_data.append({
                    "기업명": company,
                    "1년 전 가격": f"{currency} {first_p:,.0f}" if currency=="₩" else f"{currency} {first_p:,.2f}",
                    "현재 가격": f"{currency} {last_p:,.0f}" if currency=="₩" else f"{currency} {last_p:,.2f}",
                    "52주 최고가": f"{currency} {comp_data.max():,.0f}" if currency=="₩" else f"{currency} {comp_data.max():,.2f}",
                    "52주 최저가": f"{currency} {comp_data.min():,.0f}" if currency=="₩" else f"{currency} {comp_data.min():,.2f}",
                    "연간 총수익률": f"{total_return:+.2f}%"
                })
                
        if summary_data:
            summary_df = pd.DataFrame(summary_data)
            st.dataframe(summary_df.set_index("기업명"), use_container_width=True)
