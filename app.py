import streamlit as st
import pandas as pd
import plotly.express as px
import gspread
import datetime

# --- 1. CONFIGURATION ---
APP_LOGO_URL = "https://i.postimg.cc/8Cr6SypK/yzwb-ll-sm.png"
BG_IMAGE_URL = "https://i.postimg.cc/GmFZ4KS7/Gemini-Generated-Image-k1h11zk1h11zk1h1.png"

# הלינק הקבוע לגיליון שלך
SHEET_URL = "https://docs.google.com/spreadsheets/d/1o7OO2nyqAEqRgUq5makKZKR7ZtFyeh2JcJlzXnEmsv8/edit?gid=0#gid=0"

# לוגואים קבועים
LOGO_BRIGHTON = "https://upload.wikimedia.org/wikipedia/en/f/fd/Brighton_&_Hove_Albion_FC_logo.svg"
LOGO_AFRICA = "https://upload.wikimedia.org/wikipedia/en/f/f9/2023_Africa_Cup_of_Nations_logo.png"

st.set_page_config(
    page_title="Elite Football Tracker",
    layout="wide",
    page_icon=APP_LOGO_URL,
    initial_sidebar_state="expanded"
)

# --- 2. CSS STYLING ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;600;900&family=Inter:wght@400;600&display=swap');
    
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    [data-testid="stSidebarNav"] {{display: none;}}
    
    [data-testid="collapsedControl"], [data-testid="stSidebarCollapsedControl"], button[kind="header"] {{
        display: block !important;
        visibility: visible !important;
    }}

    [data-testid="stAppViewContainer"] {{
        background-image: linear-gradient(rgba(0, 0, 0, 0.7), rgba(0, 0, 0, 0.7)), url("{BG_IMAGE_URL}");
        background-attachment: fixed;
        background-size: cover;
        background-position: center;
    }}

    [data-testid="stSidebar"] {{
        background-color: #f8f9fa !important;
        border-right: 1px solid #ddd;
    }}
    [data-testid="stSidebar"] * {{
        color: #000000 !important;
        text-shadow: none !important;
        font-family: 'Montserrat', sans-serif;
    }}
    
    /* Banners */
    .comp-banner-box {{
        border-radius: 15px; padding: 20px; display: flex; align-items: center; 
        justify-content: center; margin-bottom: 30px; box-shadow: 0 10px 30px rgba(0,0,0,0.5);
        border: 2px solid rgba(255,255,255,0.4); width: 100%;
    }}
    .comp-banner-logo {{ height: 70px; margin-right: 20px; filter: drop-shadow(0 4px 6px rgba(0,0,0,0.3)); }}
    .comp-banner-text {{ margin: 0; font-size: 2.5rem; font-weight: 900; text-transform: uppercase; letter-spacing: 2px; }}

    @media only screen and (max-width: 768px) {{
        .comp-banner-text {{ display: none !important; }}
        .comp-banner-logo {{ margin-right: 0 !important; height: 80px !important; }}
        .comp-banner-box {{ padding: 15px !important; }}
        [data-testid="stDataFrame"] * {{font-size: 12px !important;}}
    }}

    /* Cards */
    .activity-card {{
        border-radius: 15px !important; padding: 20px !important; margin-bottom: 15px !important;
        box-shadow: 0 8px 25px rgba(0,0,0,0.4) !important; position: relative !important; overflow: hidden !important;
    }}
    .activity-card-won {{ background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 50%, #b1dfbb 100%) !important; border-left: 6px solid #28a745 !important; }}
    .activity-card-lost {{ background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 50%, #f1b0b7 100%) !important; border-left: 6px solid #dc3545 !important; }}
    .activity-card-pending {{ background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 50%, #fdcb6e 100%) !important; border-left: 6px solid #ffc107 !important; }}
    
    .custom-metric-box {{
        background-color: rgba(255, 255, 255, 0.95); border-radius: 12px; padding: 20px;
        text-align: center; box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }}
    .metric-card-label {{ color: #555 !important; font-weight: 700; font-size: 13px; text-shadow: none !important; }}
    .metric-card-value {{ color: #1b4332 !important; font-weight: 900; font-size: 26px; text-shadow: none !important; }}
    </style>
""", unsafe_allow_html=True)

# --- 3. BACKEND ---
@st.cache_data(ttl=15)
def get_data_sync():
    try:
        # מתחבר ישירות ללינק שצרבנו בקוד
        gc = gspread.service_account_from_dict(st.secrets["service_account"])
        sh = gc.open_by_url(SHEET_URL)
        ws_m = sh.get_worksheet(0)
        m_data = ws_m.get_all_records()
        try: base_br = float(str(ws_m.cell(1, 10).value).replace(',', ''))
        except: base_br = 5000.0
        return m_data, ws_m, base_br
    except Exception as e:
        st.error(f"Error: {e}")
        return [], None, 5000.0

m_raw, sheet_m, initial_br = get_data_sync()

def safe_float(v, default=0.0):
    try: return float(str(v).replace(',', '.'))
    except: return default

def update_bankroll(sheet, val):
    if sheet is None: return False
    try:
        sheet.update_cell(1, 10, val)
        get_data_sync.clear()
        return True
    except: return False

def update_match_result(sheet, row_num, result):
    if sheet is None: return False
    try:
        sheet.update_cell(row_num, 6, result)
        get_data_sync.clear()
        return True
    except: return False

def delete_last_row(sheet, row_count):
    if sheet is None or row_count == 0: return False
    try:
        sheet.delete_rows(row_count + 1)
        get_data_sync.clear()
        return True
    except: return False

def process_matches(raw):
    if not raw: return pd.DataFrame()
    processed = []
    
    # אתחול סייקלים לשתי התחרויות הקבועות
    cycle_invest = {"Brighton": 0.0, "Africa Cup of Nations": 0.0}
    next_bets = {"Brighton": 30.0, "Africa Cup of Nations": 30.0} # בסיס לכל תחרות
    
    for idx, row in enumerate(raw):
        # קריאת נתונים בטוחה
        comp = str(row.get('Competition', 'Brighton')).strip()
        if not comp: comp = 'Brighton'
        
        home = str(row.get('Home Team',''))
        away = str(row.get('Away Team',''))
        match_str = f"{home} vs {away}"
        date_str = str(row.get('Date', ''))
        
        odds = safe_float(row.get('Odds', 1.0))
        stake_val = row.get('Stake')
        
        # חישוב גובה ההימור
        if stake_val in [None, '', ' ']:
            exp = next_bets.get(comp, 30.0)
        else:
            exp = safe_float(stake_val, next_bets.get(comp, 30.0))
            
        res = str(row.get('Result', '')).strip()
        
        # לוגיקת Pending
        if res == "Pending":
            processed.append({
                "Row": idx+2, "Date": date_str, "Comp": comp, "Match": match_str,
                "Odds": odds, "Expense": 0.0, "Income": 0.0, "Net Profit": 0.0,
                "Status": "⏳ Pending"
            })
            continue
            
        # לוגיקת סיום משחק וחישוב הימור הבא
        if comp not in cycle_invest: cycle_invest[comp] = 0.0
        cycle_invest[comp] += exp
        
        is_win = "Draw (X)" in res
        
        if is_win:
            inc = exp * odds
            net = inc - cycle_invest[comp]
            cycle_invest[comp] = 0.0
            status = "✅ Won"
            next_bets[comp] = 30.0 # איפוס לבסיס (אפשר לשנות ל-20 לאפריקה אם תרצה)
        else:
            inc = 0.0
            net = -exp
            status = "❌ Lost"
            next_bets[comp] = exp * 2.0 # הכפלה
            
        processed.append({
            "Row": idx+2, "Date": date_str, "Comp": comp, "Match": match_str,
            "Odds": odds, "Expense": exp, "Income": inc, "Net Profit": net,
            "Status": status
        })
        
    return pd.DataFrame(processed), next_bets

df, next_stakes = process_matches(m_raw)
current_bal = initial_br + (df['Income'].sum() - df['Expense'].sum()) if not df.empty else initial_br

# --- 4. SIDEBAR (Hardcoded Navigation) ---
with st.sidebar:
    try: st.image(APP_LOGO_URL, use_container_width=True)
    except: pass
    
    st.markdown("## WALLET")
    st.metric("Bankroll", f"₪{initial_br:,.0f}")
    
    amt = st.number_input("Amount", min_value=0.0, value=100.0, step=50.0)
    c1, c2 = st.columns(2)
    if c1.button("Deposit"):
        update_bankroll(sheet_m, initial_br + amt); st.rerun()
    if c2.button("Withdraw"):
        update_bankroll(sheet_m, initial_br - amt); st.rerun()
        
    st.divider()
    
    # תפריט קבוע ללא אפשרות הוספה
    track = st.selectbox("Navigate", ["📊 Overview", "Brighton", "Africa Cup of Nations"])
    
    if st.button("🔄 Sync Cloud", use_container_width=True):
        get_data_sync.clear(); st.rerun()

# --- 5. MAIN CONTENT ---

# A. OVERVIEW
if track == "📊 Overview":
    st.markdown(f"""
        <div class="comp-banner-box" style="background: linear-gradient(90deg, #40916c, #95d5b2);">
            <img src="{APP_LOGO_URL}" class="comp-banner-logo">
            <h1 class="comp-banner-text" style="color: #081c15 !important;">OVERVIEW</h1>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"<h2 style='text-align:center;'>₪{current_bal:,.