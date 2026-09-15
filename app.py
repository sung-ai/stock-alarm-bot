import streamlit as st
import pandas as pd
import yfinance as yf
import datetime
import plotly.express as px

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


# ==========================================
# 1. 시장 심리 및 공포지수 기준 안내 섹션 (최상단)
# ==========================================
st.markdown("### 🌪️ [먼저 확인] 시장 심리 및 공포지수 기준 안내")

try:
    current_vix, vix_change = get_vix_data()
    fng_approx = min(max(int((current_vix - 10) * 3.33), 0), 100)
    
    col_info, col_status = st.columns(2)
    
    with col_info:
        st.markdown("#### 📐 CNN 공포탐욕 지수 기준표 (0 ~ 100)")
        st.markdown(
            """
            * **0 ~ 24 (🔴 극단적 공포 - Extreme Fear):** 시장 패닉 상태. 역사적 바닥권일 확률이 높아 공격적 매수 기회.
            * **25 ~ 44 (🟠 공포 - Fear):** 투자 심리 위축. 분할 매수를 시작하기 좋은 구간.
            * **45 ~ 55 (⚪ 중립 - Neutral):** 시장 방향성이 뚜렷하지 않은 관망 구간.
            * **56 ~ 75 (🔵 탐욕 - Greed):** 상승 기대감 확산, 서서히 주의가 필요한 구간.
            * **76 ~ 100 (🟢 극단적 탐욕 - Extreme Greed):** 과열 구간. 차익 실현 및 현금 확보를 고려해야 할 시기.
            """
        )

    with col_status:
        st.markdown("#### 📊 현재 시장 심리 상태 판정")
        st.metric(label="VIX Index (참고용 변동성)", value=f"{current_vix:.2f}", delta=f"{vix_change:+.2f}")
        st.metric(label="환산 공포탐욕 점수 (대략적)", value=f"{fng_approx}점 / 100점")
        
        # 구간별 메시지 출력
        if fng_approx <= 24:
            st.error("🚨 현재 상태: **극단적 공포 (Extreme Fear)** - 적극적인 분할 매수 타점입니다!")
        elif fng_approx <= 44:
            st.warning("⚠️ 현재 상태: **공포 (Fear)** - 시장 심리가 위축되어 분할 매수를 고려할 시기입니다.")
        elif fng_approx <= 55:
            st.info("ℹ️ 현재 상태: **중립 (Neutral)** - 시장이 평온하며 관망하는 구간입니다.")
        elif fng_approx <= 75:
            st.success("🙂 현재 상태: **탐욕 (Greed)** - 상승 추세이나 과열을 주시해야 합니다.")
        else:
            st.markdown("🔥 현재 상태: **극단적 탐욕 (Extreme Greed)** - 시장 과열! 리스크 관리가 필요합니다.")

except Exception as e:
    st.warning("시장 심리 데이터를 불러오는 중 오류가 발생했습니다.")

st.markdown("---")


# ==========================================
# 2. 내 포트폴리오 비중 및 수익률 사각형 맵 (트리맵)
# ==========================================
st.markdown("### 🗂️ 내 포트폴리오 비중 & 수익률 맵")
st.caption("사이드바(또는 아래 설정)에서 각 종목별 보유 금액(투자금)을 입력하면 박스 크기가 비중에 맞게 자동으로 조절됩니다.")

# 사이드바에서 보유 금액 설정 기능 추가
st.sidebar.header("💰 내 포트폴리오 설정")
qld_amount = st.sidebar.number_input("QLD 보유 금액 ($)", min_value=0.0, value=3000.0, step=500.0)
tqqq_amount = st.sidebar.number_input("TQQQ 보유 금액 ($)", min_value=0.0, value=5000.0, step=500.0)
soxl_amount = st.sidebar.number_input("SOXL 보유 금액 ($)", min_value=0.0, value=2000.0, step=500.0)

with st.spinner("포트폴리오 비중 데이터를 계산하는 중..."):
    # 실시간 가격 조회를 위한 임시 데이터 수집
    q_data, _ = get_stock_data("QLD")
    t_data, _ = get_stock_data("TQQQ")
    s_data, _ = get_stock_data("SOXL")
    
    qld_price = q_data.iloc[-1]['Close']
    tqqq_price = t_data.iloc[-1]['Close']
    soxl_price = s_data.iloc[-1]['Close']
    
    # 임의의 평단가 대비 오늘 수익률 가상 계산 (실제 평단가가 없으므로 최근 20일 전 가격 대비로 예시 구현)
    qld_ret = ((qld_price - q_data.iloc[-20]['Close']) / q_data.iloc[-20]['Close']) * 100
    tqqq_ret = ((tqqq_price - t_data.iloc[-20]['Close']) / t_data.iloc[-20]['Close']) * 100
    soxl_ret = ((soxl_price - s_data.iloc[-20]['Close']) / s_data.iloc[-20]['Close']) * 100

    portfolio_data = pd.DataFrame({
        "Ticker": ["QLD", "TQQQ", "SOXL"],
        "Amount": [qld_amount, tqqq_amount, soxl_amount],
        "Return": [qld_ret, tqqq_ret, soxl_ret],
        "Category": ["나스닥 레버리지", "나스닥 3배", "반도체 3배"]
    })
    
    # 트리맵(사각형 박스 맵) 생성
    fig_tree = px.treemap(
        portfolio_data,
        path=['Category', 'Ticker'],
        values='Amount',
        color='Return',
        color_continuous_scale='RdYlGn', # 빨강(손실) -> 노랑 -> 초록(수익)
        color_continuous_midpoint=0,
        range_color=[-15, 15]
    )
    fig_tree.update_layout(height=300, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig_tree, use_container_width=True)

st.markdown("---")


# ==========================================
# 3. 종목별 상세 지표 분석 (QLD, TQQQ, SOXL)
# ==========================================
tickers = ["QLD", "TQQQ", "SOXL"]
tabs = st.tabs(tickers)

for i, ticker in enumerate(tickers):
    with tabs[i]:
        st.subheader(f"{ticker} 상세 지표 분석")
        
        with st.spinner(f"{ticker} 데이터를 불러오는 중..."):
            if ticker == "QLD":
                df_daily, df_weekly = q_data, get_stock_data("QLD")[1]
                current_price = qld_price
                disparity = ((current_price - df_daily.iloc[-1]['MA200']) / df_daily.iloc[-1]['MA200']) * 100
                current_rsi = df_weekly.iloc[-1]['RSI']
            elif ticker == "TQQQ":
                df_daily, df_weekly = t_data, get_stock_data("TQQQ")[1]
                current_price = tqqq_price
                disparity = ((current_price - df_daily.iloc[-1]['MA200']) / df_daily.iloc[-1]['MA200']) * 100
                current_rsi = df_weekly.iloc[-1]['RSI']
            else:
                df_daily, df_weekly = s_data, get_stock_data("SOXL")[1]
                current_price = soxl_price
                disparity = ((current_price - df_daily.iloc[-1]['MA200']) / df_daily.iloc[-1]['MA200']) * 100
                current_rsi = df_weekly.iloc[-1]['RSI']
                
            ma200 = df_daily.iloc[-1]['MA200']
            
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

# 사이드바 정보
st.sidebar.markdown("---")
st.sidebar.header("ℹ️ 설정 정보")
st.sidebar.info(
    "이 대시보드는 Streamlit Cloud와 yfinance를 활용해 실시간으로 지표를 계산합니다.\n\n"
    "버전: v2.0 (포트폴리오 비중 트리맵 추가)"
)
