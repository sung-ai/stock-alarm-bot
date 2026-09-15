import streamlit as st
import pandas as pd
import yfinance as yf
import datetime
import plotly.graph_objects as go

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

# 데이터 분석 함수 (종목 데이터)
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

# VIX(공포지수) 가져오기 함수
@st.cache_data(ttl=3600)
def get_vix_data():
    vix_df = yf.download("^VIX", period="5d", interval="1d", progress=False)
    if isinstance(vix_df.columns, pd.MultiIndex):
        vix_df.columns = vix_df.columns.get_level_values(0)
    current_vix = vix_df.iloc[-1]['Close']
    prev_vix = vix_df.iloc[-2]['Close']
    vix_change = current_vix - prev_vix
    return current_vix, vix_change

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
            st.caption("각 단계별 목표치와 현재 수치의 차이를 함께 표시합니다.")
            
            met_count = 0
            for tier in criteria_tiers:
                is_disp_met = disparity <= tier["disp"]
                is_rsi_met = current_rsi <= tier["rsi"]
                
                disp_gap = disparity - tier["disp"]
                rsi_gap = current_rsi - tier["rsi"]
                
                if is_disp_met and is_rsi_met:
                    met_count += 1
                    status_str = "🟢 **[충족]** (괴리율 & RSI 모두 충족)"
                elif is_disp_met:
                    met_count += 1
                    status_str = f"🟢 **[충족]** (괴리율 충족 / RSI는 기준 초과 +{rsi_gap:.1f})"
                elif is_rsi_met:
                    met_count += 1
                    status_str = f"🟢 **[충족]** (RSI 충족 / 괴리율은 기준 초과 +{disp_gap:.1f}%)"
                else:
                    status_str = f"⚪ (미달: 괴리율 {disp_gap:+.1f}%p, RSI {rsi_gap:+.1f})"
                
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
            chart_df = df_daily[['Close', 'MA200']].tail(250)
            st.line_chart(chart_df)

# --- 대시보드 하단 시장 공포지수(VIX 기반 게이지 차트) 섹션 ---
st.markdown("---")
st.markdown("### 🌪️ 시장 심리 및 공포지수")

try:
    current_vix, vix_change = get_vix_data()
    
    # VIX를 0~100 스케일의 공포지수 점수로 대략적으로 변환 (VIX 10=극단탐욕(0), 20=보통(50), 40이상=극단공포(100))
    # 보통 VIX 15~20 사이가 중립이므로 이에 맞춰 매핑
    fng_approx = min(max(int((current_vix - 10) * 3.33), 0), 100)
    
    col_gauge, col_text = st.columns([1.2, 1])
    
    with col_gauge:
        # Plotly를 이용해 CNN 스타일의 반원 게이지 차트 직접 구현
        fig = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = fng_approx,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "Market Fear & Greed (VIX 환산)", 'font': {'size': 18}},
            number = {'font': {'size': 36}},
            gauge = {
                'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
                'bar': {'color': "rgba(0,0,0,0)"}, # 바늘 역할 대신 기본 바 숨김
                'bgcolor': "white",
                'borderwidth': 2,
                'bordercolor': "gray",
                'steps': [
                    {'range': [0, 25], 'color': '#ff4d4d'},   # 극단적 공포 (빨강)
                    {'range': [25, 45], 'color': '#ff9966'},  # 공포 (주황)
                    {'range': [45, 55], 'color': '#e6e6e6'},  # 중립 (회색)
                    {'range': [55, 75], 'color': '#99ccff'},  # 탐욕 (연파랑)
                    {'range': [75, 100], 'color': '#3399ff'}  # 극단적 탐욕 (파랑)
                ],
                'threshold': {
                    'line': {'color': "black", 'width': 4},
                    'thickness': 0.75,
                    'value': fng_approx
                }
            }
        ))
        fig.update_layout(height=250, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig, use_container_width=True)

    with col_text:
        st.markdown("#### VIX 변동성 공포지수 상세")
        st.metric(label="VIX Index", value=f"{current_vix:.2f}", delta=f"{vix_change:+.2f}")
        
        if current_vix < 15:
            st.info("😎 **시장 분위기: 탐욕 / 안정적** (변동성이 낮고 시장이 평온합니다.)")
        elif 15 <= current_vix < 20:
            st.success("🙂 **시장 분위기: 보통 / 완만함** (일반적인 변동성 구간입니다.)")
        elif 20 <= current_vix < 30:
            st.warning("⚠️ **시장 분위기: 공포 / 변동성 확대** (시장 불안감이 커지고 있습니다. 분할 매수 타점을 주시하세요!)")
        else:
            st.error("🚨 **시장 분위기: 극단적 공포 / 패닉** (급락장 또는 위기 상황입니다. 공격적인 분할 매수 기회일 수 있습니다!)")
            
except Exception as e:
    st.warning("시장 심리 데이터를 불러오는 중 오류가 발생했습니다.")

# 사이드바 정보
st.sidebar.header("ℹ️ 설정 정보")
st.sidebar.info(
    "이 대시보드는 Streamlit Cloud와 yfinance를 활용해 실시간으로 지표를 계산합니다.\n\n"
    "버전: v1.7 (Plotly 기반 커스텀 게이지 차트 적용)"
)
