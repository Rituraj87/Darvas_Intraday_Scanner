import streamlit as st
import pandas as pd
import yfinance as yf
import pandas_ta as ta
import requests
import io

# --- 1. पेज सेटअप ---
st.set_page_config(
    page_title="Pro Intraday Advisor",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. CSS (Day/Night Adaptive & 3D Cards) ---
st.markdown("""
<style>
    /* 3D Adaptive Cards */
    .metric-card {
        background-color: var(--secondary-background-color); /* Auto adapts to theme */
        border: 1px solid var(--text-color);
        border-radius: 15px;
        padding: 20px;
        box-shadow: 4px 4px 10px rgba(0,0,0,0.3);
        text-align: center;
        margin-bottom: 20px;
        transition: transform 0.2s;
    }
    .metric-card:hover {
        transform: scale(1.02);
    }
    .card-title {
        font-size: 1.1rem;
        font-weight: 600;
        color: var(--text-color); /* Auto text color */
        opacity: 0.8;
    }
    .card-value-green {
        color: #00FF7F;
        font-size: 2.2rem;
        font-weight: 900;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.5);
    }
    .card-value-red {
        color: #FF4B4B;
        font-size: 2.2rem;
        font-weight: 900;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.5);
    }
    
    /* Advisor Note Box */
    .advisor-box {
        background-color: rgba(255, 255, 0, 0.1);
        border-left: 5px solid #FFD700;
        padding: 15px;
        margin-bottom: 20px;
        border-radius: 5px;
    }
    .advisor-text {
        font-size: 14px;
        line-height: 1.6;
        color: var(--text-color);
    }
    
    /* Authentic Button */
    .stButton>button {
        width: 100%;
        height: 55px;
        font-size: 20px;
        font-weight: bold;
        border-radius: 12px;
        background: linear-gradient(90deg, #1E90FF, #00BFFF);
        color: white;
        border: none;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
</style>
""", unsafe_allow_html=True)

# --- 3. ऑथेंटिकेशन ---
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False

    if not st.session_state["password_correct"]:
        st.markdown("<h2 style='text-align: center;'>🔐 ACCESS PROTOCOL</h2>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            pwd = st.text_input("Enter Authentic Code:", type="password")
            if st.button("AUTHENTICATE"):
                if pwd == "Raipur@2026":
                    st.session_state["password_correct"] = True
                    st.rerun()
                else:
                    st.error("Access Denied. Incorrect Credentials.")
        return False
    return True

# --- 4. डेटा और लॉजिक ---
@st.cache_data
def get_nifty_tickers():
    try:
        # Nifty 100 for speed, change url to nifty500list.csv for all
        url = "https://www.niftyindices.com/IndexConstituent/ind_nifty100list.csv"
        headers = {'User-Agent': 'Mozilla/5.0'}
        s = requests.get(url, headers=headers).content
        df = pd.read_csv(io.StringIO(s.decode('utf-8')))
        return [f"{x}.NS" for x in df['Symbol'].tolist()]
    except:
        return ['RELIANCE.NS', 'TATASTEEL.NS', 'HDFCBANK.NS', 'SBIN.NS', 'INFY.NS', 'ICICIBANK.NS']

def calculate_technicals(df):
    df['RSI'] = ta.rsi(df['Close'], length=14)
    df['EMA_9'] = ta.ema(df['Close'], length=9)
    df['EMA_21'] = ta.ema(df['Close'], length=21)
    df.ta.vwap(append=True) # Adds VWAP_D
    return df

# --- MAIN APP ---
if check_password():
    
    # 1. Advisor Notification (लंबा-चौड़ा नोट)
    st.markdown("""
    <div class="advisor-box">
        <h3>📢 AI TRADING ADVISOR NOTE (PLEASE READ)</h3>
        <div class="advisor-text">
            <b>1. Trend is King:</b> कभी भी मार्केट के ट्रेंड के खिलाफ ट्रेड न करें। अगर 'Strong Sell' है, तो गलती से भी Buy न करें।<br>
            <b>2. Capital Protection:</b> इंट्राडे में अपनी कुल पूंजी का केवल 20% उपयोग करें। <br>
            <b>3. Stop Loss (SL):</b> यह एप्प आपको SL सुझाव देता है। इसे भगवान की लकीर मानें। <b>SL हिट हो तो तुरंत एग्जिट करें, उम्मीद में न बैठें।</b><br>
            <b>4. Overtrading:</b> दिन में 2 या 3 अच्छे ट्रेड ही काफी हैं। जबरदस्ती हर सिग्नल पर ट्रेड न लें।<br>
            <b>5. Confirmation:</b> "Strong Buy/Sell" का मतलब है कि Open=Low/High के साथ-साथ RSI और EMA भी सपोर्ट कर रहे हैं। यही सबसे सुरक्षित ट्रेड हैं।<br>
            <b>6. Volatility:</b> 9:15 AM से 9:30 AM तक बाजार बहुत अस्थिर रहता है। नए लोग 9:30 के बाद ही एंट्री लें।
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 2. कंट्रोल पैनल
    col_ctrl1, col_ctrl2 = st.columns([3, 1])
    with col_ctrl1:
        st.title("📊 LIVE INTRADAY SCREENER")
    with col_ctrl2:
        timeframe = st.selectbox("⏳ Candle Timeframe", ["15m", "5m", "30m", "60m"], index=0)

    # 3. स्कैन बटन
    if st.button("🚀 SCAN NIFTY MARKET"):
        
        tickers = get_nifty_tickers()
        data_rows = []
        buy_c = 0
        sell_c = 0
        
        progress_bar = st.progress(0, text="Initializing Scanner...")
        total = 30 # डेमो लिमिट (स्पीड के लिए) - इसे बढ़ाकर len(tickers) कर सकते हैं
        
        for i, ticker in enumerate(tickers[:total]):
            try:
                # डेटा डाउनलोड
                df = yf.download(ticker, period="5d", interval=timeframe, progress=False)
                
                if len(df) > 20:
                    if isinstance(df.columns, pd.MultiIndex):
                        df.columns = df.columns.get_level_values(0)
                    
                    df = calculate_technicals(df)
                    curr = df.iloc[-1]
                    
                    # वेरिएबल्स
                    c = curr['Close']
                    o = curr['Open']
                    h = curr['High']
                    l = curr['Low']
                    rsi = curr['RSI']
                    vwap = curr.get('VWAP_D', c) # fallback to C if VWAP fails
                    ema9 = curr['EMA_9']
                    ema21 = curr['EMA_21']
                    
                    # लॉजिक
                    status = "AVOID" # डिफॉल्ट
                    entry = 0.0
                    target = 0.0
                    sl = 0.0
                    
                    # कंडीशन
                    open_low = abs(o - l) <= (o * 0.001)
                    open_high = abs(o - h) <= (o * 0.001)
                    bullish = (rsi > 50) and (c > vwap) and (ema9 > ema21)
                    bearish = (rsi < 50) and (c < vwap) and (ema9 < ema21)
                    
                    if open_low:
                        if bullish:
                            status = "STRONG BUY"
                            buy_c += 1
                        else:
                            status = "BUY (Weak)"
                        entry = o
                        sl = o * 0.99
                        target = o * 1.02
                        
                    elif open_high:
                        if bearish:
                            status = "STRONG SELL"
                            sell_c += 1
                        else:
                            status = "SELL (Weak)"
                        entry = o
                        sl = o * 1.01
                        target = o * 0.98
                    
                    else:
                        # AVOID केस में भी CMP दिखाएंगे, लेकिन Entry/Target खाली रखेंगे
                        status = "AVOID"
                        entry = 0.0 
                        target = 0.0
                        sl = 0.0
                    
                    # डेटा लिस्ट में जोड़ें (Column Order: Stock, Status, CMP, Entry, Target, SL...)
                    data_rows.append({
                        "Stock": ticker.replace('.NS', ''),
                        "Status": status,
                        "CMP": c,
                        "Entry": entry if entry > 0 else None, # None means cell will be empty
                        "Target": target if target > 0 else None,
                        "Stop Loss": sl if sl > 0 else None,
                        "RSI": rsi,
                        "EMA Cross": "Yes" if ema9 > ema21 else "No"
                    })
                    
            except Exception as e:
                pass
            
            progress_bar.progress((i+1)/total)
            
        progress_bar.empty()
        
        # सेशन स्टेट में सेव करें
        st.session_state['data'] = pd.DataFrame(data_rows)
        st.session_state['buy_count'] = buy_c
        st.session_state['sell_count'] = sell_c

    # 4. परिणाम (Results)
    if 'data' in st.session_state and not st.session_state['data'].empty:
        
        # --- टॉप कार्ड्स (3D) ---
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="card-title">🚀 STRONG BUY OPPORTUNITIES</div>
                <div class="card-value-green">{st.session_state['buy_count']}</div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="card-title">🩸 STRONG SELL SIGNALS</div>
                <div class="card-value-red">{st.session_state['sell_count']}</div>
            </div>
            """, unsafe_allow_html=True)
        
        # --- मेन टेबल ---
        df = st.session_state['data']
        
        # स्टाइलिंग फंक्शन
        def color_status(val):
            color = 'var(--text-color)' # Default adaptive color
            weight = 'normal'
            if 'STRONG BUY' in str(val):
                color = '#00FF00'
                weight = 'bold'
            elif 'STRONG SELL' in str(val):
                color = '#FF0000'
                weight = 'bold'
            elif 'AVOID' in str(val):
                color = 'gray' # Neutral gray for Avoid
            return f'color: {color}; font-weight: {weight}'

        # Dataframe दिखाना (Pinned Columns के साथ)
        st.dataframe(
            df.style.map(color_status, subset=['Status']),
            use_container_width=True,
            height=600,
            hide_index=True, # सीरियल नंबर हटा दिया
            column_config={
                "Stock": st.column_config.TextColumn("Stock Name", pinned=True), # PINNED
                "Status": st.column_config.TextColumn("Signal", pinned=True, width="medium"), # PINNED
                "CMP": st.column_config.NumberColumn("CMP (₹)", format="%.2f"),
                "Entry": st.column_config.NumberColumn("Entry Price", format="%.2f"), # RE-ADDED
                "Target": st.column_config.NumberColumn("Target (2%)", format="%.2f"), # RE-ADDED
                "Stop Loss": st.column_config.NumberColumn("Stop Loss", format="%.2f"),
                "RSI": st.column_config.NumberColumn("RSI", format="%.2f"),
            }
        )
    else:
        st.info("👆 ऊपर 'SCAN NIFTY MARKET' बटन दबाकर स्कैन शुरू करें।")

