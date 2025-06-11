import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="Stock Insights Tool", layout="centered")

st.title("📈 Stock Insights — 6-Week Snapshot")
st.markdown("Enter a stock symbol (e.g., AAPL, AMZN) to view recent trends and news.")

# User Input
symbol = st.text_input("Enter Stock Symbol", value="AAPL").upper()

if st.button("Get Stock Insights"):
    try:
        # Time Range
        end_date = datetime.today()
        start_date = end_date - timedelta(weeks=6)

        # Fetch historical data
        stock = yf.Ticker(symbol)
        hist = stock.history(start=start_date, end=end_date)

        if hist.empty:
            st.error("No data found for this symbol. Please check the symbol and try again.")
        else:
            st.subheader("📊 Section 1: Daily Price (Last 6 Weeks)")
            price_df = hist[['Open', 'High', 'Low', 'Close']].round(2)
            price_df.index = price_df.index.date  # Simplify date format
            st.dataframe(price_df.tail(30), use_container_width=True)

            st.subheader("⚠️ Section 2: Volatility & Events")

            # Detect large moves > 5%
            hist['% Change'] = hist['Close'].pct_change() * 100
            spikes = hist[hist['% Change'].abs() > 5].copy()
            spikes['Direction'] = spikes['% Change'].apply(lambda x: 'Up' if x > 0 else 'Down')
            spikes = spikes[['% Change', 'Direction']].round(2)

            if spikes.empty:
                st.info("No major price swings (>5%) in the last 6 weeks.")
            else:
                st.write("### Significant Price Swings (>5%)")
                spikes.index = spikes.index.date
                st.dataframe(spikes)

                st.write("### Potential Reasons")
                st.markdown("Note: News headlines are not integrated yet. Check Yahoo Finance or Google News on these dates for context such as earnings, upgrades, etc.")

    except Exception as e:
        st.error(f"Something went wrong: {e}")
