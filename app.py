import streamlit as st
import pandas as pd
import yfinance as yf
import datetime

# 페이지 기본 설정
st.set_page_config(
    page_title="주식 기술적 지표 모니터링 대시보드",
    page_icon="📈",
    layout="wide"
)

st.title("📈 QLD · TQQQ · SOXL 실시간 모니터링 대시보드")
st.markdown("깃허브 클라우드 기반으로 동작하는 나만의 투자 지표 대시보드입니다.")
st.markdown("---")

# RSI 계산 함수
def calculate_rsi(data, window=14):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

# 데이터 분석 함수
@st.cache_data(ttl=3600) # 1시간 동안 데이터 캐싱 (속도 향상)
def get_stock_data(ticker):
    # 일봉 데이터 (200일선 계산용)
    df_daily = yf.download(ticker, period="2y", interval="1d", progress=False)
    if isinstance(df_daily.columns, pd.MultiIndex):
        df_daily.columns = df_daily.columns.get_level_values(0)
    df_daily['MA200'] = df_daily['Close'].rolling(window=200).mean()
    
    # 주봉 데이터 (RSI 계산용)
    df_weekly = yf.download(ticker, period="3y", interval="1wk", progress=False)
    if isinstance(df_weekly.columns, pd.MultiIndex):
        df_weekly.columns = df_weekly.columns.get_level_values(0)
    df_weekly['RSI'] = calculate_rsi(df_weekly['Close'], window=14)
    
    return df_daily, df_weekly

# 종목 리스트
tickers = ["QLD", "TQQQ", "SOXL"]

# 탭으로 종목 구분
tabs = st.tabs(tickers)

for i, ticker in enumerate(tickers):
    with tabs[i]:
        st.subheader(f"{ticker} 상세 지표 분석")
        
        with st.spinner(f"{ticker} 데이터를 불러오는 중..."):
            df_daily, df_weekly = get_stock_data(ticker)
            
            if df_daily.empty or df_weekly.empty:
                st.error("데이터를 불러오지 못했습니다.")
                continue
                
            current_price = df_daily.iloc[-1]['Close']
            ma200 = df_daily.iloc[-1]['MA200']
            disparity = ((current_price - ma200) / ma200) * 100
            current_rsi = df_weekly.iloc[-1]['RSI']
            
            # 메인 지표 3분할 카드
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(label="현재가 (USD)", value=f"${current_price:.2f}")
            with col2:
                st.metric(label="200일선 괴리율", value=f"{disparity:.2f}%", delta=f"MA200: ${ma200:.2f}")
            with col3:
                st.metric(label="주봉 RSI (14)", value=f"{current_rsi:.2f}")
                
            st.markdown("---")
            
            # 매수 조건 명시 및 판정 섹션
            st.markdown("### 🎯 매수 조건 판정 및 기준")
            
            # 기준 정의 (원하시는 숫자로 나중에 수정 가능합니다)
            disparity_criteria = -5.0  # 200일선 괴리율 -5% 이하
            rsi_criteria = 35.0       # 주봉 RSI 35 이하
            
            # 조건 만족 여부 체크
            is_disparity_met = disparity <= disparity_criteria
            is_rsi_met = current_rsi <= rsi_criteria
            
            # 화면에 조건 안내 표기
            st.markdown(
                f"- **기준 1 (괴리율)**: 200일선 괴리율 **{disparity_criteria}% 이하** (현재: `{disparity:.2f}%`) "
                f"{'🟢 **[충족]**' if is_disparity_met else '⚪ (미달)'}"
            )
            st.markdown(
                f"- **기준 2 (주봉 RSI)**: RSI **{rsi_criteria} 이하** (현재: `{current_rsi:.2f}`) "
                f"{'🟢 **[충족]**' if is_rsi_met else '⚪ (미달)'}"
            )
            
            # 종합 판정 박스
            if is_disparity_met or is_rsi_met:
                st.success(f"🔥 **[{ticker}] 매수 조건 충족!** 분할 매수 타이밍을 적극적으로 고려해 보세요.")
            else:
                st.info(f"⏳ **[{ticker}] 관망 중** (설정된 매수 기준에 아직 도달하지 않았습니다.)")
            
            st.markdown("---")
            st.markdown("### 📊 최근 주가 및 200일선 추세")
            # 최근 1년 차트 데이터 추출
            chart_df = df_daily[['Close', 'MA200']].tail(250)
            st.line_chart(chart_df)

# 사이드바 정보
st.sidebar.header("ℹ️ 설정 정보")
st.sidebar.info(
    "이 대시보드는 Streamlit Cloud와 yfinance를 활용해 실시간으로 지표를 계산합니다.\n\n"
    "버전: v1.1 (매수 조건 판정 추가)"
)
