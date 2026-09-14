import os
import pandas as pd
import yfinance as yf
import requests
import datetime

TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    response = requests.post(url, json=payload)
    return response.json()

def calculate_rsi(data, window=14):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def check_qld_conditions():
    ticker = "QLD"
    df_daily = yf.download(ticker, period="2y", interval="1d", progress=False)
    if isinstance(df_daily.columns, pd.MultiIndex):
        df_daily.columns = df_daily.columns.get_level_values(0)
    df_daily['MA200'] = df_daily['Close'].rolling(window=200).mean()
    
    current_price = df_daily.iloc[-1]['Close']
    ma200 = df_daily.iloc[-1]['MA200']
    disparity = ((current_price - ma200) / ma200) * 100

    df_weekly = yf.download(ticker, period="3y", interval="1wk", progress=False)
    if isinstance(df_weekly.columns, pd.MultiIndex):
        df_weekly.columns = df_weekly.columns.get_level_values(0)
    df_weekly['RSI'] = calculate_rsi(df_weekly['Close'], window=14)
    current_rsi = df_weekly.iloc[-1]['RSI']

    alerts = []
    if disparity <= -26:
        alerts.append(f"🚨 **[QLD 일봉 경고]** 200일선 괴리율 -26% 이하! (현재: {disparity:.2f}%)")
    elif disparity <= -18:
        alerts.append(f"⚠️ **[QLD 일봉 주의]** 200일선 괴리율 -18% 이하! (현재: {disparity:.2f}%)")
    elif disparity <= -10:
        alerts.append(f"🔔 **[QLD 일봉 관심]** 200일선 괴리율 -10% 이하! (현재: {disparity:.2f}%)")

    if current_rsi <= 36:
        alerts.append(f"🚨 **[QLD 주봉 경고]** RSI 36 이하 진입! (현재 RSI: {current_rsi:.2f})")
    elif current_rsi <= 42:
        alerts.append(f"⚠️ **[QLD 주봉 주의]** RSI 42 이하 진입! (현재 RSI: {current_rsi:.2f})")
    elif current_rsi <= 48:
        alerts.append(f"🔔 **[QLD 주봉 관심]** RSI 48 이하 진입! (현재 RSI: {current_rsi:.2f})")

    return alerts

def check_tqqq_conditions():
    ticker = "TQQQ"
    df_daily = yf.download(ticker, period="2y", interval="1d", progress=False)
    if isinstance(df_daily.columns, pd.MultiIndex):
        df_daily.columns = df_daily.columns.get_level_values(0)
    df_daily['MA200'] = df_daily['Close'].rolling(window=200).mean()
    
    current_price = df_daily.iloc[-1]['Close']
    ma200 = df_daily.iloc[-1]['MA200']
    disparity = ((current_price - ma200) / ma200) * 100

    df_weekly = yf.download(ticker, period="3y", interval="1wk", progress=False)
    if isinstance(df_weekly.columns, pd.MultiIndex):
        df_weekly.columns = df_weekly.columns.get_level_values(0)
    df_weekly['RSI'] = calculate_rsi(df_weekly['Close'], window=14)
    current_rsi = df_weekly.iloc[-1]['RSI']

    alerts = []
    if disparity <= -45:
        alerts.append(f"🚨 **[TQQQ 일봉 경고]** 200일선 괴리율 -45% 이하! (현재: {disparity:.2f}%)")
    elif disparity <= -32:
        alerts.append(f"⚠️ **[TQQQ 일봉 주의]** 200일선 괴리율 -32% 이하! (현재: {disparity:.2f}%)")
    elif disparity <= -18:
        alerts.append(f"🔔 **[TQQQ 일봉 관심]** 200일선 괴리율 -18% 이하! (현재: {disparity:.2f}%)")

    if current_rsi <= 31:
        alerts.append(f"🚨 **[TQQQ 주봉 경고]** RSI 31 이하 진입! (현재 RSI: {current_rsi:.2f})")
    elif current_rsi <= 36:
        alerts.append(f"⚠️ **[TQQQ 주봉 주의]** RSI 36 이하 진입! (현재 RSI: {current_rsi:.2f})")
    elif current_rsi <= 43:
        alerts.append(f"🔔 **[TQQQ 주봉 관심]** RSI 43 이하 진입! (현재 RSI: {current_rsi:.2f})")

    return alerts

def check_soxl_conditions():
    ticker = "SOXL"
    df_daily = yf.download(ticker, period="2y", interval="1d", progress=False)
    if isinstance(df_daily.columns, pd.MultiIndex):
        df_daily.columns = df_daily.columns.get_level_values(0)
    df_daily['MA200'] = df_daily['Close'].rolling(window=200).mean()
    
    current_price = df_daily.iloc[-1]['Close']
    ma200 = df_daily.iloc[-1]['MA200']
    disparity = ((current_price - ma200) / ma200) * 100

    df_weekly = yf.download(ticker, period="3y", interval="1wk", progress=False)
    if isinstance(df_weekly.columns, pd.MultiIndex):
        df_weekly.columns = df_weekly.columns.get_level_values(0)
    df_weekly['RSI'] = calculate_rsi(df_weekly['Close'], window=14)
    current_rsi = df_weekly.iloc[-1]['RSI']

    alerts = []
    if disparity <= -45:
        alerts.append(f"🚨 **[SOXL 일봉 경고]** 200일선 괴리율 -45% 이하! (현재: {disparity:.2f}%)")
    elif disparity <= -32:
        alerts.append(f"⚠️ **[SOXL 일봉 주의]** 200일선 괴리율 -32% 이하! (현재: {disparity:.2f}%)")
    elif disparity <= -18:
        alerts.append(f"🔔 **[SOXL 일봉 관심]** 200일선 괴리율 -18% 이하! (현재: {disparity:.2f}%)")

    if current_rsi <= 31:
        alerts.append(f"🚨 **[SOXL 주봉 경고]** RSI 31 이하 진입! (현재 RSI: {current_rsi:.2f})")
    elif current_rsi <= 36:
        alerts.append(f"⚠️ **[SOXL 주봉 주의]** RSI 36 이하 진입! (현재 RSI: {current_rsi:.2f})")
    elif current_rsi <= 43:
        alerts.append(f"🔔 **[SOXL 주봉 관심]** RSI 43 이하 진입! (현재 RSI: {current_rsi:.2f})")

    return alerts

def run_all_checks():
    all_alerts = []
    all_alerts.extend(check_qld_conditions())
    all_alerts.extend(check_tqqq_conditions())
    all_alerts.extend(check_soxl_conditions())
    
    if all_alerts:
        final_message = "📊 **[주식 조건 만족 알림]**\n\n" + "\n\n".join(all_alerts)
        send_telegram_message(final_message)
        print("조건 만족 메시지 전송 완료")
    else:
        print("조건 만족 종목 없음")

if __name__ == "__main__":
    run_all_checks()
