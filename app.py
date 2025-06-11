import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="Stock Price & Gap Dashboard", layout="wide")

# CSS for center alignment & some light styling
st.markdown(
    """
    <style>
    .stApp {
        background-color: #f0f8ff;
    }
    .title {
        color: #007acc;
        font-size: 36px;
        font-weight: 700;
        padding-bottom: 15px;
        text-align: center;
    }
    .section-header {
        color: #004c99;
        font-size: 24px;
        font-weight: 600;
        margin-top: 20px;
        margin-bottom: 10px;
    }
    .dataframe td, .dataframe th {
        text-align: center !important;
    }
    .dataframe th {
        background-color: #cce6ff !important;
        color: #003366 !important;
    }
    .dataframe td {
        background-color: #e6f0ff !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

def add_gap_columns(df):
    df = df.copy()
    df["PrevClose"] = df["Close"].shift(1)
    df["Gap"] = df["Open"] - df["PrevClose"]
    df["GapDirection"] = df["Gap"].apply(lambda x: "Gap Up" if x > 0 else ("Gap Down" if x < 0 else "No Gap"))
    df.drop(columns=["PrevClose"], inplace=True)
    return df

def get_stock_data(symbol, weeks=6):
    ticker = yf.Ticker(symbol)
    
    end_date = datetime.today()
    start_date = end_date - timedelta(weeks=weeks)
    
    df = ticker.history(start=start_date.strftime("%Y-%m-%d"), end=end_date.strftime("%Y-%m-%d"), interval="1d")
    df.reset_index(inplace=True)
    
    # Reverse order: newest dates first
    df = df.iloc[::-1].reset_index(drop=True)
    
    # Keep only needed columns for display
    df = df[["Date", "Open", "High", "Low", "Close"]]
    
    df = add_gap_columns(df)
    
    # Format Date column as string for better display
    df["Date"] = df["Date"].dt.strftime("%Y-%m-%d")
    
    # Round numeric columns for neatness
    for col in ["Open", "High", "Low", "Close", "Gap"]:
        df[col] = df[col].round(2)
    
    return df

st.markdown('<h1 class="title">Stock Price & Gap Dashboard</h1>', unsafe_allow_html=True)

stock_symbol = st.text_input("Enter Stock Symbol (e.g. AAPL, MSFT):", value="AAPL").upper()

if stock_symbol:
    try:
        df_prices = get_stock_data(stock_symbol)
        
        st.markdown('<div class="section-header">Section 1: Daily Prices with Gap Info</div>', unsafe_allow_html=True)
        st.dataframe(df_prices, use_container_width=True)
        
        # Section 2 placeholder (news integration can be added here)
        st.markdown('<div class="section-header">Section 2: Price Swings & News (Coming Soon)</div>', unsafe_allow_html=True)
        st.info("News and price swing analysis will be integrated here in future updates.")
        
    except Exception as e:
        st.error(f"Error fetching data for symbol '{stock_symbol}': {e}")

else:
    st.info("Please enter a stock symbol above.")
