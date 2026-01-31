import streamlit as st
import pandas as pd
import yfinance as yf
import requests
import io
import numpy as np
from datetime import datetime
import pytz

# --- 1. पेज सेटअप (Mobile Friendly) ---
st.set_page_config(
    page_title="Pro Trader Scanner",
    layout="wide",
    initial_sidebar_state="collapsed" # मोबाइल पर साइडबार बंद रहेगा
)

# --- 2. कस्टम CSS (मोबाइल व्यू को सुंदर बनाने के लिए) ---
st.markdown("""
    <style>
    .metric-card {
        background-color: #f0f2f6;
        border-left: 5px solid #ff4b4b;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
    }
    .stButton>button {
        width: 100%;
        background-color: #0068c9;
        color: white;
        height: 3em;
        font-size: 20px;
        border-radius: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. पासवर्ड सिस्टम ---
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False
    
    if not st.session_state["password_correct"]:
        pwd = st.text_input("🔑 ऑथेंटिक पासवर्ड दर्ज करें:", type="password")
        if pwd == "Raipur@2026":
            st.session_state["password_correct"] = True
            st.rerun()
        elif pwd:
            st.error("पासवर्ड गलत है।")
        return False
    return True

# --- 4. इंडिकेटर कैलकुलेशन (Advanced Logic) ---
def calculate_indicators(df):
    # RSI (Relative Strength Index)
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # EMA (Exponential Moving Average - 20 Period)
    df['EMA_20'] = df['Close'].ewm(span=20, adjust=False).mean()
    
    # VWAP (Volume Weighted Average Price)
    df['VWAP'] = (df['Volume'] * (df['High'] + df['Low'] + df['Close']) / 3).cumsum() / df['Volume'].cumsum()
    
    return df

# --- 5. मुख्य ऐप ---
if check_password():
    
    # --- हेडर और टाइम नोटिफिकेशन ---
    ist = pytz.timezone('Asia/Kolkata')
    current_time = datetime.now(ist)
    current_hour = current_time.hour
    
    # नोटिफिकेशन लॉजिक
    time_msg = ""
    rec_timeframe = "15m"
    if current_hour < 10:
        time_msg = "⚠️ बाजार अभी खुला है (Volatile)। 15 मिनट टाइमफ्रेम सुरक्षित है।"
        rec_timeframe = "15m"
    elif current_hour >= 14: # 2 बजे के बाद
        time_msg = "⚠️ बाजार बंद होने वाला है। इंट्राडे पोजीशन स्क्वायर-ऑफ करें।"
        rec_timeframe = "5m"
    else:
        time_msg = "✅ बाजार स्थिर है। आप 5 या 15 मिनट दोनों का उपयोग कर सकते हैं।"
        rec_timeframe = "15m"

    st.info(f"{time_msg} | अनुशंसित टाइमफ्रेम: **{rec_timeframe}**")

    # --- इनपुट्स ---
    col_tf, col_blank = st.columns([1, 2])
    with col_tf:
        timeframe = st.selectbox("टाइमफ्रेम चुनें:", ["5m", "15m", "30m"], index=1)

    # --- खाली स्थान होल्डर्स (Placeholders for Cards) ---
    # हम इन्हें बाद में भरेंगे जब स्कैन पूरा होगा
    metrics_container = st.container()

    # --- स्कैनर बटन (बीच में) ---
    col_l, col_btn, col_r = st.columns([1, 2, 1])
    with col_btn:
        start_scan = st.button(f"🔍 START PRO SCANNER ({timeframe})")

    # --- स्कैनिंग लॉजिक ---
    if start_scan:
        st.write("बाजार का विश्लेषण चल रहा है... कृपया प्रतीक्षा करें...")
        
        # Nifty 50 tickers (डेमो के लिए 50, स्पीड के लिए)
        # आप इसे पूरा Nifty 500 कर सकते हैं
        try:
            url = "https://www.niftyindices.com/IndexConstituent/ind_nifty50list.csv"
            headers = {'User-Agent': 'Mozilla/5.0'}
            s = requests.get(url, headers=headers).content
            df_nifty = pd.read_csv(io.StringIO(s.decode('utf-8')))
            tickers = [f"{x}.NS" for x in df_nifty['Symbol'].tolist()]
        except:
            tickers = ['RELIANCE.NS', 'TATASTEEL.NS', 'HDFCBANK.NS', 'INFY.NS', 'SBIN.NS']

        results = []
        buy_count = 0
        sell_count = 0
        
        progress_bar = st.progress(0)
        
        for i, ticker in enumerate(tickers):
            try:
                # डेटा लाएं (RSI/EMA के लिए कम से कम 5 दिन का डेटा चाहिए)
                df = yf.download(ticker, period="5d", interval=timeframe, progress=False)
                
                if len(df) > 20:
                    # Multi-index fix
                    if isinstance(df.columns, pd.MultiIndex):
                        df.columns = df.columns.get_level_values(0)
                    
                    # इंडिकेटर लगाएं
                    df = calculate_indicators(df)
                    curr = df.iloc[-1]
                    
                    # वेरिएबल्स
                    o = curr['Open']
                    h = curr['High']
                    l = curr['Low']
                    c = curr['Close']
                    rsi = curr['RSI']
                    vwap = curr['VWAP']
                    ema = curr['EMA_20']
                    
                    # --- CORE STRATEGY ---
                    signal = "AVOID"
                    status = "Weak"
                    
                    # BUY: Open=Low AND Price > VWAP (Trend Confirmation)
                    if abs(o - l) <= (o * 0.001):
                        if c > vwap and rsi > 50:
                            signal = "STRONG BUY"
                            buy_count += 1
                            status = "Strong Bullish"
                        elif c > vwap:
                            signal = "BUY" # थोड़ा कमजोर
                        
                    # SELL: Open=High AND Price < VWAP
                    elif abs(o - h) <= (o * 0.001):
                        if c < vwap and rsi < 50:
                            signal = "STRONG SELL"
                            sell_count += 1
                            status = "Strong Bearish"
                        elif c < vwap:
                            signal = "SELL"

                    if "BUY" in signal or "SELL" in signal:
                        results.append({
                            "Stock": ticker.replace('.NS', ''),
                            "Action": signal,
                            "Price": round(c, 2),
                            "RSI": round(rsi, 1),
                            "VWAP check": "Above" if c > vwap else "Below",
                            "Stop Loss": round(l if "BUY" in signal else h, 2),
                            "Target": round(c * 1.015 if "BUY" in signal else c * 0.985, 2)
                        })
            except Exception as e:
                pass
            
            progress_bar.progress((i + 1) / len(tickers))

        # --- रिजल्ट दिखाना ---
        
        # 1. टॉप कार्ड्स अपडेट (Top Cards)
        with metrics_container:
            m1, m2, m3 = st.columns(3)
            m1.metric("Strong Buy Signals", buy_count, delta=f"{buy_count} stocks")
            m2.metric("Strong Sell Signals", sell_count, delta=f"-{sell_count} stocks", delta_color="inverse")
            m3.metric("Total Scanned", len(tickers))
        
        # 2. डेटा टेबल (Data Table)
        if results:
            st.success(f"{len(results)} ट्रेड अवसर मिले!")
            df_res = pd.DataFrame(results)
            
            # Index सेट करें ताकि वह 'Pin' हो जाए
            df_res.set_index("Stock", inplace=True)
            
            st.dataframe(
                df_res,
                height=500,
                use_container_width=True,
                column_config={
                    "Action": st.column_config.TextColumn(
                        "Signal",
                        help="Strong Buy/Sell based on OHL + RSI + VWAP",
                    ),
                    "RSI": st.column_config.NumberColumn(
                        "RSI (Momentum)",
                        format="%.1f",
                        help="Above 50 is Bullish, Below 50 is Bearish"
                    ),
                    "VWAP check": st.column_config.TextColumn(
                        "Trend (VWAP)",
                        help="Price vs Institutional Avg Price"
                    )
                }
            )
        else:
            st.warning("कोई भी स्टॉक आपकी स्ट्रैटेजी (OHL + RSI + VWAP) से मैच नहीं कर रहा है।")
            
