import streamlit as st
import pandas as pd
import gspread
import datetime
import plotly.express as px

# --- 1. CONFIGURATION ---
APP_LOGO_URL = "https://i.postimg.cc/8Cr6SypK/yzwb-ll-sm.png"
BG_IMAGE_URL = "https://i.postimg.cc/GmFZ4KS7/Gemini-Generated-Image-k1h11zk1h11zk1h1.png"
SHEET_ID = "1o7OO2nyqAEqRgUq5makKZKR7ZtFyeh2JcJlzXnEmsv8"

st.set_page_config(page_title="Elite Football Tracker", layout="wide", page_icon=APP_LOGO_URL)

# --- 2. CSS STYLING ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;600;900&display=swap');
    
    [data-testid="stAppViewContainer"] {{
        background-image: linear-gradient(rgba(0,0,0,0.7), rgba(0,0,0,0.7)), url("{BG_IMAGE_URL}");
        background-attachment: fixed; background-size: cover;
    }}
    
    /* Cards Design */
    .activity-card {{
        background: rgba(255,255,255,0.95); border-radius: 12px; padding: 15px; margin-bottom: 10px;
        border-left: 6px solid #ccc; color: black !important; box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }}
    .activity-card-won {{ border-left-color: #28a745 !important; }} /* Green */
    .activity-card-lost {{ border-left-color: #dc3545 !important; }} /* Red */
    .activity-card-pending {{ border-left-color: #ffc107 !important; }} /* Yellow */
    
    /* Metrics Box */
    .metric-box {{
        background: rgba(255, 255, 255, 0.9); border-radius: 10px; padding: 15px; 
        text-align: center; box-shadow: 0 2px 5px rgba(0,0,0,0.2);
    }}
    .metric-label {{ font-size: 0.8rem; color: #555; font-weight: bold; text-transform: uppercase; }}
    .metric-value {{ font-size: 1.4rem; font-weight: 900; color: #000; }}

    /* Banner */
    .comp-banner-box {{
        border-radius: 15px; padding: 20px; display: flex; align-items: center; 
        justify-content: center; margin-bottom: 30px; box-shadow: 0 10px 30px rgba(0,0,0,0.5);
        border: 2px solid rgba(255,255,255,0.4); width: 100%;
    }}
    .comp-banner-logo {{ height: 55px; margin-right: 20px; }}
    .comp-banner-text {{ margin: 0; font-size: 1.8rem; font-weight: 900; text-transform: uppercase; color: white; }}
    </style>
""", unsafe_allow_html=True)

# --- 3. CONNECTION MANAGER ---
@st.cache_data(ttl=15)
def connect_to_sheets():
    try:
        if "service_account" not in st.secrets:
            return None, None, 5000.0, "Missing Secrets"
            
        gc = gspread.service_account_from_dict(st.secrets["service_account"])
        
        try:
            sh = gc.open_by_key(SHEET_ID)
        except Exception as e:
            return None, None, 5000.0, f"Cannot open Sheet. Check permissions. Error: {e}"

        worksheet = sh.get_worksheet(0)
        
        try:
            data = worksheet.get_all_records()
        except:
            data = [] 
            
        try:
            val = worksheet.cell(1, 10).value # תא J1 - בנקרול התחלתי
            bankroll = float(str(val).replace(',', '')) if val else 5000.0
        except:
            bankroll = 5000.0
            
        return data, worksheet, bankroll, None
        
    except Exception as e:
        return None, None, 5000.0, str(e)

raw_data, worksheet, initial_bankroll, error_msg = connect_to_sheets()

# --- 4. LOGIC ENGINE ---
def process_data(raw):
    if not raw: return pd.DataFrame(), {"Brighton": 30.0, "Africa Cup of Nations": 30.0}
    
    processed = []
    cycles = {"Brighton": 0.0, "Africa Cup of Nations": 0.0}
    next_bets = {"Brighton": 30.0, "Africa Cup of Nations": 30.0}
    
    for i, row in enumerate(raw):
        if not isinstance(row, dict): continue
        
        try:
            comp = str(row.get('Competition', 'Brighton')).strip()
            if not comp: comp = 'Brighton'
            
            home = str(row.get('Home Team', '')).strip()
            away = str(row.get('Away Team', '')).strip()
            match = f"{home} vs {away}"
            
            try: odds = float(str(row.get('Odds', 1)).replace(',', '.'))
            except: odds = 1.0
            
            try: stake = float(str(row.get('Stake', 0)).replace(',', '.'))
            except: stake = 0.0
            
            res = str(row.get('Result', '')).strip()
            date = str(row.get('Date', ''))
            
            if stake == 0: stake = next_bets.get(comp, 30.0)
            
            # PENDING
            if res == "Pending" or not res:
                processed.append({
                    "Row": i+2, "Comp": comp, "Match": match, "Date": date, 
                    "Profit": 0, "Status": "Pending", "Stake": stake, "Odds": odds, 
                    "Income": 0, "Expense": 0
                })
                continue
            
            # COMPLETED
            cycles[comp] = cycles.get(comp, 0.0) + stake
            
            if "Draw (X)" in res:
                income = stake * odds
                net = income - cycles[comp]
                cycles[comp] = 0.0
                next_bets[comp] = 30.0
                status = "Won"
            else:
                income = 0.0
                net = -stake
                next_bets[comp] = stake * 2.0
                status = "Lost"
                
            processed.append({
                "Row": i+2, "Comp": comp, "Match": match, "Date": date, 
                "Profit": net, "Status": status, "Stake": stake, "Odds": odds, 
                "Income": income, "Expense": stake
            })
        except: continue
        
    return pd.DataFrame(processed), next_bets

df, next_stakes = process_data(raw_data)
# בנקרול חי = התחלתי + סך הרווח הנקי
current_bal = initial_bankroll + (df['Profit'].sum() if not df.empty else 0)

# --- 5. SIDEBAR ---
with st.sidebar:
    st.image(APP_LOGO_URL, use_container_width=True)
    if error_msg: st.error("Offline")
    else: st.success("Connected")
        
    st.metric("Bankroll", f"₪{initial_bankroll:,.0f}")
    
    amt = st.number_input("Amount", 100.0, step=50.0)
    c1, c2 = st.columns(2)
    if c1.button("Deposit"):
        if worksheet: worksheet.update