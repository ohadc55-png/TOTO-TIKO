import streamlit as st
import pandas as pd
import plotly.express as px
import gspread
import datetime

# --- 1. CONFIGURATION ---
APP_LOGO_URL = "https://i.postimg.cc/8Cr6SypK/yzwb-ll-sm.png"
BG_IMAGE_URL = "https://i.postimg.cc/GmFZ4KS7/Gemini-Generated-Image-k1h11zk1h11zk1h1.png"

# הלינקים לחצים שהעלית
IMG_ARROW_MAIN = "https://i.postimg.cc/vHQy61dy/Gemini-Generated-Image-dl91ekdl91ekdl91.png"
IMG_ARROW_SIDEBAR = "https://i.postimg.cc/hvVG4Nxz/Gemini-Generated-Image-2tueuy2tueuy2tue.png"

st.set_page_config(
    page_title="Elite Football Tracker",
    layout="wide",
    page_icon=APP_LOGO_URL,
    initial_sidebar_state="expanded"
)

# --- 2. CSS STYLING (שמירה על העיצוב שלך + תיקוני פרופורציה וחצים) ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;600;900&family=Inter:wght@400;600&display=swap');
    
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    [data-testid="stSidebarNav"] {{display: none;}}
    
    /* תיקון חצים מבוסס תמונה */
    [data-testid="stSidebarCollapsedControl"] {{
        background-color: rgba(0, 0, 0, 0.6) !important;
        border-radius: 12px !important;
        width: 45px !important; height: 45px !important;
        background-image: url('{IMG_ARROW_MAIN}') !important;
        background-size: 28px !important;
        background-repeat: no-repeat !important;
        background-position: center !important;
        color: transparent !important; font-size: 0px !important;
    }}
    [data-testid="stSidebarCollapsedControl"] svg {{ display: none !important; }}

    button[kind="header"] {{
        background-image: url('{IMG_ARROW_SIDEBAR}') !important;
        background-size: 28px !important;
        background-repeat: no-repeat !important;
        background-position: center !important;
        color: transparent !important; font-size: 0px !important;
    }}
    button[kind="header"] svg {{ display: none !important; }}

    [data-testid="stAppViewContainer"] {{
        background-image: linear-gradient(rgba(0, 0, 0, 0.7), rgba(0, 0, 0, 0.7)), url("{BG_IMAGE_URL}");
        background-attachment: fixed; background-size: cover; background-position: center;
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

    .main h1, .main h2, .main h3, .main h4, .main p {{
        color: #ffffff !important;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.8);
    }}

    .custom-metric-box {{
        background-color: rgba(255, 255, 255, 0.95);
        border-radius: 12px; padding: 20px; text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }}
    .metric-card-label {{ color: #555 !important; font-weight: 700; font-size: 13px; text-shadow: none !important; }}
    .metric-card-value {{ color: #1b4332 !important; font-weight: 900; font-size: 26px; text-shadow: none !important; }}

    /* Activity Cards Style - Keeping your exact design */
    .activity-card {{
        border-radius: 15px !important; padding: 25px !important; margin-bottom: 20px !important;
        box-shadow: 0 8px 25px rgba(0,0,0,0.4) !important; transition: all 0.3s ease !important;
        position: relative !important; overflow: hidden !important;
    }}
    .activity-card-won {{ background: linear-gradient(135deg, rgba(212, 237, 218, 0.5) 0%, rgba(177, 223, 187, 0.5) 100%) !important; border-left: 6px solid #28a745 !important; }}
    .activity-card-lost {{ background: linear-gradient(135deg, rgba(248, 215, 218, 0.5) 0%, rgba(241, 176, 183, 0.5) 100%) !important; border-left: 6px solid #dc3545 !important; }}
    
    /* מובייל אופטימיזציה לבאנרים */
    @media only screen and (max-width: 768px) {{
        .banner-title-text {{ display: none !important; }}
        .banner-container-flex {{ justify-content: center !important; }}
        .activity-stats {{ flex-direction: column !important; gap: 10px !important; }}
        .activity-match {{ font-size: 1rem !important; }}
    }}

    /* Custom Loading Spinner */
    [data-testid="stStatusWidget"]::after {{ content: 'DRAW IT' !important; color: white; font-weight: 900; margin-top: 120px; position: absolute; }}
    </style>
""", unsafe_allow_html=True)

# --- 3. BACKEND LOGIC (PRESERVING YOUR FUNCTIONS) ---
@st.cache_data(ttl=30)
def get_data_from_sheets():
    try:
        gc = gspread.service_account_from_dict(st.secrets["service_account"])
        sh = gc.open_by_url(st.secrets["sheet_url"])
        matches_sheet = sh.get_worksheet(0)
        competitions_sheet = sh.get_worksheet(1)
        data = matches_sheet.get_all_records()
        competitions_data = competitions_sheet.get_all_records()
        try:
            val = matches_sheet.cell(1, 10).value
            initial_bankroll = float(str(val).replace(',', '')) if val else 5000.0
        except: initial_bankroll = 5000.0
        return data, matches_sheet, competitions_sheet, competitions_data, initial_bankroll
    except Exception as e:
        st.error(f"Connection Error: {e}")
        return [], None, None, [], 5000.0

def calculate_logic(raw_data, br_base, af_base):
    processed = []
    # Tracking per competition for cycle recovery
    cycle_invest = {}
    next_bets = {}
    
    for idx, row in enumerate(raw_data):
        try:
            comp = str(row.get('Competition', 'Brighton')).strip() or 'Brighton'
            if comp not in cycle_invest: cycle_invest[comp] = 0.0
            
            odds = safe_float_conversion(row.get('Odds', 1), 1.0)
            stake_val = row.get('Stake')
            # לוגיקה חכמה לסכום הימור
            exp = safe_float_conversion(stake_val, 30.0) 
            
            res = str(row.get('Result', '')).strip()
            if res == "Pending":
                processed.append({"Row": idx + 2, "Date": row.get('Date', ''), "Comp": comp, "Match": f"{row.get('Home Team','')} vs {row.get('Away Team','')}", "Odds": odds, "Expense": 0.0, "Income": 0.0, "Net Profit": 0.0, "Status": "⏳ Pending", "ROI": "N/A"})
                continue
            
            cycle_invest[comp] += exp
            is_win = "Draw (X)" in res
            
            if is_win:
                inc = exp * odds
                net = inc - cycle_invest[comp] # רווח סייקל אמיתי
                cycle_invest[comp] = 0.0
                status = "✅ Won"
            else:
                inc = 0.0
                net = -exp
                status = "❌ Lost"
            
            processed.append({"Row": idx + 2, "Date": row.get('Date', ''), "Comp": comp, "Match": f"{row.get('Home Team','')} vs {row.get('Away Team','')}", "Odds": odds, "Expense": exp, "Income": inc, "Net Profit": net, "Status": status})
        except: continue
    return processed

def safe_float_conversion(value, default=0.0):
    try: return float(str(value).replace(',', '.'))
    except: return default

# --- 4. EXECUTION ---
raw_data, matches_sheet, competitions_sheet, competitions_data, saved_br = get_data_from_sheets()
processed_matches = calculate_logic(raw_data, 30.0, 20.0)
df = pd.DataFrame(processed_matches) if processed_matches else pd.DataFrame()
current_bal = saved_br + (df['Income'].sum() - df['Expense'].sum()) if not df.empty else saved_br

# --- 5. UI LAYOUT ---
with st.sidebar:
    st.image(APP_LOGO_URL, use_container_width=True)
    st.markdown("## WALLET CONTROL")
    st.metric("Base Bankroll", f"₪{saved_br:,.0f}")
    amt = st.number_input("Transaction Amount", min_value=0.0, value=100.0, step=50.0, label_visibility="collapsed")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Deposit", use_container_width=True):
            matches_sheet.update_cell(1, 10, saved_br + amt); st.rerun()
    with c2:
        if st.button("Withdraw", use_container_width=True):
            matches_sheet.update_cell(1, 10, saved_br - amt); st.rerun()
    
    st.divider()
    # כפתור ליצירת תחרות חדשה (חלון צף יופעל כאן)
    if st.button("➕ New Competition", use_container_width=True, type="primary"):
        st.session_state.show_new_comp = True
    
    st.divider()
    active_comps = [c['Competition Name'] for c in competitions_data if c.get('Status') == 'Active']
    track = st.selectbox("Track", ["📊 Overview", "📚 History"] + active_comps, label_visibility="collapsed")
    if st.button("🔄 Sync Cloud", use_container_width=True):
        get_data_from_sheets.clear(); st.rerun()

# Modal Logic for New Competition
if st.session_state.get('show_new_comp', False):
    with st.form("new_comp_form"):
        st.subheader("🆕 New Competition Setup")
        c_name = st.text_input("Name")
        c_bet = st.number_input("Starting Bet", value=30.0)
        c_logo = st.text_input("Logo URL")
        col1, col2 = st.columns(2)
        c1 = col1.color_picker("Primary Color", "#4CABFF")
        c2 = col2.color_picker("Secondary Color", "#E6F7FF")
        if st.form_submit_button("Launch"):
            competitions_sheet.append_row([c_name, "Active", c_bet, "", c_logo, c1, c2, "#000000", datetime.datetime.now().strftime("%Y-%m-%d"), "", 0])
            st.session_state.show_new_comp = False
            st.rerun()

# --- MAIN CONTENT ---
if track == "📊 Overview":
    st.markdown(f"""<div style="background: linear-gradient(90deg, #40916c, #95d5b2); border-radius: 15px; padding: 20px; display: flex; align-items: center; justify-content: center; margin-bottom: 30px;"><img src="{APP_LOGO_URL}" style="height: 60px; margin-right: 20px;"><h1 style="margin: 0;">OVERVIEW</h1></div>""", unsafe_allow_html=True)
    st.markdown(f"<h2 style='text-align: center; font-size: 3rem;'>₪{current_bal:,.2f}</h2><p style='text-align: center; opacity: 0.7;'>LIVE BANKROLL</p>", unsafe_allow_html=True)
    
    comp_stats = get_competition_stats(df, saved_br)
    for stat in comp_stats:
        # בניה דינמית של הבאנר לפי התחרות
        st.markdown(f"""
            <div style="background: white; border-radius: 15px; padding: 20px; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center;">
                <h3 style="color: black !important; margin:0;">{stat['Competition']}</h3>
                <div style="text-align: right;"><div style="color: #666;">Profit</div><div style="font-size: 1.5rem; font-weight: 900; color: #2d6a4f;">₪{stat['Net Profit']:,.0f}</div></div>
            </div>
        """, unsafe_allow_html=True)

elif track == "📚 History":
    st.markdown("<h1>📚 Competition History</h1>", unsafe_allow_html=True)
    archived = [c for c in competitions_data if c.get('Status') == 'Archived']
    if archived:
        for c in archived:
            st.write(f"### {c['Competition Name']} (Closed)")
    else: st.info("No archived competitions.")

else:
    # עמוד תחרות ספציפי
    comp_meta = next(c for c in competitions_data if c['Competition Name'] == track)
    st.markdown(f"""
        <div class="banner-container-flex" style="background: linear-gradient(90deg, {comp_meta['Banner Color 1']}, {comp_meta['Banner Color 2']}); border-radius: 15px; padding: 25px; display: flex; align-items: center; margin-bottom: 30px;">
            <img src="{comp_meta['Logo URL'] or APP_LOGO_URL}" style="height: 70px; margin-right: 25px;">
            <h1 class="banner-title-text" style="margin: 0; color: {comp_meta['Text Color'] or 'white'} !important;">{track.upper()}</h1>
        </div>
    """, unsafe_allow_html=True)
    
    # כפתור סגירת תחרות
    if st.button("🏁 Close Competition", use_container_width=True):
        # מציאת השורה בשיטס ושינוי הסטטוס
        cell = competitions_sheet.find(track)
        competitions_sheet.update_cell(cell.row, 2, "Archived")
        st.success("Archived successfully!"); st.rerun()

    # Activity Log
    st.markdown("## 📜 Activity Log")
    f_df = df[df['Comp'] == track].sort_index(ascending=False)
    for idx, row in f_df.iterrows():
        card_type = "activity-card-won" if "Won" in row['Status'] else "activity-card-lost"
        st.markdown(f"""
            <div class="activity-card {card_type}">
                <div class="activity-header">
                    <div class="activity-match">{row['Match']}</div>
                    <div class="activity-date">📅 {row['Date']}</div>
                </div>
                <div class="activity-stats">
                    <div class="activity-stat-item"><div class="activity-stat-label">Stake</div><div class="activity-stat-value">₪{row['Expense']:,.0f}</div></div>
                    <div class="activity-stat-item"><div class="activity-stat-label">ROI</div><div class="activity-stat-value">₪{row['Net Profit']:,.0f}</div></div>
                </div>
            </div>
        """, unsafe_allow_html=True)

# פונקציות עזר שנשארות מהקוד המקורי
def get_competition_stats(df, initial_bankroll):
    if df.empty: return []
    stats = []
    for comp in df['Comp'].unique():
        comp_df = df[df['Comp'] == comp]
        net_profit = comp_df['Income'].sum() - comp_df['Expense'].sum()
        stats.append({'Competition': comp, 'Net Profit': net_profit})
    return stats