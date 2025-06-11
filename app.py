import streamlit as st
import yfinance as yf
import pandas as pd
import requests
from datetime import datetime, timedelta

st.set_page_config(page_title="Stock Insights Tool", layout="wide")

# CSS to control table width, padding, and center alignment without vertical scrolling inside table
st.markdown(
    """
    <style>
    /* Container for table */
    .table-container {
        max-width: 700px;  /* Adjust max width as needed */
        margin: 0;
        padding: 0;
    }
    /* Table style */
    .table-container table {
        border-collapse: collapse;
        width: 100%;
        font-size: 14px;
    }
    .table-container th, .table-container td {
        border: 1px solid #ddd;
        text-align: center;
        padding: 6px 8px;
        white-space: nowrap;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("📈 Stock Insights — 6-Week Snapshot with News")
symbol = st.text_input("Enter Stock Symbol", value="AAPL").upper()

marketaux_api_key = st.secrets["marketaux"]["key"]

def get_news_marketaux(symbol, from_date, to_date, api_key):
    url = "https://api.marketaux.com/v1/news/all"
    params = {
        "symbols": symbol,
        "filter_entities": "true",
        "language": "en",
        "published_on.min": from_date,
        "published_on.max": to_date,
        "api_token": api_key,
        "limit": 5,
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        return data.get("data", [])
    else:
        st.warning(f"Marketaux API Error: {response.status_code} - {response.text}")
        return []

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
            hist['Day'] = hist.index.strftime('%A')
            hist.index = hist.index.date
            hist = hist[['Day', 'Open', 'High', 'Low', 'Close']]

            col1, col2 = st.columns([6, 4])

            with col1:
                st.subheader("📊 Section 1: Daily Prices (Recent First)")
                # Convert styled dataframe to HTML with container div
                styled_table = hist[::-1].style.format("{:.2f}").set_properties(**{'text-align': 'center'})
                html = styled_table.render()
                st.markdown(f'<div class="table-container">{html}</div>', unsafe_allow_html=True)

            with col2:
                st.subheader("⚠️ Section 2: Volatility & Related News")
                hist['% Change'] = hist['Close'].pct_change() * 100
                spikes = hist[hist['% Change'].abs() > 5].copy()
                spikes['Direction'] = spikes['% Change'].apply(lambda x: 'Up' if x > 0 else 'Down')
                spikes = spikes[['% Change', 'Direction']].round(2)

                if spikes.empty:
                    st.info("No major price swings (>5%) in the last 6 weeks.")
                else:
                    recent_spike = spikes.tail(1)
                    for date, row in recent_spike[::-1].iterrows():
                        date_str = date.isoformat()
                        next_day_str = (datetime.fromisoformat(date_str) + timedelta(days=1)).strftime('%Y-%m-%d')
                        st.write(f"### {date_str} — {row['Direction']}ward move of {row['% Change']}%")
                        headlines = get_news_marketaux(symbol, date_str, next_day_str, marketaux_api_key)
                        if headlines:
                            for article in headlines:
                                st.markdown(f"- [{article['title']}]({article['url']})")
                        else:
                            st.write("No news found for this date.")

                st.subheader("📰 Live News: Latest Headlines")
                today_str = datetime.today().strftime('%Y-%m-%d')
                news_today = get_news_marketaux(symbol, today_str, today_str, marketaux_api_key)
                if news_today:
                    for article in news_today:
                        st.markdown(f"- [{article['title']}]({article['url']})")
                else:
                    st.write("No recent news found today.")

    except Exception as e:
        st.error(f"Error: {e}")
