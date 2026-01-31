import streamlit as st
import pandas as pd
import yfinance as yf
import pandas_ta as ta
import requests
import io

# --- 1. पेज सेटअप (मोबाइल फ्रेंडली) ---
st.set_page_config(
    page_title="Pro Trader AI Scanner",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. कस्टम CSS (3D कार्ड्स और मोबाइल UI के लिए) ---
st.markdown("""
<style>
    /* 3D Cards Design */
    .metric-card {
        background: linear-gradient(135deg, #ffffff 0%, #f0f2f6 100%);
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 10px 20px rgba(0,0,0,0.15), 0 6px 6px rgba(0,0,0,0.10);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        text-align: center;
        border: 1px solid #e0e0e0;
        margin-bottom: 15px;
    }
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 15px 30px rgba(0,0,0,0.25);
    }
    .card-title {
        color: #555;
        font-size: 1.2rem;
        font-weight: 600;
        margin-bottom: 10px;
    }
    .card-value-green {
        color: #00cc66;
        font-size: 2.5rem;
        font-weight: 800;
    }
    .card-value-red {
        color: #ff3333;
        font-size: 2.5rem;
        font-weight: 800;
    }
    
    /* Authentic Button Style */
    .stButton>button {
        width: 100%;
        border-radius: 10px;
        height: 50px;
        font-weight: bold;
        font-size: 18px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    /* Mobile Optimization for Table */
    .dataframe {
        font-size: 12px !important;
    }
    
    /* Dark Mode Compatibility */
    @media (prefers-color-scheme: dark) {
        .metric-card {
            background: linear-gradient(135deg, #262730 0%, #1c1c1e 100%);
            border: 1px solid #444;
        }
        .card-title { color: #ddd; }
    }
</style>
""", unsafe_allow_html=True)

# --- 3. ऑथेंटिकेशन (Authentic Login) ---
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False

    if not st.session_state["password_correct"]:
        st.markdown("<h2 style='text-align: center;'>🔒 Authentic Access System</h2>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            pwd = st.text_input("एक्सेस कोड दर्ज करें", type="password")
            if st.button("AUTHENTIC ENTRY 🔐"):
                if pwd == "Raipur@2026":
                    st.session_state["password_correct"] = True
                    st.rerun()
                else:
                    st.error("अनुमति अस्वीकृत (Access Denied)")
        return False
    return True

# --- 4. टेक्निकल इंडिकेटर्स लॉजिक ---
def calculate_technicals(df):
    # RSI (14)
    df['RSI'] = ta.rsi(df['Close'], length=14)
    
    # EMA Crossover (9 & 21)
    df['EMA_9'] = ta.ema(df['Close'], length=9)
    df['EMA_21'] = ta.ema(df['Close'], length=21)
    
    # VWAP
    df.ta.vwap(append=True) # Adds VWAP_D column
    
    # MACD
    macd = ta.macd(df['Close'])
    df = pd.concat([df, macd], axis=1) # MACD_12_26_9, MACDh, MACDs
    
    return df

# --- 5. डेटा डाउनलोडर ---
@st.cache_data
def get_nifty_tickers():
    try:
        # स्पीड के लिए अभी Nifty 100 ले रहे हैं, आप 500 कर सकते हैं
        url = "https://www.niftyindices.com/IndexConstituent/ind_nifty100list.csv"
        headers = {'User-Agent': 'Mozilla/5.0'}
        s = requests.get(url, headers=headers).content
        df = pd.read_csv(io.StringIO(s.decode('utf-8')))
        return [f"{x}.NS" for x in df['Symbol'].tolist()]
    except:
        return ['RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'SBIN.NS', 'INFY.NS']

# --- MAIN APP ---
if check_password():
    
    # --- हेडर और सेटिंग्स ---
    st.markdown("<h1 style='text-align: center;'>📊 Advance Intraday Hunter</h1>", unsafe_allow_html=True)
    
    # टाइमफ्रेम सेलेक्शन (नोटिफिकेशन के साथ)
    col_t1, col_t2 = st.columns([3, 1])
    with col_t1:
        st.info("💡 **ट्रेडिंग टिप:** इंट्राडे के लिए 15 मिनट (15m) सबसे सुरक्षित टाइमफ्रेम है। 5 मिनट (5m) केवल स्कैल्पिंग के लिए उपयोग करें।")
    with col_t2:
        timeframe = st.selectbox("⏳ Timeframe", ["15m", "5m", "30m", "1h"], index=0)

    # --- स्टेट मैनेजमेंट ---
    if 'scan_results' not in st.session_state:
        st.session_state['scan_results'] = None
    if 'buy_count' not in st.session_state:
        st.session_state['buy_count'] = 0
    if 'sell_count' not in st.session_state:
        st.session_state['sell_count'] = 0

    # --- स्कैनर बटन (CENTERED) ---
    col_b1, col_b2, col_b3 = st.columns([1, 2, 1])
    with col_b2:
        scan_btn = st.button("🔍 START PRO SCANNING", type="primary")

    # --- स्कैनिंग लॉजिक ---
    if scan_btn:
        tickers = get_nifty_tickers()
        data_rows = []
        buy_c = 0
        sell_c = 0
        
        progress_text = "Analyzing Stocks with RSI, MACD & VWAP..."
        my_bar = st.progress(0, text=progress_text)
        
        # डेमो के लिए लिमिट (स्पीड के लिए)
        limit = 30 
        
        for i, ticker in enumerate(tickers[:limit]):
            try:
                # ज्यादा डेटा चाहिए इंडिकेटर्स के लिए (period=5d)
                df = yf.download(ticker, period="5d", interval=timeframe, progress=False)
                
                if len(df) > 20: # कम से कम 20 कैंडल्स चाहिए
                    if isinstance(df.columns, pd.MultiIndex):
                        df.columns = df.columns.get_level_values(0)
                        
                    # इंडिकेटर्स कैलकुलेट करें
                    df = calculate_technicals(df)
                    
                    curr = df.iloc[-1]
                    prev = df.iloc[-2]
                    
                    # बेसिक डेटा
                    o = curr['Open']
                    h = curr['High']
                    l = curr['Low']
                    c = curr['Close']
                    rsi = curr['RSI']
                    vwap = curr.get('VWAP_D', 0)
                    ema9 = curr['EMA_9']
                    ema21 = curr['EMA_21']
                    
                    # सिग्नल लॉजिक
                    signal = "WAIT"
                    action_color = "grey"
                    
                    # 1. Open High Low Strategy
                    is_open_low = abs(o - l) <= (o * 0.001)
                    is_open_high = abs(o - h) <= (o * 0.001)
                    
                    # 2. Advanced Confirmation
                    bullish_conf = (rsi > 50) and (c > vwap) and (ema9 > ema21)
                    bearish_conf = (rsi < 50) and (c < vwap) and (ema9 < ema21)
                    
                    if is_open_low:
                        if bullish_conf:
                            signal = "STRONG BUY 🚀"
                            buy_c += 1
                        else:
                            signal = "BUY (Weak)"
                            
                    elif is_open_high:
                        if bearish_conf:
                            signal = "STRONG SELL 🩸"
                            sell_c += 1
                        else:
                            signal = "SELL (Weak)"

                    # केवल तभी लिस्ट में जोड़ें जब कोई सिग्नल हो
                    if "STRONG" in signal or "BUY" in signal or "SELL" in signal:
                        data_rows.append({
                            "Stock": ticker.replace('.NS', ''),
                            "Signal": signal,
                            "Price": round(c, 2),
                            "RSI": round(rsi, 1),
                            "VWAP Signal": "Bullish" if c > vwap else "Bearish",
                            "EMA Cross": "Yes" if ema9 > ema21 else "No",
                            "StopLoss": round(l, 2) if "BUY" in signal else round(h, 2)
                        })
            except Exception as e:
                pass
            
            my_bar.progress((i + 1) / limit)
            
        my_bar.empty()
        
        # परिणाम सेव करें
        st.session_state['scan_results'] = pd.DataFrame(data_rows)
        st.session_state['buy_count'] = buy_c
        st.session_state['sell_count'] = sell_c

    # --- 6. डैशबोर्ड UI (परिणाम दिखाना) ---
    
    # 3D कार्ड्स (Result आने के बाद अपडेट होंगे)
    st.write("---")
    col_card1, col_card2 = st.columns(2)
    
    with col_card1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="card-title">🚀 STRONG BUY SIGNALS</div>
            <div class="card-value-green">{st.session_state['buy_count']}</div>
            <p>Stocks ready to fly</p>
        </div>
        """, unsafe_allow_html=True)
        
    with col_card2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="card-title">🩸 STRONG SELL SIGNALS</div>
            <div class="card-value-red">{st.session_state['sell_count']}</div>
            <p>Stocks ready to fall</p>
        </div>
        """, unsafe_allow_html=True)

    # रिजल्ट टेबल
    if st.session_state['scan_results'] is not None and not st.session_state['scan_results'].empty:
        st.subheader("📋 Live Market Signals")
        
        df_res = st.session_state['scan_results']
        
        # स्टाइलिंग: कलर कोडिंग
        def highlight_signal(val):
            color = 'black'
            weight = 'normal'
            if 'STRONG BUY' in val:
                color = '#00cc66' # Green
                weight = 'bold'
            elif 'STRONG SELL' in val:
                color = '#ff3333' # Red
                weight = 'bold'
            return f'color: {color}; font-weight: {weight}'
            
        # डेटाफ्रेम कॉन्फ़िगरेशन (पिन पॉइंट कॉलम)
        st.dataframe(
            df_res.style.map(highlight_signal, subset=['Signal']),
            use_container_width=True,
            height=500,
            column_config={
                "Stock": st.column_config.TextColumn("Stock Name", pinned=True), # PINNED HERE
                "Signal": st.column_config.TextColumn("Trade Action"),
                "RSI": st.column_config.NumberColumn("RSI (14)", help="Over 60 is Strong, Under 40 is Weak"),
                "Price": st.column_config.NumberColumn("CMP", format="₹ %.2f"),
                "StopLoss": st.column_config.NumberColumn("SL Suggestion", format="₹ %.2f"),
            }
        )
    elif scan_btn:
        st.warning("No Strong Signals found in current scan.")
        
