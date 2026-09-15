import streamlit as st
import pandas as pd
import yfinance as yf
import datetime
import plotly.express as px

# 페이지 기본 설정
st.set_page_config(
    page_title="주식 포트폴리오 & 지표 모니터링 대시보드",
    page_icon="📈",
    layout="wide"
)

st.title("📈 내 실시간 주식 포트폴리오 대시보드 (원화/달러 통합)")
st.markdown("구글 스프레드시트와 연동되어 해외주식(달러)과 국내주식(원화)을 한화 기준으로 통합 관리합니다.")
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
@st.cache_data(ttl=3600)
def get_stock_data(ticker):
    df_daily = yf.download(ticker, period="2y", interval="1d", progress=False)
    if isinstance(df_daily.columns, pd.MultiIndex):
        df_daily.columns = df_daily.columns.get_level_values(0)
    df_daily['MA200'] = df_daily['Close'].rolling(window=200).mean()
    
    df_weekly = yf.download(ticker, period="3y", interval="1wk", progress=False)
    if isinstance(df_weekly.columns, pd.MultiIndex):
        df_weekly.columns = df_weekly.columns.get_level_values(0)
    df_weekly['RSI'] = calculate_rsi(df_weekly['Close'], window=14)
    
    return df_daily, df_weekly

# 실시간 환율(USD/KRW) 가져오기 함수
@st.cache_data(ttl=3600)
def get_exchange_rate():
    try:
        ex_df = yf.download("USDKRW=X", period="5d", interval="1d", progress=False)
        if isinstance(ex_df.columns, pd.MultiIndex):
            ex_df.columns = ex_df.columns.get_level_values(0)
        return float(ex_df.iloc[-1]['Close'])
    except:
        return 1350.0

# VIX(공포지수) 가져오기 함수
@st.cache_data(ttl=3600)
def get_vix_data():
    vix_df = yf.download("^VIX", period="5d", interval="1d", progress=False)
    if isinstance(vix_df.columns, pd.MultiIndex):
        vix_df.columns = vix_df.columns.get_level_values(0)
    current_vix = float(vix_df.iloc[-1]['Close'])
    prev_vix = float(vix_df.iloc[-2]['Close'])
    vix_change = current_vix - prev_vix
    return current_vix, vix_change


# ==========================================
# 1. 시장 심리 및 공포지수 기준 안내
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
            * **0 ~ 24 (🔴 극단적 공포):** 패닉 셀링 구간, 공격적 매수 기회.
            * **25 ~ 44 (🟠 공포):** 투자 심리 위축, 분할 매수 시작 구간.
            * **45 ~ 55 (⚪ 중립):** 시장 관망 구간.
            * **56 ~ 75 (🔵 탐욕):** 상승 기대감 확산, 주의 구간.
            * **76 ~ 100 (🟢 극단적 탐욕):** 과열 구간, 차익 실현 고려.
            """
        )

    with col_status:
        st.markdown("#### 📊 현재 시장 심리 상태 판정")
        st.metric(label="VIX Index (변동성)", value=f"{current_vix:.2f}", delta=f"{vix_change:+.2f}")
        st.metric(label="환산 공포탐욕 점수", value=f"{fng_approx}점 / 100점")
        
        if fng_approx <= 24:
            st.error("🚨 현재 상태: **극단적 공포** - 적극적인 분할 매수 타점!")
        elif fng_approx <= 44:
            st.warning("⚠️ 현재 상태: **공포** - 분할 매수를 고려할 시기입니다.")
        elif fng_approx <= 55:
            st.info("ℹ️ 현재 상태: **중립** - 시장이 평온합니다.")
        elif fng_approx <= 75:
            st.success("🙂 현재 상태: **탐욕** - 상승 추세이나 과열 주시.")
        else:
            st.markdown("🔥 현재 상태: **극단적 탐욕** - 리스크 관리 필요!")

except Exception as e:
    st.warning("시장 심리 데이터를 불러오는 중 오류가 발생했습니다.")

st.markdown("---")


# ==========================================
# 2. 포트폴리오 데이터 준비 (스프레드시트 or 샘플 안전장치)
# ==========================================
st.markdown("### 🗂️ 내 실시간 포트폴리오 비중 & 수익률 맵 (통합 한화 기준)")
st.caption("달러 종목은 실시간 환율을 곱해 원화로 환산하고, SK하이닉스 같은 원화 종목과 합쳐서 전체 비중을 계산합니다.")

# 💡 여기에 본인의 구글 스프레드시트 CSV 링크를 넣으세요.
# 만약 링크 자리에 "YOUR_GOOGLE_SHEET_CSV_URL_HERE"가 그대로 있거나 에러가 나면 샘플 데이터로 자동 실행됩니다.
sheet_url = "YOUR_GOOGLE_SHEET_CSV_URL_HERE"

usd_krw = get_exchange_rate()
st.sidebar.metric("환율 (USD/KRW)", f"{usd_krw:,.2f} 원")

df_portfolio = None

# 스프레드시트 읽기 시도
if "YOUR_GOOGLE_SHEET_CSV_URL" not in sheet_url and sheet_url.strip() != "":
    try:
        temp_df = pd.read_csv(sheet_url)
        # 필수 컬럼 검사
        required_cols = ['Ticker', 'Category', 'Quantity', 'BuyPrice', 'Currency']
        if all(col in temp_df.columns for col in required_cols):
            df_portfolio = temp_df.dropna(subset=['Ticker'])
        else:
            st.warning("⚠️ 스프레드시트 컬럼명이 올바르지 않습니다. (Ticker, Category, Quantity, BuyPrice, Currency 필요)")
    except Exception as e:
        st.warning(f"스프레드시트 연동 중 에러 발생: {e}. 기본 샘플 데이터로 동작합니다.")

# 링크가 없거나 에러가 났을 때 보여줄 안전한 기본 샘플 데이터 (하이닉스 포함)
if df_portfolio is None or len(df_portfolio) == 0:
    st.info("💡 **안내:** 현재 구글 스프레드시트 링크가 연결되지 않았거나 비어 있어, **기본 샘플 데이터(하이닉스 포함)**로 화면을 띄우고 있습니다.")
    df_portfolio = pd.DataFrame({
        "Ticker": ["QLD", "TQQQ", "SOXL", "000660.KS"],
        "Category": ["레버리지", "레버리지", "반도체", "국내주식"],
        "Quantity": [50, 100, 200, 10],
        "BuyPrice": [80.0, 50.0, 20.0, 150000.0],
        "Currency": ["USD", "USD", "USD", "KRW"]
    })

live_tickers = df_portfolio['Ticker'].tolist()
updated_rows = []
daily_data_dict = {}
weekly_data_dict = {}

# 주가 데이터 수집 및 한화 환산 계산
for idx, row in df_portfolio.iterrows():
    ticker = str(row['Ticker']).strip()
    qty = float(row['Quantity'])
    buy_price = float(row['BuyPrice'])
    currency = str(row['Currency']).strip()
    category = str(row['Category']).strip()
    
    try:
        df_d, df_w = get_stock_data(ticker)
        daily_data_dict[ticker] = df_d
        weekly_data_dict[ticker] = df_w
        
        raw_current_price = float(df_d.iloc[-1]['Close'])
        
        if currency.upper() == "USD":
            current_price_krw = raw_current_price * usd_krw
            buy_price_krw = buy_price * usd_krw
        else:
            current_price_krw = raw_current_price
            buy_price_krw = buy_price
            
        total_value_krw = current_price_krw * qty
        return_pct = ((raw_current_price - buy_price) / buy_price) * 100
        
        updated_rows.append({
            "Ticker": ticker,
            "Category": category,
            "TotalValue": total_value_krw,
            "Return": return_pct,
            "CurrentPrice": raw_current_price,
            "Currency": currency
        })
    except Exception as e:
        # 데이터 수집 실패 시 예외 처리
        fallback_val = buy_price * qty if currency.upper() == "KRW" else buy_price * qty * usd_krw
        updated_rows.append({
            "Ticker": ticker,
            "Category": category,
            "TotalValue": fallback_val,
            "Return": 0.0,
            "CurrentPrice": buy_price,
            "Currency": currency
        })
        
df_res = pd.DataFrame(updated_rows)

# 트리맵 시각화
try:
    fig_tree = px.treemap(
        df_res,
        path=['Category', 'Ticker'],
        values='TotalValue',
        color='Return',
        color_continuous_scale='RdYlGn',
        color_continuous_midpoint=0,
        range_color=[-20, 20]
    )
    fig_tree.update_layout(height=350, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig_tree, use_container_width=True)
except Exception as e:
    st.error(f"트리맵 시각화 중 오류 발생: {e}")


# ==========================================
# 3. 종목별 상세 지표 분석 탭
# ==========================================
st.markdown("---")
st.markdown("### 📊 보유 종목별 상세 지표 및 매수 조건 분석")

if len(live_tickers) > 0:
    tabs = st.tabs(live_tickers)
    
    for i, ticker in enumerate(live_tickers):
        with tabs[i]:
            st.subheader(f"{ticker} 상세 지표 분석")
            
            if ticker in daily_data_dict:
                df_daily = daily_data_dict[ticker]
                df_weekly = weekly_data_dict[ticker]
                
                current_price = float(df_daily.iloc[-1]['Close'])
                ma200 = float(df_daily.iloc[-1]['MA200'])
                disparity = ((current_price - ma200) / ma200) * 100
                current_rsi = float(df_weekly.iloc[-1]['RSI'])
                
                curr_symbol = "$" if ".KS" not in ticker and ".KQ" not in ticker else "원"
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric(label="현재가", value=f"{current_price:,.2f} {curr_symbol}")
                with col2:
                    st.metric(label="200일선 괴리율", value=f"{disparity:.2f}%", delta=f"MA200: {ma200:,.2f}")
                with col3:
                    st.metric(label="주봉 RSI (14)", value=f"{current_rsi:.2f}")
                    
                st.markdown("---")
                
                st.markdown(f"### 🎯 [{ticker}] 분할 매수 조건 판정")
                criteria_tiers = [
                    {"name": "1차 매수", "disp": -15.0, "rsi": 45.0},
                    {"name": "2차 매수", "disp": -25.0, "rsi": 38.0},
                    {"name": "3차 매수", "disp": -35.0, "rsi": 32.0},
                ]
                
                met_count = 0
                for tier in criteria_tiers:
                    is_disp_met = disparity <= tier["disp"]
                    is_rsi_met = current_rsi <= tier["rsi"]
                    
                    if is_disp_met or is_rsi_met:
                        met_count += 1
                        status_str = "🟢 **[충족]**"
                    else:
                        status_str = "⚪ (미달)"
                        
                    st.markdown(f"- **{tier['name']}** (목표 괴리율 `{tier['disp']}%` 이하 또는 RSI `{tier['rsi']}` 이하) -> {status_str}")
                
                if met_count > 0:
                    st.success(f"🔥 [{ticker}] 매수 조건 충족 단계 발생!")
                else:
                    st.info(f"⏳ [{ticker}] 관망 중")
                    
                st.markdown("---")
                st.line_chart(df_daily[['Close', 'MA200']].tail(250))

# 사이드바 정보
st.sidebar.markdown("---")
st.sidebar.header("ℹ️ 설정 정보")
st.sidebar.info(
    "원화/달러 통합 포트폴리오 대시보드 v3.3\n\n"
    "스프레드시트 누락 시 자동 샘플 모드 지원"
)
