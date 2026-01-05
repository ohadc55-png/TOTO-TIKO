import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import datetime

# --- 1. CONFIGURATION & ASSETS ---
APP_LOGO_URL = "https://i.postimg.cc/8Cr6SypK/yzwb-ll-sm.png"
BG_IMAGE_URL = "https://i.postimg.cc/GmFZ4KS7/Gemini-Generated-Image-k1h11zk1h11zk1h1.png"

# לוגואים
LOGOS = {
    "Brighton": "https://upload.wikimedia.org/wikipedia/en/f/fd/Brighton_&_Hove_Albion_FC_logo.svg",
    "Africa Cup of Nations": "https://upload.wikimedia.org/wikipedia/en/f/f9/2023_Africa_Cup_of_Nations_logo.png"
}
# צבעים לכרטיסיות
COLORS = {
    "Brighton": ("#0057B8", "#FFCD00"), # כחול צהוב
    "Africa Cup of Nations": ("#007A33", "#FCD116") # ירוק צהוב
}

st.set_page_config(page_title="Elite Football Tracker", layout="wide", page_icon=APP_LOGO_URL)

# --- 2. CSS STYLING ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;600;900&display=swap');
    
    [data-testid="stAppViewContainer"] {{
        background-image: linear-gradient(rgba(0,0,0,0.8), rgba(0,0,0,0.8)), url("{BG_IMAGE_URL}");
        background-attachment: fixed; background-size: cover;
    }}
    
    /* Activity Logs (History) */
    .activity-card {{
        background: rgba(255,255,255,0.95); border-radius: 12px; padding: 15px; margin-bottom: 10px;
        border-left: 8px solid #ccc; color: black !important; box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }}
    .activity-card-won {{ border-left-color: #28a745 !important; }}
    .activity-card-lost {{ border-left-color: #dc3545 !important; }}
    .activity-card-pending {{ border-left-color: #ffc107 !important; }}
    
    /* Metrics */
    .metric-box {{
        background: rgba(30, 30, 30, 0.8); border: 1px solid rgba(255,255,255,0.2);
        border-radius: 10px; padding: 15px; text-align: center; margin-bottom: 10px;
    }}
    .metric-label {{ font-size: 0.85rem; color: #ccc; text-transform: uppercase; letter-spacing: 1px; }}
    .metric-value {{ font-size: 1.6rem; font-weight: 700; color: #fff; }}

    /* Overview Cards */
    .overview-card {{
        background: linear-gradient(145deg, #1e1e1e, #2d2d2d);
        border-radius: 15px; padding: 20px; margin-bottom: 20px;
        border: 1px solid #444; box-shadow: 0 4px 15px rgba(0,0,0,0.5);
    }}
    .overview-header {{ display: flex; align-items: center; margin-bottom: 15px; border-bottom: 1px solid #444; padding-bottom: 10px; }}
    .overview-logo {{ height: 40px; margin-right: 15px; }}
    .overview-title {{ font-size: 1.2rem; font-weight: bold; color: white; margin: 0; }}
    .overview-stats {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }}
    .stat-item {{ background: rgba(0,0,0,0.3); padding: 10px; border-radius: 8px; text-align: center; }}
    .stat-val {{ font-size: 1.1rem; font-weight: bold; color: white; }}
    .stat-lbl {{ font-size: 0.7rem; color: #aaa; }}
    
    /* Top Banner */
    .comp-banner {{
        border-radius: 15px; padding: 25px; display: flex; align-items: center; 
        justify-content: center; margin-bottom: 30px; box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    }}
    </style>
""", unsafe_allow_html=True)

# --- 3. CONNECTION (Authorized) ---
@st.cache_data(ttl=15)
def connect_to_sheets():
    try:
        if "service_account" not in st.secrets or "sheet_id" not in st.secrets:
            return None, None, 5000.0, "Missing Secrets"
            
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["service_account"], scopes=scopes)
        gc = gspread.authorize(creds)
        
        sh = gc.open_by_key(st.secrets["sheet_id"])
        worksheet = sh.get_worksheet(0)
        
        raw_values = worksheet.get_all_values()
        if len(raw_values) > 1:
            headers = [h.strip() for h in raw_values[0]]
            data = [dict(zip(headers, row)) for row in raw_values[1:] if any(row)]
        else:
            data = []
            
        try:
            val = worksheet.cell(1, 10).value
            bankroll = float(str(val).replace(',', '')) if val else 5000.0
        except:
            bankroll = 5000.0
            
        return data, worksheet, bankroll, None
        
    except Exception as e:
        return None, None, 5000.0, str(e)

raw_data, worksheet, initial_bankroll, error_msg = connect_to_sheets()

# --- 4. DATA PROCESSING ---
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
            
            # ניתוח סטטוס
            if res == "Pending" or not res:
                status = "Pending"
                profit = 0
                income = 0
            elif "Draw (X)" in res:
                cycles[comp] = 0.0 # איפוס סייקל
                next_bets[comp] = 30.0
                income = stake * odds
                profit = income - stake
                status = "Won"
            else:
                cycles[comp] += stake
                next_bets[comp] = stake * 2.0
                income = 0
                profit = -stake
                status = "Lost"

            processed.append({
                "Row": i+2, "Comp": comp, "Match": match, "Date": date, 
                "Profit": profit, "Status": status, "Stake": stake, 
                "Odds": odds, "Income": income, "Expense": stake
            })
        except: continue
        
    return pd.DataFrame(processed), next_bets

df, next_stakes = process_data(raw_data)
# חישוב בנקרול נוכחי (התחלתי + רווחים)
current_bal = initial_bankroll + (df['Profit'].sum() if not df.empty else 0)

# --- 5. SIDEBAR ---
with st.sidebar:
    st.image(APP_LOGO_URL, use_container_width=True)
    if error_msg: st.error("Offline")
    else: st.success("Online")
    
    st.markdown(f"""
    <div style="text-align:center; padding:10px; background:rgba(255,255,255,0.1); border-radius:10px; margin-bottom:20px;">
        <div style="font-size:0.8rem; color:#aaa;">CURRENT BANKROLL</div>
        <div style="font-size:1.8rem; font-weight:bold; color:#4CAF50;">₪{current_bal:,.0f}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # ניהול כספים
    with st.expander("💰 Manage Funds"):
        amt = st.number_input("Amount", 100.0, step=50.0)
        c1, c2 = st.columns(2)
        if c1.button("Deposit"):
            if worksheet: worksheet.update_cell(1, 10, initial_bankroll + amt); connect_to_sheets.clear(); st.rerun()
        if c2.button("Withdraw"):
            if worksheet: worksheet.update_cell(1, 10, initial_bankroll - amt); connect_to_sheets.clear(); st.rerun()
            
    st.divider()
    track = st.selectbox("Navigate", ["📊 Overview", "Brighton", "Africa Cup of Nations"])
    if st.button("🔄 Sync Data"): connect_to_sheets.clear(); st.rerun()

# --- 6. MAIN CONTENT ---
if error_msg:
    st.error(f"⚠️ {error_msg}")
    st.stop()

# === OVERVIEW PAGE ===
if track == "📊 Overview":
    st.markdown('<h1 style="text-align:center; color:white; margin-bottom:40px;">TOURNAMENT SUMMARY</h1>', unsafe_allow_html=True)
    
    # הצגת כרטיסיות