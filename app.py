import streamlit as st
import yfinance as yf
import pandas as pd
import requests
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px

st.set_page_config(page_title="Stock Insights Tool", layout="centered")

st.title("📈 Stock Insights — 6-Week Snapshot with News & Indicators")

symbol = st.text_input("Enter Stock Symbol", value="AAPL").upper()

# NewsAPI setup
news_api_key = st.secrets["newsapi"]["key"]
news_url = "https://newsapi.org/v2/everything"

def get_news(query, from_date, to_date):
    params = {
        "q": query,
        "from": from_date,
        "to": to_date,
        "language": "en",
        "sortBy": "relevancy",
        "apiKey": news_api_key,
        "pageSize": 5,
    }
    response = requests.get(news_url, params=params)
    if response.status_code == 200:
        return response.json().get("articles", [])
    else:
        return []

def calculate_ema(data, period=20):
    return data['Close'].ewm(span=period, adjust=False).mean()

def calculate_rsi(data, period=14):
    delta = data['Close'].diff()
    gain = delta.clip(lower=0)
    loss = -1 * delta.clip(upper=0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

if st.button("Get Stock Insights"):
    try:
        end_date = datetime.today()
        start_date = end_date - timedelta(weeks=6)

        stock = yf.Ticker(symbol)
        hist = stock.history(start=start_date, end=end_date)
        hist = hist[['Open', 'High', 'Low', 'Close']].round(2)

        if hist.empty:
            st.error("No data found for this symbol.")
        else:
            hist.index = pd.to_datetime(hist.index)

            # UI controls for indicators
            show_ema = st.checkbox("Show EMA (20)", value=True)
            show_rsi = st.checkbox("Show RSI (14)", value=True)

            # Calculate indicators if selected
            if show_ema:
                hist['EMA20'] = calculate_ema(hist, 20)
            if show_rsi:
                hist['RSI14'] = calculate_rsi(hist, 14)

            st.subheader("📊 Section 1: Daily Prices (Recent First)")
            st.dataframe(hist[::-1], use_container_width=True)

            # Plot price + EMA chart
            fig_price = go.Figure()
            fig_price.add_trace(go.Candlestick(
                x=hist.index,
                open=hist['Open'],
                high=hist['High'],
                low=hist['Low'],
                close=hist['Close'],
                name="Price"
            ))
            if show_ema:
                fig_price.add_trace(go.Scatter(
                    x=hist.index,
                    y=hist['EMA20'],
                    mode='lines',
                    name='EMA 20',
                    line=dict(color='orange', width=2)
                ))
            fig_price.update_layout(title=f"{symbol} Price Chart", xaxis_title="Date", yaxis_title="Price")
            st.plotly_chart(fig_price, use_container_width=True)

            # Plot RSI chart
            if show_rsi:
                fig_rsi = go.Figure()
                fig_rsi.add_trace(go.Scatter(
                    x=hist.index,
                    y=hist['RSI14'],
                    mode='lines',
                    name='RSI 14',
                    line=dict(color='green', width=2)
                ))
                fig_rsi.update_layout(
                    title=f"{symbol} RSI (14)",
                    xaxis_title="Date",
                    yaxis_title="RSI",
                    yaxis=dict(range=[0, 100]),
                    shapes=[
                        # Overbought and oversold lines
                        dict(type='line', xref='paper', x0=0, x1=1, y0=70, y1=70,
                             line=dict(color='red', dash='dash')),
                        dict(type='line', xref='paper', x0=0, x1=1, y0=30, y1=30,
                             line=dict(color='blue', dash='dash'))
                    ]
                )
                st.plotly_chart(fig_rsi, use_container_width=True)

            # Section 2: Volatility & News
            st.subheader("⚠️ Section 2: Volatility & Related News")
            hist['% Change'] = hist['Close'].pct_change() * 100
            spikes = hist[hist['% Change'].abs() > 5].copy()
            spikes['Direction'] = spikes['% Change'].apply(lambda x: 'Up' if x > 0 else 'Down')
            spikes = spikes[['% Change', 'Direction']].round(2)

            if spikes.empty:
                st.info("No major price swings (>5%) in the last 6 weeks.")
            else:
                for date, row in spikes[::-1].iterrows():
                    st.write(f"### {date.date()} — {row['Direction']}ward move of {row['% Change']}%")
                    headlines = get_news(symbol, date.strftime('%Y-%m-%d'), date.strftime('%Y-%m-%d'))
                    if headlines:
                        for article in headlines:
                            st.markdown(f"- [{article['title']}]({article['url']})")
                    else:
                        st.write("No news found for this date.")

            # Live news today
            st.subheader("📰 Live News: Latest Headlines")
            today_str = datetime.today().strftime('%Y-%m-%d')
            news_today = get_news(symbol, today_str, today_str)
            if news_today:
                for article in news_today:
                    st.markdown(f"- [{article['title']}]({article['url']})")
            else:
                st.write("No recent news found today.")

    except Exception as e:
        st.error(f"Error: {e}")
