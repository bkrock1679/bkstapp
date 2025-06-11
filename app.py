import streamlit as st
import yfinance as yf
import pandas as pd
import requests
from datetime import datetime, timedelta

st.set_page_config(page_title="Stock Gap Analyzer", layout="wide")
st.title("📈 Stock Gap Analyzer with News")

# Sidebar input for stock symbol
symbol = st.sidebar.text_input("Enter Stock Symbol (e.g., AAPL, NVDA):", "AAPL")

# Define date range (last 6 weeks)
end_date = datetime.today()
start_date = end_date - timedelta(weeks=6)

# Section 1: Daily Prices & Gap Analysis
st.header("Section 1: Daily Prices & Gap Analysis")

try:
    # Download stock data
    data = yf.download(symbol, start=start_date, end=end_date)
    if data.empty:
        st.error("No data found. Please check the stock symbol.")
    else:
        data = data[['Open', 'High', 'Low', 'Close']].copy()
        data.reset_index(inplace=True)
        data['Date'] = pd.to_datetime(data['Date'])

        # Calculate previous day's close
        data['Prev Close'] = data['Close'].shift(1)

        # Debug types (optional, can comment out)
        # st.write(f"Open type: {type(data['Open'])}")
        # st.write(f"Prev Close type: {type(data['Prev Close'])}")

        # Calculate gap as today's open minus previous close
        data['Gap ($)'] = data['Open'] - data['Prev Close']

        # Gap direction label
        data['Gap Direction'] = data['Gap ($)'].apply(lambda x: 'Gap Up' if x > 0 else ('Gap Down' if x < 0 else 'No Gap'))

        # Sort dates descending (most recent first)
        data = data.sort_values('Date', ascending=False)

        # Display table with centered text
        st.dataframe(
            data[['Date', 'Open', 'High', 'Low', 'Close', 'Prev Close', 'Gap ($)', 'Gap Direction']]
            .style.set_properties(**{'text-align': 'center'}),
            use_container_width=True
        )

except Exception as e:
    st.error(f"Error loading data: {e}")

# Section 2: Price Swings & News
st.header("Section 2: Price Swings & News")

try:
    # Calculate daily percent change in close price
    data['Daily Change %'] = data['Close'].pct_change() * 100

    # Filter for significant swings > 3%
    significant_swings = data[abs(data['Daily Change %']) > 3]

    if not significant_swings.empty:
        news_api_key = st.secrets["newsapi"]["key"]
        base_url = "https://newsapi.org/v2/everything"

        for _, row in significant_swings.iterrows():
            # Ensure Date is scalar datetime and convert to string
            date_str = pd.to_datetime(row['Date']).strftime('%Y-%m-%d')

            st.subheader(f"🗓️ {date_str} — {row['Daily Change %']:.2f}% {'🔺' if row['Daily Change %'] > 0 else '🔻'}")
            st.write(f"**Close Price:** {row['Close']:.2f}  |  **Previous Close:** {row['Prev Close']:.2f}")

            # Query NewsAPI for relevant news on this date
            params = {
                'q': symbol,
                'from': date_str,
                'to': date_str,
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
                st.write("No significant news found on this day.")
    else:
        st.info("No significant price swings (> 3%) in the last 6 weeks.")

except Exception as e:
    st.error(f"Error fetching news or analyzing swings: {e}")

st.caption("Note: Data from Yahoo Finance. News powered by NewsAPI.org")
