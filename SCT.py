import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import ta
from textblob import TextBlob

# Page config
st.set_page_config(
    page_title="Stock Comparison Tool",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Title and description
st.title("📈 Stock Comparison Tool")

# Sidebar input
st.sidebar.header("User Input")

# Popular tickers
popular = st.sidebar.selectbox(
    "Choose a popular stock:",
    ["None", "AAPL", "MSFT", "GOOGL", "TSLA", "INFY.NS", "TCS.NS"]
)

# Manual input
ticker = st.sidebar.text_input("Or enter a stock ticker:", "").upper()

# Use popular if selected
if popular != "None":
    ticker = popular

# Guard clause
if not ticker:
    st.warning("Please select or enter a ticker symbol from the sidebar.")
    st.stop()

# Date input
start_date = st.sidebar.date_input("Start Date", pd.to_datetime("2022-01-01"))
end_date = st.sidebar.date_input("End Date", pd.to_datetime("2024-12-31"))

# Indicator selection
indicators = st.sidebar.multiselect(
    "Select Technical Indicators",
    ['SMA (20)', 'EMA (20)', 'RSI', 'MACD'],
    default=['SMA (20)', 'RSI']
)

# Load stock data
@st.cache_data
def load_data(ticker, start, end):
    df = yf.download(ticker, start=start, end=end)
    df.reset_index(inplace=True)
    return df

data = load_data(ticker, start_date, end_date)

if 'Close' not in data.columns:
    st.error("❌ 'Close' column not found in data.")
    st.stop()

# Fix: Extract 'Close' as Series
close_col = pd.to_numeric(data['Close'].values.flatten(), errors='coerce')



if close_col.isnull().all():
    st.error("❌ Invalid or missing closing price data.")
    st.stop()

# Technical Indicators
if 'SMA (20)' in indicators:
    data['SMA20'] = ta.trend.sma_indicator(close=close_col, window=20)

if 'EMA (20)' in indicators:
    data['EMA20'] = ta.trend.ema_indicator(close=close_col, window=20)

if 'RSI' in indicators:
    data['RSI'] = ta.momentum.rsi(close=close_col, window=14)

if 'MACD' in indicators:
    try:
        macd_obj = ta.trend.macd(close=close_col)
        data['MACD'] = macd_obj.macd()
        data['Signal_Line'] = macd_obj.macd_signal()
    except Exception as e:
        st.warning(f"⚠ MACD error: {e}")
        data['MACD'] = data['Signal_Line'] = None

# Candlestick chart
st.subheader(f"📉 Price Chart for {ticker}")
fig = go.Figure()
fig.add_trace(go.Candlestick(
    x=data['Date'],
    open=data['Open'],
    high=data['High'],
    low=data['Low'],
    close=data['Close'],
    name='Candlestick'
))
if 'SMA (20)' in indicators and 'SMA20' in data:
    fig.add_trace(go.Scatter(x=data['Date'], y=data['SMA20'], name='SMA 20', line=dict(color='blue')))
if 'EMA (20)' in indicators and 'EMA20' in data:
    fig.add_trace(go.Scatter(x=data['Date'], y=data['EMA20'], name='EMA 20', line=dict(color='orange')))
fig.update_layout(
    xaxis_rangeslider_visible=False,
    template='plotly_white',
    height=600
)
st.plotly_chart(fig, use_container_width=True)

# RSI
if 'RSI' in indicators and 'RSI' in data:
    st.subheader("📊 RSI (Relative Strength Index)")
    fig_rsi = go.Figure()
    fig_rsi.add_trace(go.Scatter(x=data['Date'], y=data['RSI'], line=dict(color='purple'), name='RSI'))
    fig_rsi.add_hline(y=70, line_dash="dash", line_color="red")
    fig_rsi.add_hline(y=30, line_dash="dash", line_color="green")
    fig_rsi.update_layout(template='plotly_white', height=300)
    st.plotly_chart(fig_rsi, use_container_width=True)

# MACD
if 'MACD' in indicators and data.get('MACD') is not None:
    st.subheader("📊 MACD")
    fig_macd = go.Figure()
    fig_macd.add_trace(go.Scatter(x=data['Date'], y=data['MACD'], name='MACD', line=dict(color='blue')))
    fig_macd.add_trace(go.Scatter(x=data['Date'], y=data['Signal_Line'], name='Signal Line', line=dict(color='red')))
    fig_macd.update_layout(template='plotly_white', height=300)
    st.plotly_chart(fig_macd, use_container_width=True)

# Metrics
st.subheader("📈 Key Metrics")
col1, col2, col3 = st.columns(3)
col1.metric("Latest Close", f"${float(data['Close'].iloc[-1]):.2f}")
col2.metric("52W High", f"${float(data['High'].max()):.2f}")
col3.metric("52W Low", f"${float(data['Low'].min()):.2f}")

# Fundamental ratios
st.subheader("📘 Fundamental Ratio Analysis")
ticker_obj = yf.Ticker(ticker)
info = ticker_obj.info

col4, col5, col6 = st.columns(3)
col4.metric("P/E Ratio", f"{info.get('trailingPE', 'N/A')}")
col5.metric("EPS (TTM)", f"{info.get('trailingEps', 'N/A')}")
roe = info.get('returnOnEquity')
col6.metric("ROE", f"{roe * 100:.2f}%" if roe else "N/A")

col7, col8, col9 = st.columns(3)
col7.metric("Debt/Equity", f"{info.get('debtToEquity', 'N/A')}")
col8.metric("P/B Ratio", f"{info.get('priceToBook', 'N/A')}")
col9.metric("Market Cap", f"${info.get('marketCap', 0):,.0f}")

# Insights
st.subheader("💡 Investment Insights")
if 'RSI' in indicators and 'RSI' in data:
    latest_rsi = data['RSI'].iloc[-1]
    if latest_rsi > 70:
        st.warning("RSI indicates the stock is overbought – Consider waiting.")
    elif latest_rsi < 30:
        st.success("RSI indicates oversold – Possible buying opportunity.")
    else:
        st.info("RSI is neutral.")

if 'MACD' in indicators and data.get('MACD') is not None:
    macd_curr = data['MACD'].iloc[-1]
    signal_curr = data['Signal_Line'].iloc[-1]
    if macd_curr > signal_curr:
        st.success("MACD crossover: Bullish signal.")
    elif macd_curr < signal_curr:
        st.warning("MACD crossover: Bearish signal.")
    else:
        st.info("MACD is neutral.")

# News sentiment
st.subheader("🗞 News Sentiment Analysis")
try:
    news = ticker_obj.news
    if news:
        for item in news[:5]:
            title = item['title']
            sentiment = TextBlob(title).sentiment.polarity
            if sentiment > 0.1:
                st.success(f"🔼 {title}")
            elif sentiment < -0.1:
                st.error(f"🔻 {title}")
            else:
                st.info(f"➖ {title}")
    else:
        st.write("No recent news available.")
except:
    st.warning("Sentiment analysis not available.")

# Raw data
with st.expander("📋 View Raw Data"):
    st.dataframe(data.tail(100))

# Footer
st.markdown("---")
st.markdown("<div style='text-align:center; color:gray;'>Made by Team Analytics</div>", unsafe_allow_html=True)
