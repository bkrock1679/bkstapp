import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests

st.set_page_config(page_title="Stock Gap Analyzer", layout="wide")
st.title("📈 Stock Gap Analyzer with News")

# Sidebar Input
symbol = st.sidebar.text_input("Enter Stock Symbol (e.g., AAPL, NVDA):", "AAPL")

# Optional mapping from ticker to company name for better news search
ticker_map = {
    "AAPL": "Apple",
    "TSLA": "Tesla",
    "MSFT": "Microsoft",
    "GOOGL": "Google",
    "NVDA": "Nvidia",
    "AMZN": "Amazon",
    "META": "Meta",
    "EWS": "iShares MSCI Singapore ETF"
}
company_name = ticker_map.get(symbol.upper(), symbol)

# Date setup
end_date = datetime.today()
start_date = end_date - timedelta(weeks=6)

# Section 1: Price Table with Gap Calculation
st.header("Section 1: Daily Prices & Gap Analysis")

try:
    data = yf.download(symbol, start=start_date, end=end_date)
    if data.empty:
        st.error("No data found. Please check the stock symbol.")
    else:
        data = data[['Open', 'High', 'Low', 'Close']].copy()
        data.reset_index(inplace=True)

        # Calculate Previous Close and Gap
        data['Prev Close'] = data['Close'].shift(1)
        data['Gap ($)'] = data['Open'] - data['Prev Close']
        data['Gap Direction'] = data['Gap ($)'].apply(lambda x: 'Gap Up' if x > 0 else ('Gap Down' if x < 0 else 'No Gap'))

        # Reorder by most recent first
        data = data.sort_values(by='Date', ascending=False)

        # Format columns and center-align
        styled_data = data[['Date', 'Open', 'High', 'Low', 'Close', 'Prev Close', 'Gap ($)', 'Gap Direction']]
        styled_data.columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Prev Close', 'Gap ($)', 'Gap Direction']
        st.dataframe(styled_data.style.set_properties(**{'text-align': 'center'}), use_container_width=True)

except Exception as e:
    st.error(f"Error loading data: {e}")

# Section 2: Price Swings & News Analysis
st.header("Section 2: Price Swings & News")

try:
    # Identify significant swings (e.g., >3% up or down)
    data['Daily Change %'] = data['Close'].pct_change() * 100
    significant_swings = data[abs(data['Daily Change %']) > 3]

    if not significant_swings.empty:
        news_api_key = st.secrets["newsapi"]["key"]
        base_url = "https://newsapi.org/v2/everything"

        for _, row in significant_swings.iterrows():
            date_str = row['Date'].strftime('%Y-%m-%d')
            from_date = (row['Date'] - timedelta(days=1)).strftime('%Y-%m-%d')
            to_date = (row['Date'] + timedelta(days=1)).strftime('%Y-%m-%d')

            st.subheader(f"🗓️ {date_str} — {row['Daily Change %']:.2f}% {'🔺' if row['Daily Change %'] > 0 else '🔻'}")
            st.write(f"**Close Price:** {row['Close']:.2f}  |  **Previous Close:** {row['Prev Close']:.2f}")

            params = {
                'q': company_name,
                'from': from_date,
                'to': to_date,
                'sortBy': 'relevancy',
                'apiKey': news_api_key,
                'language': 'en',
                'pageSize': 5
            }
            response = requests.get(base_url, params=params)
            articles = response.json().get('articles', [])

            if articles:
                for article in articles:
                    st.markdown(f"- [{article['title']}]({article['url']})")
            else:
                st.write("No significant news found around this day.")
    else:
        st.info("No significant price swings (> 3%) in the last 6 weeks.")

except Exception as e:
    st.error(f"Error fetching news or analyzing swings: {e}")

st.caption("Note: Data from Yahoo Finance. News powered by NewsAPI.org")
