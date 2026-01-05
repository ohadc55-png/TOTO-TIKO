import streamlit as st
import pandas as pd
import gspread
import datetime
import plotly.express as px

# --- 1. CONFIGURATION ---
APP_LOGO_URL = "https://i.postimg.cc/8Cr6SypK/yzwb-ll-sm.png"
BG_IMAGE_URL = "https://i.postimg.cc/GmFZ4KS7/Gemini-Generated-Image-k1h11zk1h11zk1h1.png"
# הלינק לשיטס נמצא כאן בקוד כדי למנוע תקלות ב-Secrets
SHEET_URL = "https://docs.google.com/spreadsheets/d/1o7OO2nyqAEqRgUq5makKZKR7ZtFyeh2JcJlzXnEmsv8/edit?gid=0#gid=0"

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
    
    .comp-banner-box {{
        border-radius: 15px; padding: 20px; display: flex; align-items: center; 
        justify-content: center; margin-bottom: 30px; box-shadow: 0 10px 30px rgba(0,0,0,0.5);
        border: 2px solid rgba(255,255,255,0.4); width: 100%;
    }}
    .comp-banner-logo {{ height: 55px; margin-right: 20px; filter: drop-shadow(0 4px 6px rgba(0,0,0,0.3)); }}
    .comp-banner-text {{ margin: 0; font-size: 1.8rem; font-weight: 900; text-transform: uppercase; letter-spacing: 2px; font-family: 'Montserrat', sans-serif; }}

    @media only screen and (max-width: 768px) {{
        .comp-banner-text {{ display: none !important; }}
        .comp-banner-logo {{ margin-right: 0 !important; height: 60px; }}
        .comp-banner-box {{ padding: 15px; }}
        [data-testid="stDataFrame"] * {{ font-size: 12px !important; }}
    }}

    .activity-card {{
        border-radius: 15px !important; padding: 20px !important; margin-bottom: 15px !important;
        box-shadow: 0 8px 25px rgba(0,0,0,0.4) !important; position: relative !important; overflow: hidden !important;
        background: rgba(255,255,255,0.9);
    }}
    .activity-card-won {{ border-left: 6px solid #28a745 !important; }}
    .activity-card-lost {{ border-left: 6px solid #dc3545 !important; }}
    .activity-card-pending {{ border-left: 6px solid #ffc107 !important; }}
    
    .custom-metric-box {{
        background-color: rgba(255, 255, 255, 0.95); border-radius: 12px; padding: 20px;
        text-align: center; box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }}
    .metric-card-label {{ color: #555 !important; font-weight: 700; font-size: 13px; }}
    .metric-card-value {{ color: #1b4332 !important; font-weight: 900; font-size: 26px; }}
    </style>
""", unsafe_allow_html=True)

# --- 3. BACKEND FUNCTIONS ---
@st.cache_data(ttl=30)
def get_data_from_sheets():
    try:
        if "service_account" not in st.secrets:
            st.error("Error: [service_account] section missing in Secrets!")
            return [], None, 5000.0
            
        # יצירת החיבור עם טיפול בשגיאות
        try:
            gc = gspread.service_account_from_dict(st.secrets["service_account"])
        except Exception as auth_err:
            st.error(f"Authentication Failed: {auth_err}")
            return [], None, 5000.0

        sh = gc.open_by_url(SHEET_URL)
        worksheet = sh.get_worksheet(0)
        data = worksheet.get_all_records()
        
        try:
            val = worksheet.cell(1, 10).value
            initial_bankroll = float(str(val).replace(',', '')) if val else 5000.0
        except:
            initial_bankroll = 5000.0
            
        return data, worksheet, initial_bankroll
        
    except Exception as e:
        # הצגת שגיאה מפורטת למקרה של בעיית חיבור
        st.error(f"Connection Error Details: {e}")
        return [], None, 5000.0

def update_bankroll(worksheet, val):
    if worksheet is None: return False
    try:
        worksheet.update_cell(1, 10, val)
        get_data_from_sheets.clear()
        return True
    except: return False

def safe_float(val):
    try: return float(str(val).replace(',', '.'))
    except: return 0.0

def calculate_logic(raw_data, br_base, af_base):
    processed = []
    next_bets = {"Brighton": float(br_base), "Africa Cup of Nations": float(af_base)}
    cycle_invest = {"Brighton": 0.0, "Africa Cup of Nations": 0.0}
    
    for idx, row in enumerate(raw_data):
        try:
            comp = str(row.get('Competition', 'Brighton')).strip() or 'Brighton'
            home = str(row.get('Home Team', '')).strip()
            away = str(row.get('Away Team', '')).strip()
            match = f"{home} vs {away}"
            date = str(row.get('Date', ''))
            odds = safe_float(row.get('Odds', 1))
            stake = safe_float(row.get('Stake', 0))
            if stake == 0: stake = next_bets.get(comp, 30.0)
            
            res = str(row.get('Result', '')).strip()
            
            if res == "Pending":
                processed.append({
                    "Row": idx + 2, "Date": date, "Comp": comp, "Match": match,
                    "Odds": odds, "Expense": 0.0, "Income": 0.0, "Net Profit": 0.0,
                    "Status": "⏳ Pending", "ROI": "N/A"
                })
                continue
            
            cycle_invest[comp] += stake
            if "Draw (X)" in res:
                inc = stake * odds
                net = inc - cycle_invest[comp]
                cycle_invest[comp] = 0.0
                next_bets[comp] = 30.0
                status = "✅ Won"
            else:
                inc = 0.0
                net = -stake
                next_bets[comp] = stake * 2.0
                status = "❌ Lost"
            
            processed.append({
                "Row": idx + 2, "Date": date, "Comp": comp, "Match": match,
                "Odds": odds, "Expense": stake, "Income": inc, "Net Profit": net,
                "Status": status, "ROI": "N/A"
            })
        except: continue
    return processed, next_bets

def get_stats(df, bankroll):
    if df.empty: return []
    stats = []
    for comp in df['Comp'].unique():
        cdf = df[df['Comp'] == comp]
        wins = len(cdf[cdf['Status'] == "✅ Won"])
        net = cdf['Income'].sum() - cdf['Expense'].sum()
        stats.append({'Competition': comp, 'Matches': len(cdf), 'Wins': wins, 'Net Profit': net})
    return stats

def add_match(ws, date, comp, h, a, o, res, s):
    if ws:
        try:
            ws.append_row([date, comp, h, a, o, res, s, 0.0])
            get_data_from_sheets.clear()
            return True
        except: return False
    return False

def update_res(ws, row, res):
    if ws:
        try:
            ws.update_cell(row, 6, res)
            get_data_from_sheets.clear()
            return True
        except: return False
    return False

def undo(ws, count):
    if ws and count > 0:
        try:
            ws.delete_rows(count + 1)
            get_data_from_sheets.clear()
            return True
        except: return False
    return False

# --- 4. EXECUTION ---
raw_data, worksheet, saved_br = get_data_from_sheets()
processed, next_stakes = calculate_logic(raw_data, 30.0, 20.0)
df = pd.DataFrame(processed) if processed else pd.DataFrame()
current_bal = saved_br + (df['Income'].sum() - df['Expense'].sum()) if not df.empty else saved_br

# --- 5. SIDEBAR ---
with st.sidebar:
    st.image(APP_LOGO_URL, use_container_width=True)
    st.metric("Base Bankroll", f"₪{saved_br:,.0f}")
    
    amt = st.number_input("Amount", 100.0, step=50.0)
    c1, c2 = st.columns(2)
    if c1.button("Deposit"): update_bankroll(worksheet, saved_br + amt); st.rerun()
    if c2.button("Withdraw"): update_bankroll(worksheet, saved_br - amt); st.rerun()
    
    st.divider()
    track = st.selectbox("Track", ["📊 Overview", "Brighton", "Africa Cup of Nations"])
    if st.button("Sync"): get_data_from_sheets.clear(); st.rerun()

# --- MAIN PAGE ---
if track == "📊 Overview":
    st.markdown(f"""
        <div class="comp-banner-box" style="background: linear-gradient(90deg, #40916c, #95d5b2);">
            <img src="{APP_LOGO_URL}" class="comp-banner-logo">
            <h1 class="comp-banner-text" style="color: #081c15 !important;">OVERVIEW</h1>
        </div>
    """, unsafe_allow_html=True)
    
    # תיקון קריטי: שימוש בגרשיים משולשים כדי למנוע SyntaxError
    st.markdown(f"""
        <div style="text-align: center; margin-bottom: 30px;">
            <h1 style="color: white; margin: 0;">₪{current_bal:,.2f}</h1>
            <p style="color: #ccc; font-weight: bold; margin-top: 5px;">LIVE BANKROLL</p>
        </div>
    """, unsafe_allow_html=True)
    
    stats = get_stats(df, saved_br)
    for stat in stats:
        color = "#2d6a4f" if stat['Net Profit'] >= 0 else "#d32f2f"
        st.markdown(f"""
            <div style="background:white; border-radius:15px; padding:20px; margin-bottom:15px; display:flex; justify-content:space-between; align-items:center;">
                <h3 style="color:black; margin:0;">{stat['Competition']}</h3>
                <div style="text-align:right;">
                    <div style="font-size:1.5rem; font-weight:900; color:{color};">₪{stat['Net Profit']:,.0f}</div>
                    <div style="color:#666;">{stat['Matches']} Matches</div>
                </div>
            </div>
        """, unsafe_allow_html=True)

else:
    # הגדרות תצוגה
    if track == "Brighton":
        c1, c2, logo = "#4CABFF", "#E6F7FF", "https://upload.wikimedia.org/wikipedia/en/f/fd/Brighton_&_Hove_Albion_FC_logo.svg"
        txt_col = "#004085"
    else:
        c1, c2, logo = "#007A33", "#FCD116", "https://upload.wikimedia.org/wikipedia/en/f/f9/2023_Africa_Cup_of_Nations_logo.png"
        txt_col = "#FFFFFF"

    st.markdown(f"""
        <div class="comp-banner-box" style="background: linear-gradient(90deg, {c1}, {c2});">
            <img src="{logo}" class="comp-banner-logo">
            <h1 class="comp-banner-text" style="color: {txt_col} !important;">{track.upper()}</h1>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""<h1 style='text-align:center; color:white;'>₪{current_bal:,.2f}</h1>""", unsafe_allow_html=True)

    f_df = df[df['Comp'] == track].copy() if not df.empty else pd.DataFrame()
    next_bet = next_stakes.get(track, 30.0)
    
    st.markdown(f"""<div style='text-align:center; margin:20px;'>Next Bet: <span style='color:#4CAF50; font-weight:900; font-size:1.5rem;'>₪{next_bet:,.0f}</span></div>""", unsafe_allow_html=True)

    # טופס
    c_form, c_chart = st.columns(2)
    with c_form:
        with st.form("new"):
            st.subheader("Add Match")
            h = st.text_input("Home")
            a = st.text_input("Away")
            o = st.number_input("Odds", 3.2)
            s = st.number_input("Stake", float(next_bet))
            res = st.radio("Result", ["Pending", "Draw (X)", "No Draw"], horizontal=True)
            if st.form_submit_button("Submit"):
                if h and a:
                    add_match(worksheet, str(datetime.date.today()), track, h, a, o, res, s)
                    st.rerun()

    # היסטוריה
    st.subheader("History")
    if not f_df.empty:
        for idx, row in f_df.sort_index(ascending=False).iterrows():
            cls = "activity-card-won" if "Won" in row['Status'] else "activity-card-pending" if "Pending" in row['Status'] else "activity-card-lost"
            
            if "Pending" in row['Status']:
                st.markdown(f"**{row['Match']}**")
                b1, b2 = st.columns(2)
                if b1.button("✅ Won", key=f"w{idx}"): update_res(worksheet, row['Row'], "Draw (X)"); st.rerun()
                if b2.button("❌ Lost", key=f"l{idx}"): update_res(worksheet, row['Row'], "No Draw"); st.rerun()
            
            st.markdown(f"""
                <div class="activity-card {cls}">
                    <div style="display:flex; justify-content:space-between;">
                        <b>{row['Match']}</b>
                        <b>₪{row['Net Profit']:,.0f}</b>
                    </div>
                    <div style="font-size:0.8rem; color:#555;">{row['Date']} | {row['Status']}</div>
                </div>
            """, unsafe_allow_html=True)

    with st.expander("Admin"):
        if st.button("Undo Last"): undo(worksheet, len(raw_data)); st.rerun()