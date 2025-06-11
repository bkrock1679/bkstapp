import streamlit as st
import yfinance as yf
import pandas as pd
import requests
from datetime import datetime, timedelta

st.set_page_config(page_title="Stock Gap Analyzer", layout="wide")
st.title("📈 Stock Gap Analyzer with News")

symbol = st.sidebar.text_input("Enter Stock Symbol (e.g., AAPL, NVDA):", "AAPL")

end_date = datetime.today()
start_date = end_date - timedelta(weeks=6)

st.header("Section 1: Daily Prices & Gap Analysis")

data = None  # Initialize globally

try:
    data = yf.download(symbol, start=start_date, end=end_date)
    if data.empty:
        st.error("No data found. Please check the stock symbol.")
    else:
        data = data[['Open', 'High', 'Low', 'Close']].copy()
        data.reset_index(inplace=True)

        data['Date'] = pd.to_datetime(data['Date'])
        data['Prev Close'] = data['Close'].shift(1)

        # Debug print to verify types and shapes
        st.write("Type of data['Open']:", type(data['Open']))
        st.write("Type of data['Prev Close']:", type(data['Prev Close']))
        st.write("data['Open'].shape:", data['Open'].shape)
        st.write("data['Prev Close'].shape:", data['Prev Close'].shape)

        # Calculate Gap ($)
        data['Gap ($)'] = data['Open'] - data['Prev Close']

        data['Gap Direction'] = data['Gap ($)'].apply(
            lambda x: 'Gap Up' if x > 0 else ('Gap Down' if x < 0 else 'No Gap'))

        data = data.sort_values('Date', ascending=False)

        # Create string date column
        data['Date_str'] = data['Date'].dt.strftime('%Y-%m-%d')

        st.dataframe(
            data[['Date', 'Open', 'High', 'Low', 'Close', 'Prev Close', 'Gap ($)', 'Gap Direction']]
            .style.set_properties(**{'text-align': 'center'}),
            use_container_width=True
        )

except Exception as e:
    st.error(f"Error loading data: {e}")

if data is not None and not data.empty:

    st.header("Section 2: Price Swings & News")

    try:
        data['Daily Change %'] = data['Close'].pct_change() * 100
        significant_swings = data[abs(data['Daily Change %']) > 3]

        if not significant_swings.empty:
            news_api_key = st.secrets["newsapi"]["key"]
            base_url = "https://newsapi.org/v2/everything"

            for _, row in significant_swings.iterrows():
                date_str = row['Date_str']

                st.subheader(f"🗓️ {date_str} — {row['Daily Change %']:.2f}% {'🔺' if row['Daily Change %'] > 0 else '🔻'}")
                st.write(f"**Close Price:** {row['Close']:.2f}  |  **Previous Close:** {row['Prev Close']:.2f}")

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

else:
    st.info("Skipping Section 2 because no valid stock data available.")

st.caption("Note: Data from Yahoo Finance. News powered by NewsAPI.org")
