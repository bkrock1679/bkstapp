import streamlit as st
import yfinance as yf
import pandas as pd
import requests
from datetime import datetime, timedelta

st.set_page_config(page_title="Stock Insights Tool", layout="centered")
st.title("📈 Stock Insights — 6-Week Snapshot with News")

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
        st.warning(f"News API Error: {response.status_code}")
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
            st.subheader("📊 Section 1: Daily Prices (Recent First)")
            hist.index = hist.index.date
            st.dataframe(hist[::-1], use_container_width=True)

            # Attempt to get full company name
            try:
                company_name = stock.info.get("shortName", symbol)
            except Exception:
                company_name = symbol

            st.subheader("⚠️ Section 2: Volatility & Related News")
            hist['% Change'] = hist['Close'].pct_change() * 100
            spikes = hist[hist['% Change'].abs() > 5].copy()
            spikes['Direction'] = spikes['% Change'].apply(lambda x: 'Up' if x > 0 else 'Down')
            spikes = spikes[['% Change', 'Direction']].round(2)

            if spikes.empty:
                st.info("No major price swings (>5%) in the last 6 weeks.")
            else:
                for date, row in spikes[::-1].iterrows():
                    date_str = date.isoformat()
                    next_day_str = (datetime.fromisoformat(date_str) + timedelta(days=1)).strftime('%Y-%m-%d')
                    st.write(f"### {date_str} — {row['Direction']}ward move of {row['% Change']}%")
                    headlines = get_news(company_name, date_str, next_day_str)
                    if headlines:
                        for article in headlines:
                            st.markdown(f"- [{article['title']}]({article['url']})")
                    else:
                        st.write("No news found for this date.")

            st.subheader("📰 Live News: Latest Headlines")
            today_str = datetime.today().strftime('%Y-%m-%d')
            tomorrow_str = (datetime.today() + timedelta(days=1)).strftime('%Y-%m-%d')
            news_today = get_news(company_name, today_str, tomorrow_str)
            if news_today:
                for article in news_today:
                    st.markdown(f"- [{article['title']}]({article['url']})")
            else:
                st.write("No recent news found today.")

    except Exception as e:
        st.error(f"Error: {e}")
