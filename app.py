import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import requests

st.set_page_config(page_title="Stock Dashboard", layout="wide")

# --- Styling ---
st.markdown(
    """
    <style>
    .stApp { background-color: #f7fbff; }
    .title { color: #005b96; font-size: 36px; font-weight: 700; text-align: center; padding: 20px 0; }
    .section-header { color: #004080; font-size: 24px; font-weight: 600; margin-top: 30px; }
    .dataframe td, .dataframe th { text-align: center !important; }
    .dataframe th { background-color: #d0e6f7 !important; }
    .dataframe td { background-color: #eef6fb !important; }
    </style>
    """,
    unsafe_allow_html=True
)

# --- Gap Calculation ---
def add_gap_columns(df):
    df = df.copy()
    df["PrevClose"] = df["Close"].shift(1)
    df["Gap"] = df["Open"] - df["PrevClose"]
    df["GapDirection"] = df["Gap"].apply(lambda x: "Gap Up" if x > 0 else ("Gap Down" if x < 0 else "No Gap"))
    df.drop(columns=["PrevClose"], inplace=True)
    return df

# --- Get Stock Data ---
def get_stock_data(symbol, weeks=6):
    end_date = datetime.today()
    start_date = end_date - timedelta(weeks=weeks)
    df = yf.Ticker(symbol).history(start=start_date, end=end_date, interval="1d")
    df.reset_index(inplace=True)
    df = df[["Date", "Open", "High", "Low", "Close"]]
    df = df.iloc[::-1].reset_index(drop=True)
    df = add_gap_columns(df)
    df["Date"] = df["Date"].dt.strftime("%Y-%m-%d")
    for col in ["Open", "High", "Low", "Close", "Gap"]:
        df[col] = df[col].round(2)
    return df

# --- Get News from NewsAPI ---
def get_news(symbol, from_date):
    api_key = st.secrets["newsapi"]["key"]
    url = f"https://newsapi.org/v2/everything?q={symbol}&from={from_date}&sortBy=publishedAt&apiKey={api_key}&language=en"
    response = requests.get(url)
    articles = response.json().get("articles", [])
    headlines = []
    for article in articles[:10]:
        headlines.append(f"- [{article['title']}]({article['url']})")
    return headlines

# --- Detect Price Swings ---
def detect_swings(df, threshold_percent=3):
    swings = []
    for i in range(1, len(df)):
        prev_close = df.loc[i - 1, "Close"]
        current_close = df.loc[i, "Close"]
        change = ((current_close - prev_close) / prev_close) * 100
        if abs(change) >= threshold_percent:
            swings.append((df.loc[i, "Date"], round(change, 2)))
    return swings

# --- App UI ---
st.markdown('<div class="title">Stock Price Gap & News Dashboard</div>', unsafe_allow_html=True)

symbol = st.text_input("Enter Stock Symbol (e.g., AMZN, AAPL, TSLA):", value="AAPL").upper()

if symbol:
    try:
        df = get_stock_data(symbol)
        st.markdown('<div class="section-header">Section 1: Daily Prices with Gap Info</div>', unsafe_allow_html=True)
        st.dataframe(df, use_container_width=True)

        st.markdown('<div class="section-header">Section 2: Significant Price Swings & Related News</div>', unsafe_allow_html=True)
        
        swings = detect_swings(df)
        if swings:
            for date, change in swings:
                direction = "▲" if change > 0 else "▼"
                st.write(f"**{date}**: {direction} {abs(change)}% change")
                news_headlines = get_news(symbol, date)
                if news_headlines:
                    for item in news_headlines:
                        st.markdown(item)
                else:
                    st.write("_No relevant news found._")
        else:
            st.info("No significant price swings (±3%) in the last 6 weeks.")

    except Exception as e:
        st.error(f"Error: {e}")
else:
    st.info("Please enter a stock symbol above.")
