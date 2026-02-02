import streamlit as st
import pandas as pd
import yfinance as yf
import pandas_ta as ta
import requests
import io

# --- 1. पेज सेटअप ---
st.set_page_config(
    page_title="Pro Trader AI Terminal",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. Advance CSS (3D Cards + Day/Night Visibility + Pinning Fixes) ---
st.markdown("""
<style>
    /* 3D Glassmorphism Cards */
    .metric-card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border-radius: 20px;
        padding: 20px;
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
        border: 1px solid rgba(255, 255, 255, 0.18);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        text-align: center;
        margin-bottom: 20px;
    }
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 40px rgba(0,0,0,0.4);
    }
    
    /* Day Mode Specifics */
    @media (prefers-color-scheme: light) {
        .metric-card {
            background: linear-gradient(145deg, #ffffff, #e6e6e6);
            box-shadow: 5px 5px 10px #d9d9d9, -5px -5px 10px #ffffff;
            color: #333;
        }
        .stock-list { color: #555; }
    }

    /* Night Mode Specifics */
    @media (prefers-color-scheme: dark) {
        .metric-card {
            background: linear-gradient(145deg, #1e1e1e, #2d2d2d);
            box-shadow: 5px 5px 15px #121212, -5px -5px 15px #383838;
            color: #e0e0e0;
        }
        .stock-list { color: #ccc; }
    }

    /* Card Text Styles */
    .card-title { font-size: 1.1rem; font-weight: bold; margin-bottom: 5px; opacity: 0.8; }
    .card-count { font-size: 2.5rem; font-weight: 900; margin: 0; }
    .stock-list { font-size: 0.85rem; margin-top: 10px; font-family: monospace; overflow-wrap: break-word; }
    
    .green-text { color: #00e676; }
    .red-text { color: #ff5252; }

    /* Authentic Button */
    div.stButton > button {
        width: 100%;
        border-radius: 12px;
        height: 55px;
        background: linear-gradient(90deg, #4b6cb7 0%, #182848 100%);
        color: white;
        font-weight: bold;
        border: none;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
    div.stButton > button:hover {
        transform: scale(1.02);
        box-shadow: 0 6px 20px rgba(0,0,0,0.3);
    }

    /* Warning Box Style */
    .advisor-note {
        padding: 20px;
        border-left: 5px solid #ff9800;
        background-color: rgba(255, 152, 0, 0.1);
        border-radius: 5px;
        margin-bottom: 25px;
        font-size: 0.95rem;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. Authentication ---
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False

    if not st.session_state["password_correct"]:
        st.markdown("<br><br><h2 style='text-align: center;'>🔐 QUANTUM TRADER ACCESS</h2>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            pwd = st.text_input("ENTER SECURITY PROTOCOL", type="password")
            if st.button("AUTHENTICATE SYSTEM"):
                if pwd == "Raipur@2026":
                    st.session_state["password_correct"] = True
                    st.rerun()
                else:
                    st.error("ACCESS DENIED: INVALID CREDENTIALS")
        return False
    return True

# --- 4. Logic & Calculations ---
def calculate_technicals(df):
    try:
        df['RSI'] = ta.rsi(df['Close'], length=14)
        df['EMA_9'] = ta.ema(df['Close'], length=9)
        df['EMA_21'] = ta.ema(df['Close'], length=21)
        df.ta.vwap(append=True)
        return df
    except:
        return df

@st.cache_data
def get_nifty_tickers():
    try:
        # Nifty 100 for speed, change to 500 later if needed
        url = "https://www.niftyindices.com/IndexConstituent/ind_nifty100list.csv"
        headers = {'User-Agent': 'Mozilla/5.0'}
        s = requests.get(url, headers=headers).content
        df = pd.read_csv(io.StringIO(s.decode('utf-8')))
        return [f"{x}.NS" for x in df['Symbol'].tolist()]
    except:
        return ['RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'SBIN.NS']

# --- MAIN APP ---
if check_password():

    # --- ADVANCED NOTIFICATION / ADVISOR NOTE ---
    st.markdown("""
    <div class="advisor-note">
        <strong>⚠️ FINANCIAL ADVISOR ALERT (महत्वपूर्ण सूचना):</strong> <br>
        प्रिय ट्रेडर, यह सिस्टम केवल एक <strong>Probability Tool</strong> है। मार्केट में 100% कुछ भी निश्चित नहीं होता।
        <ul>
            <li><strong>Entry Rule:</strong> कभी भी ट्रेड लेते समय यह देखें कि मार्केट का ओवरऑल ट्रेंड (Nifty 50) क्या है। ट्रेंड के खिलाफ ट्रेड न लें।</li>
            <li><strong>Risk Management:</strong> हर ट्रेड में स्टॉप लॉस (SL) अनिवार्य है। अपनी कुल कैपिटल का 2% से ज्यादा जोखिम एक ट्रेड पर न लें।</li>
            <li><strong>Confirmation:</strong> केवल 'Open=High' या 'Open=Low' काफी नहीं है। RSI और VWAP का सपोर्ट देखें। अगर सिग्नल 'STRONG' है लेकिन RSI कमजोर है, तो ट्रेड को <strong>AVOID</strong> करें।</li>
            <li><strong>Discipline:</strong> ज्यादा लालच न करें। टारगेट हिट होते ही प्रॉफिट बुक करें या SL को ट्रेल करें।</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

    # --- Header & Controls ---
    col_head1, col_head2 = st.columns([3, 1])
    with col_head1:
        st.title("📊 Advance Intraday Scanner")
    with col_head2:
        timeframe = st.selectbox("Timeframe", ["15m", "5m", "30m", "1h"], index=0)

    # State variables
    if 'scan_df' not in st.session_state: st.session_state['scan_df'] = pd.DataFrame()
    if 'buy_list' not in st.session_state: st.session_state['buy_list'] = []
    if 'sell_list' not in st.session_state: st.session_state['sell_list'] = []

    # --- SCANNER BUTTON ---
    col_b1, col_b2, col_b3 = st.columns([1, 2, 1])
    with col_b2:
        scan_btn = st.button("🔍 START DEEP SCAN (Live Market)")

    if scan_btn:
        tickers = get_nifty_tickers()
        rows = []
        buy_names = []
        sell_names = []
        
        my_bar = st.progress(0, text="Initializing Quantum Scan...")
        limit = 30 # Demo limit
        
        for i, ticker in enumerate(tickers[:limit]):
            try:
                df = yf.download(ticker, period="5d", interval=timeframe, progress=False)
                if len(df) > 20:
                    if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
                    df = calculate_technicals(df)
                    
                    curr = df.iloc[-1]
                    o, h, l, c = curr['Open'], curr['High'], curr['Low'], curr['Close']
                    rsi = curr.get('RSI', 50)
                    vwap = curr.get('VWAP_D', c)
                    
                    # LOGIC
                    signal = "AVOID ⚪" # Default neutral visibility
                    entry = 0.0
                    target = 0.0
                    sl = 0.0
                    
                    # BUY
                    if abs(o - l) <= (o * 0.001):
                        strength = "WEAK"
                        if rsi > 55 and c > vwap: strength = "STRONG 🚀"
                        signal = f"BUY ({strength})"
                        entry = o
                        sl = o * 0.99
                        target = o * 1.015
                        if "STRONG" in strength: buy_names.append(ticker.replace('.NS',''))

                    # SELL
                    elif abs(o - h) <= (o * 0.001):
                        strength = "WEAK"
                        if rsi < 45 and c < vwap: strength = "STRONG 🩸"
                        signal = f"SELL ({strength})"
                        entry = o
                        sl = o * 1.01
                        target = o * 0.985
                        if "STRONG" in strength: sell_names.append(ticker.replace('.NS',''))

                    rows.append({
                        "Stock": ticker.replace('.NS', ''),
                        "Signal": signal,
                        "Entry Price": entry if entry > 0 else None,
                        "Target": target if target > 0 else None,
                        "Stop Loss": sl if sl > 0 else None,
                        "CMP": c,
                        "RSI": rsi
                    })
            except: pass
            my_bar.progress((i+1)/limit)
        
        my_bar.empty()
        st.session_state['scan_df'] = pd.DataFrame(rows)
        st.session_state['buy_list'] = buy_names
        st.session_state['sell_list'] = sell_names

    # --- 5. RESULT DASHBOARD ---
    
    # --- 3D CARDS SECTION ---
    st.write("### Market Momentum")
    c1, c2 = st.columns(2)
    
    # Helper to display list nicely
    b_str = ", ".join(st.session_state['buy_list']) if st.session_state['buy_list'] else "None"
    s_str = ", ".join(st.session_state['sell_list']) if st.session_state['sell_list'] else "None"

    with c1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="card-title green-text">BULLISH RADAR (STRONG BUY)</div>
            <div class="card-count green-text">{len(st.session_state['buy_list'])}</div>
            <div class="stock-list">{b_str}</div>
        </div>
        """, unsafe_allow_html=True)
        
    with c2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="card-title red-text">BEARISH RADAR (STRONG SELL)</div>
            <div class="card-count red-text">{len(st.session_state['sell_list'])}</div>
            <div class="stock-list">{s_str}</div>
        </div>
        """, unsafe_allow_html=True)

    # --- DATA TABLE ---
    if not st.session_state['scan_df'].empty:
        df_display = st.session_state['scan_df'].copy()
        
        # 1. Set Index to remove Serial Number and Pin Stock Name
        df_display.set_index("Stock", inplace=True)
        
        # 2. Color Logic for Table
        def highlight_vals(val):
            color = ''
            if 'STRONG 🚀' in str(val): color = 'background-color: #e8f5e9; color: green; font-weight: bold'
            elif 'STRONG 🩸' in str(val): color = 'background-color: #ffebee; color: red; font-weight: bold'
            elif 'AVOID' in str(val): color = 'color: #ff9800' # Orange for visibility in Day/Night
            return color

        # 3. Column Configuration (Format .00 and Pinning)
        st.dataframe(
            df_display.style.map(highlight_vals, subset=['Signal']),
            height=600,
            use_container_width=True,
            column_config={
                "Stock": st.column_config.TextColumn("Stock Name", pinned=True), # Pinned logic
                "Signal": st.column_config.TextColumn("Trade Status", width="medium"), 
                "Entry Price": st.column_config.NumberColumn("Entry (₹)", format="%.2f"),
                "Target": st.column_config.NumberColumn("Target (₹)", format="%.2f"),
                "Stop Loss": st.column_config.NumberColumn("SL (₹)", format="%.2f"),
                "CMP": st.column_config.NumberColumn("Current (₹)", format="%.2f"),
                "RSI": st.column_config.NumberColumn("RSI", format="%.1f"),
            }
        )
    elif scan_btn:
        st.info("No data matched. Market might be sideways.")
