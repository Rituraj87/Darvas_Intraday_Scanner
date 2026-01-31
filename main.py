import streamlit as st
import pandas as pd
import yfinance as yf
import requests
import io

# --- 1. पेज सेटअप (Page Config) ---
st.set_page_config(page_title="Pro Intraday Scanner", layout="wide")

# --- 2. पासवर्ड सिस्टम (Authentication) ---
def check_password():
    """Returns `True` if the user had the correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["password"] == "Admin": # आपका पासवर्ड
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # पासवर्ड को मेमोरी से हटा दें
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # अगर पासवर्ड नहीं डाला है तो इनपुट बॉक्स दिखाएं
        st.text_input(
            "कृपया ऑथेंटिक पासवर्ड दर्ज करें:", type="password", on_change=password_entered, key="password"
        )
        return False
    elif not st.session_state["password_correct"]:
        # गलत पासवर्ड
        st.text_input(
            "कृपया ऑथेंटिक पासवर्ड दर्ज करें:", type="password", on_change=password_entered, key="password"
        )
        st.error("😕 पासवर्ड गलत है। कृपया दोबारा प्रयास करें।")
        return False
    else:
        # पासवर्ड सही है
        return True

if check_password():
    # --- 3. डिस्क्लेमर (Warning Notification) ---
    st.markdown("""
        <div style="background-color: #ffcccc; padding: 15px; border-radius: 10px; border: 2px solid #ff0000; margin-bottom: 20px;">
            <h3 style="color: #990000; margin:0;">⚠️ ट्रेडिंग चेतावनी (Disclaimer)</h3>
            <p style="color: #333; font-weight: bold;">
                यह डेटा केवल लाइव मार्केट एनालिसिस के लिए है। कोई भी ट्रेड लेने से पहले अपनी खुद की रिसर्च जरूर करें। 
                बाजार जोखिमों के अधीन है। स्टॉप लॉस (SL) का सख्ती से पालन करें। 
                यह टूल Buy और Sell दोनों सिग्नल दिखाता है, दिशा (Trend) देखकर ही ट्रेड करें।
            </p>
        </div>
    """, unsafe_allow_html=True)

    st.title("📊 Nifty 500 - Live Intraday Hunter")

    # --- 4. डेटा फंक्शन (Caching का उपयोग ताकि बार-बार डाउनलोड न हो) ---
    @st.cache_data
    def get_nifty500_tickers():
        try:
            url = "https://www.niftyindices.com/IndexConstituent/ind_nifty500list.csv"
            headers = {'User-Agent': 'Mozilla/5.0'}
            s = requests.get(url, headers=headers).content
            df = pd.read_csv(io.StringIO(s.decode('utf-8')))
            tickers = [f"{x}.NS" for x in df['Symbol'].tolist()]
            return tickers
        except:
            return ['RELIANCE.NS', 'TATASTEEL.NS', 'SBIN.NS', 'HDFCBANK.NS'] # बैकअप

    # --- 5. स्कैनिंग लॉजिक ---
    def scan_market(tickers_list):
        data_rows = []
        
        # प्रोग्रेस बार
        my_bar = st.progress(0)
        total_stocks = len(tickers_list)
        
        # अभी डेमो के लिए हम सिर्फ पहले 30 स्टॉक्स स्कैन करेंगे (ताकि ऐप हैंग न हो)
        # आप इसे बढ़ाकर 'total_stocks' कर सकते हैं
        limit = 30  
        
        for i, ticker in enumerate(tickers_list[:limit]):
            try:
                df = yf.download(ticker, period="1d", interval="15m", progress=False)
                
                if len(df) > 0:
                    # Multi-index issue handling
                    if isinstance(df.columns, pd.MultiIndex):
                        df.columns = df.columns.get_level_values(0)

                    current_data = df.iloc[-1] # लेटेस्ट 15 min कैंडल
                    
                    o = round(current_data['Open'], 2)
                    h = round(current_data['High'], 2)
                    l = round(current_data['Low'], 2)
                    c = round(current_data['Close'], 2)
                    
                    # सिग्नल लॉजिक
                    signal = "AVOID"
                    color = "⬜" # White circle for neutral
                    entry = 0.0
                    sl = 0.0
                    target = 0.0
                    
                    # BUY CONDITION (Open = Low)
                    if abs(o - l) <= (o * 0.001):
                        signal = "STRONG BUY 🟢"
                        entry = o
                        sl = round(o * 0.99, 2)    # 1% SL
                        target = round(o * 1.02, 2) # 2% Target
                    
                    # SELL CONDITION (Open = High)
                    elif abs(o - h) <= (o * 0.001):
                        signal = "STRONG SELL 🔴"
                        entry = o
                        sl = round(o * 1.01, 2)    # 1% SL
                        target = round(o * 0.98, 2) # 2% Target

                    # डेटा लिस्ट में जोड़ें
                    data_rows.append({
                        "Stock Name": ticker.replace('.NS', ''),
                        "Signal": signal,
                        "CMP (Price)": c,
                        "Entry Price": entry if signal != "AVOID" else "-",
                        "Stop Loss": sl if signal != "AVOID" else "-",
                        "Target": target if signal != "AVOID" else "-"
                    })
            except:
                pass
            
            # प्रोग्रेस बार अपडेट
            my_bar.progress((i + 1) / limit)

        return pd.DataFrame(data_rows)

    # --- 6. यूजर इंटरफेस (UI) ---
    
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("🚀 SCAN MARKET NOW"):
            st.write("स्कैनिंग शुरू...")
            tickers = get_nifty500_tickers()
            result_df = scan_market(tickers)
            
            # --- 7. परिणाम दिखाना (Pinned Column Magic) ---
            st.success("स्कैन पूरा हुआ!")
            
            # स्टॉक नाम को इंडेक्स बना दें ताकि वह 'Pin' (Sticky) हो जाए
            result_df.set_index("Stock Name", inplace=True)
            
            # स्टाइलिंग के साथ टेबल दिखाएं
            st.dataframe(
                result_df,
                height=600,
                use_container_width=True,
                column_config={
                    "Signal": st.column_config.TextColumn(
                        "Trade Signal",
                        help="Green for Buy, Red for Sell",
                        width="medium"
                    ),
                    "CMP (Price)": st.column_config.NumberColumn(
                        "Current Price",
                        format="₹ %.2f"
                    ),
                }
            )
    
    with col2:
        st.info("👈 बाईं तरफ बटन दबाकर मार्केट स्कैन करें।")


