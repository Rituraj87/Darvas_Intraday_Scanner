import streamlit as st
import pandas as pd
import yfinance as yf
import pandas_ta as ta
import requests
import io

# --- 1. पेज कॉन्फ़िगरेशन ---
st.set_page_config(
    page_title="Pro Trader AI Terminal",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. एडवांस CSS (3D कार्ड्स और मोबाइल पिनिंग के लिए) ---
st.markdown("""
<style>
    /* 3D Metric Cards */
    .metric-card {
        background: linear-gradient(145deg, #1e1e1e, #292929);
        border-radius: 15px;
        padding: 20px;
        box-shadow: 5px 5px 10px #121212, -5px -5px 10px #363636;
        text-align: center;
        border: 1px solid #444;
        margin-bottom: 15px;
        color: white;
    }
    .card-title { font-size: 1.1rem; color: #aaaaaa; margin-bottom: 5px; }
    .card-value-green { color: #00ff7f; font-size: 2.2rem; font-weight: bold; text-shadow: 0 0 10px rgba(0,255,127,0.3); }
    .card-value-red { color: #ff4d4d; font-size: 2.2rem; font-weight: bold; text-shadow: 0 0 10px rgba(255,77,77,0.3); }

    /* Authentic Button */
    .stButton>button {
        background: linear-gradient(90deg, #00C9FF 0%, #92FE9D 100%);
        color: black;
        border: none;
        border-radius: 12px;
        height: 55px;
        font-weight: 900;
        font-size: 20px;
        box-shadow: 0 4px 15px rgba(0,201,255,0.4);
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        transform: scale(1.02);
        box-shadow: 0 6px 20px rgba(0,201,255,0.6);
    }
    
    /* Advisor Box Style */
    .advisor-box {
        background-color: #f0f2f6;
        border-left: 5px solid #ff9800;
        padding: 15px;
        border-radius: 5px;
        margin-bottom: 20px;
        color: #333;
    }
    @media (prefers-color-scheme: dark) {
        .advisor-box {
            background-color: #262730;
            color: #e0e0e0;
        }
    }
</style>
""", unsafe_allow_html=True)

# --- 3. ऑथेंटिकेशन ---
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False

    if not st.session_state["password_correct"]:
        st.markdown("<br><br><h1 style='text-align: center;'>🔐 Secure Terminal Access</h1>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            pwd = st.text_input("Enter Authentic Password:", type="password")
            if st.button("UNLOCK SYSTEM 🔓"):
                if pwd == "Raipur@2026":
                    st.session_state["password_correct"] = True
                    st.rerun()
                else:
                    st.error("❌ Access Denied! Incorrect Credentials.")
        return False
    return True

# --- 4. स्मार्ट एडवाइजर फंक्शन (लंबा नोटिफिकेशन) ---
def show_smart_advisor():
    st.markdown("""
    <div class="advisor-box">
        <h3>📢 AI Trading Advisor (Intraday Strategy)</h3>
        <p><strong>ध्यान दें (Critical Advice):</strong></p>
        <ul>
            <li>✅ <strong>Timeframe Rule:</strong> मार्केट खुलने के बाद पहले 15 मिनट (9:15-9:30) ट्रेड न करें। 9:30 के बाद जब यह स्कैनर सिग्नल दे, तभी एंट्री लें।</li>
            <li>✅ <strong>Open High/Low Logic:</strong>
                <ul>
                    <li>अगर <strong>Strong Buy</strong> है: इसका मतलब है Open = Low (खरीदार हावी हैं)।</li>
                    <li>अगर <strong>Strong Sell</strong> है: इसका मतलब है Open = High (बिकवाली हावी है)।</li>
                </ul>
            </li>
            <li>✅ <strong>Risk Management:</strong> हर ट्रेड में अपने कैपिटल का सिर्फ 2% रिस्क लें। <strong>Stop Loss (SL)</strong> लगाना अनिवार्य है। अगर प्राइस SL के पास आए, तो दया न करें, तुरंत एग्जिट करें।</li>
            <li>✅ <strong>Profit Booking:</strong> जैसे ही आपको 1:2 का रिस्क-रिवार्ड मिले (यानी ₹1 के रिस्क पर ₹2 का प्रॉफिट), अपना 50% प्रॉफिट बुक करें और बाकी का SL एंट्री प्राइस पर ले आएं।</li>
            <li>⚠️ <strong>Fake Breakouts:</strong> अगर RSI 40 और 60 के बीच में है, तो मार्केट साइडवेज है। ऐसे में 'Avoid' वाले सिग्नल्स को इग्नोर करें।</li>
        </ul>
        <hr style="border-top: 1px solid #bbb;">
        <small><i>System Status: All indicators (RSI, VWAP, EMA, Volume) are active. Good Luck!</i></small>
    </div>
    """, unsafe_allow_html=True)

# --- 5. डेटा और लॉजिक ---
@st.cache_data
def get_nifty_tickers():
    try:
        url = "https://www.niftyindices.com/IndexConstituent/ind_nifty100list.csv"
        headers = {'User-Agent': 'Mozilla/5.0'}
        s = requests.get(url, headers=headers).content
        df = pd.read_csv(io.StringIO(s.decode('utf-8')))
        return [f"{x}.NS" for x in df['Symbol'].tolist()]
    except:
        return ['RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'SBIN.NS', 'INFY.NS', 'TATAMOTORS.NS']

def calculate_technicals(df):
    df['RSI'] = ta.rsi(df['Close'], length=14)
    df['EMA_9'] = ta.ema(df['Close'], length=9)
    df['EMA_21'] = ta.ema(df['Close'], length=21)
    df.ta.vwap(append=True)
    return df

# --- MAIN APP ---
if check_password():
    
    # Header area
    show_smart_advisor()
    
    # Controls
    col_ctrl1, col_ctrl2 = st.columns([1, 4])
    with col_ctrl1:
        timeframe = st.selectbox("Timeframe", ["15m", "30m", "1h", "5m"], index=0)
    
    # Scanning Logic
    if 'scan_data' not in st.session_state:
        st.session_state['scan_data'] = None

    if st.button("⚡ SCAN MARKET NOW", type="primary"):
        tickers = get_nifty_tickers()
        results = []
        buy_count = 0
        sell_count = 0
        
        progress_bar = st.progress(0, text="AI scanning market data...")
        limit = 40 # Demo limit for speed
        
        for i, ticker in enumerate(tickers[:limit]):
            try:
                df = yf.download(ticker, period="5d", interval=timeframe, progress=False)
                if len(df) > 20:
                    if isinstance(df.columns, pd.MultiIndex):
                        df.columns = df.columns.get_level_values(0)
                        
                    df = calculate_technicals(df)
                    curr = df.iloc[-1]
                    
                    o = curr['Open']
                    h = curr['High']
                    l = curr['Low']
                    c = curr['Close']
                    rsi = curr['RSI']
                    vwap = curr.get('VWAP_D', o)
                    
                    # Logic
                    signal = "AVOID"  # Default
                    action = "Neutral"
                    entry_price = 0.0
                    target_price = 0.0
                    stop_loss = 0.0
                    
                    # OHL Strategy
                    is_open_low = abs(o - l) <= (o * 0.0015)
                    is_open_high = abs(o - h) <= (o * 0.0015)
                    
                    # Buy Logic
                    if is_open_low:
                        if c > vwap and rsi > 50:
                            signal = "STRONG BUY"
                            action = "BUY"
                            buy_count += 1
                            entry_price = o
                            stop_loss = o * 0.99  # 1% SL
                            target_price = o * 1.02 # 2% Target
                        else:
                            signal = "WEAK BUY"
                            
                    # Sell Logic
                    elif is_open_high:
                        if c < vwap and rsi < 50:
                            signal = "STRONG SELL"
                            action = "SELL"
                            sell_count += 1
                            entry_price = o
                            stop_loss = o * 1.01
                            target_price = o * 0.98
                    
                    # Append Data
                    results.append({
                        "Stock": ticker.replace('.NS', ''),
                        "Status": signal, # Renamed for clarity
                        "CMP": c,
                        "Entry": entry_price if entry_price > 0 else None,
                        "Target": target_price if target_price > 0 else None,
                        "Stop Loss": stop_loss if stop_loss > 0 else None,
                        "RSI": rsi,
                        "VWAP Ref": vwap
                    })
            except:
                pass
            progress_bar.progress((i+1)/limit)
            
        progress_bar.empty()
        st.session_state['scan_data'] = pd.DataFrame(results)
        st.session_state['b_count'] = buy_count
        st.session_state['s_count'] = sell_count

    # --- RESULT DISPLAY ---
    if st.session_state['scan_data'] is not None:
        df = st.session_state['scan_data']
        
        # 1. 3D Cards
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"""<div class="metric-card"><div class="card-title">BUY SIGNALS</div><div class="card-value-green">{st.session_state.get('b_count',0)}</div></div>""", unsafe_allow_html=True)
        with col2:
            st.markdown(f"""<div class="metric-card"><div class="card-title">SELL SIGNALS</div><div class="card-value-red">{st.session_state.get('s_count',0)}</div></div>""", unsafe_allow_html=True)

        # 2. Styling the DataFrame (Background Color Logic)
        def highlight_status(val):
            if val == 'STRONG BUY':
                return 'background-color: #004d00; color: #ffffff; font-weight: bold;' # Dark Green Box
            elif val == 'STRONG SELL':
                return 'background-color: #800000; color: #ffffff; font-weight: bold;' # Dark Red Box
            elif 'WEAK' in val:
                return 'background-color: #333300; color: white;' # Yellowish
            else:
                return '' # Adaptive for Avoid (Black/White based on theme)

        # Apply styles
        styled_df = df.style.map(highlight_status, subset=['Status']) \
                            .format("{:.2f}", subset=['CMP', 'Entry', 'Target', 'Stop Loss', 'RSI', 'VWAP Ref'])

        # 3. Final Table with PINNED Columns
        st.write("### 🎯 Live Market Signals")
        st.dataframe(
            styled_df,
            height=600,
            use_container_width=True,
            column_config={
                "Stock": st.column_config.TextColumn("Stock Name", pinned=True), # PIN #1
                "Status": st.column_config.TextColumn("Action Signal", pinned=True), # PIN #2
                "CMP": st.column_config.NumberColumn("Current Price", format="₹ %.2f"),
                "Entry": st.column_config.NumberColumn("Entry Price", format="₹ %.2f"),
                "Target": st.column_config.NumberColumn("Target (2%)", format="₹ %.2f"),
                "Stop Loss": st.column_config.NumberColumn("Stop Loss (1%)", format="₹ %.2f"),
            }
                    )
        
