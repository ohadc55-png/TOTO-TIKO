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
    
    st.markdown(f"<h2 style='text-align:center;'>₪{current_bal:,.2f}</h2><p style='text-align:center;'>LIVE BALANCE</p>", unsafe_allow_html=True)
    
    if not df.empty:
        # סטטיסטיקה לפי תחרות
        stats = df.groupby('Comp').agg({'Net Profit': 'sum', 'Match': 'count'}).reset_index()
        for _, row in stats.iterrows():
            color = '#2d6a4f' if row['Net Profit'] >= 0 else '#d32f2f'
            st.markdown(f"""
                <div style="background: white; border-radius: 12px; padding: 20px; margin-bottom: 10px; display:flex; justify-content:space-between; align-items:center;">
                    <h3 style="color:black; margin:0;">{row['Comp']}</h3>
                    <div style="text-align:right;">
                        <div style="font-weight:900; color:{color}; font-size:1.4rem;">₪{row['Net Profit']:,.0f}</div>
                        <div style="color:#666; font-size:0.8rem;">{row['Match']} Games</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

# B. SPECIFIC TRACK (Brighton / Africa)
else:
    # הגדרות עיצוב לפי התחרות שנבחרה
    if track == "Brighton":
        banner_c1, banner_c2 = "#4CABFF", "#E6F7FF"
        text_color = "#004085"
        logo = LOGO_BRIGHTON
        base_stake = 30.0
    else: # Africa
        banner_c1, banner_c2 = "#007A33", "#FCD116" # צבעי אפריקה
        text_color = "#FFFFFF"
        logo = LOGO_AFRICA
        base_stake = 30.0

    st.markdown(f"""
        <div class="comp-banner-box" style="background: linear-gradient(90deg, {banner_c1}, {banner_c2});">
            <img src="{logo}" class="comp-banner-logo">
            <h1 class="comp-banner-text" style="color: {text_color} !important;">{track}</h1>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"<h2 style='text-align:center;'>₪{current_bal:,.2f}</h2>", unsafe_allow_html=True)
    
    # סינון הנתונים לתחרות הנוכחית
    track_df = df[df['Comp'] == track].copy() if not df.empty else pd.DataFrame()
    
    # כרטיסי מידע
    exp = track_df['Expense'].sum() if not track_df.empty else 0
    inc = track_df['Income'].sum() if not track_df.empty else 0
    net = inc - exp
    
    c1, c2, c3 = st.columns(3)
    c1.markdown(f"<div class='custom-metric-box'><div class='metric-card-label'>EXPENSES</div><div class='metric-card-value'>₪{exp:,.0f}</div></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='custom-metric-box'><div class='metric-card-label'>REVENUE</div><div class='metric-card-value'>₪{inc:,.0f}</div></div>", unsafe_allow_html=True)
    color = '#2d6a4f' if net >= 0 else '#d32f2f'
    c3.markdown(f"<div class='custom-metric-box'><div class='metric-card-label'>NET PROFIT</div><div class='metric-card-value' style='color:{color} !important;'>₪{net:,.0f}</div></div>", unsafe_allow_html=True)
    
    # ההימור הבא
    next_s = next_stakes.get(track, base_stake)
    st.markdown(f"<div style='text-align:center; margin-top:20px; font-size:1.2rem;'>Next Bet: <span style='color:#4CAF50; font-weight:bold;'>₪{next_s:,.0f}</span></div>", unsafe_allow_html=True)
    
    # טופס הוספת משחק
    with st.form("add_game"):
        st.write("### ⚽ Add Match")
        c_a, c_b = st.columns(2)
        h = c_a.text_input("Home")
        a = c_b.text_input("Away")
        c_c, c_d = st.columns(2)
        odds = c_c.number_input("Odds", value=3.2)
        stake = c_d.number_input("Stake", value=float(next_s))
        res = st.radio("Result", ["Pending", "Draw (X)", "No Draw"], horizontal=True)
        
        if st.form_submit_button("Submit Game", use_container_width=True):
            if h and a:
                sheet_m.append_row([str(datetime.date.today()), track, h, a, odds, res, stake, 0.0])
                st.toast("Saved!"); get_data_sync.clear(); st.rerun()
            else:
                st.warning("Enter team names")

    # לוג פעילות
    st.write("### 📜 Activity")
    if not track_df.empty:
        track_df = track_df.sort_index(ascending=False)
        for idx, row in track_df.iterrows():
            if 'Won' in str(row['Status']): cls = 'activity-card-won'
            elif 'Pending' in str(row['Status']): cls = 'activity-card-pending'
            else: cls = 'activity-card-lost'
            
            # כפתורי עדכון למשחקים פתוחים
            if 'Pending' in str(row['Status']):
                st.info(f"Update: {row['Match']}")
                b1, b2 = st.columns(2)
                if b1.button("✅ WON", key=f"w{idx}"):
                    update_match_result(sheet_m, int(row['Row']), "Draw (X)"); st.rerun()
                if b2.button("❌ LOST", key=f"l{idx}"):
                    update_match_result(sheet_m, int(row['Row']), "No Draw"); st.rerun()
            
            st.markdown(f"""
                <div class="activity-card {cls}">
                    <div style="display:flex; justify-content:space-between;">
                        <div>
                            <div style="font-weight:bold; font-size:1.1rem; color:black;">{row['Match']}</div>
                            <div style="font-size:0.8rem; color:#555;">{row['Date']}</div>
                        </div>
                        <div style="text-align:right;">
                            <div style="font-weight:bold; font-size:1.2rem; color:black;">₪{row['Net Profit']:,.0f}</div>
                            <div style="font-size:0.8rem; color:black;">{row['Status']}</div>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

    # כפתור מחיקה אחרון (Admin)
    with st.expander("Admin Actions"):
        if st.button("Undo Last Entry"):
            delete_last_row(sheet_m, len(m_raw)); st.rerun()