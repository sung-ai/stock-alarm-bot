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
            
            # --- 종목별 맞춤 3단계 분할 매수 조건 설정 ---
            if ticker == "QLD":
                criteria_tiers = [
                    {"name": "1차 매수", "disp": -10.0, "rsi": 48.0},
                    {"name": "2차 매수", "disp": -18.0, "rsi": 42.0},
                    {"name": "3차 매수", "disp": -26.0, "rsi": 36.0},
                ]
            elif ticker == "TQQQ":
                criteria_tiers = [
                    {"name": "1차 매수", "disp": -18.0, "rsi": 43.0},
                    {"name": "2차 매수", "disp": -32.0, "rsi": 36.0},
                    {"name": "3차 매수", "disp": -45.0, "rsi": 31.0},
                ]
            elif ticker == "SOXL":
                criteria_tiers = [
                    {"name": "1차 매수", "disp": -18.0, "rsi": 43.0},
                    {"name": "2차 매수", "disp": -32.0, "rsi": 36.0},
                    {"name": "3차 매수", "disp": -45.0, "rsi": 31.0},
                ]

            st.markdown(f"### 🎯 [{ticker}] 분할 매수 조건 판정 (OR 조건)")
            st.caption("각 단계별로 '괴리율 기준' 또는 '주봉 RSI 기준' 중 무엇으로 충족되었는지 상세히 표시됩니다.")
            
            met_count = 0
            for tier in criteria_tiers:
                is_disp_met = disparity <= tier["disp"]
                is_rsi_met = current_rsi <= tier["rsi"]
                
                # 어떤 조건으로 충족되었는지 상세 분기 처리
                if is_disp_met and is_rsi_met:
                    met_count += 1
                    status_str = "🟢 **[충족]** (괴리율 & RSI 모두 충족)"
                elif is_disp_met:
                    met_count += 1
                    status_str = "🟢 **[충족]** (괴리율 조건 충족)"
                elif is_rsi_met:
                    met_count += 1
                    status_str = "🟢 **[충족]** (주봉 RSI 조건 충족)"
                else:
                    status_str = "⚪ (미달)"
                
                st.markdown(
                    f"- **{tier['name']}** (목표 괴리율 `{tier['disp']}%` 이하 / 목표 RSI `{tier['rsi']}` 이하) "
                    f"-> {status_str}"
                )
            
            # 종합 판정 결과
            if met_count > 0:
                st.success(f"🔥 **[{ticker}] 총 {met_count}개 단계의 매수 조건이 충족되었습니다!** 적극적인 분할 매수를 고려해보세요.")
            else:
                st.info(f"⏳ **[{ticker}] 관망 중** (현재 설정된 어떤 분할 매수 조건에도 도달하지 않았습니다.)")
            
            st.markdown("---")
            st.markdown("### 📊 최근 주가 및 200일선 추세")
            # 최근 1년 차트 데이터 추출
            chart_df = df_daily[['Close', 'MA200']].tail(250)
            st.line_chart(chart_df)

# 사이드바 정보
st.sidebar.header("ℹ️ 설정 정보")
st.sidebar.info(
    "이 대시보드는 Streamlit Cloud와 yfinance를 활용해 실시간으로 지표를 계산합니다.\n\n"
    "버전: v1.3 (매수 충족 사유 상세 표시 기능 추가)"
)
