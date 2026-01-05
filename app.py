import streamlit as st
import pandas as pd
import plotly.express as px
import gspread
import datetime

# --- 1. CONFIGURATION ---
APP_LOGO_URL = "https://i.postimg.cc/8Cr6SypK/yzwb-ll-sm.png"
BG_IMAGE_URL = "https://i.postimg.cc/GmFZ4KS7/Gemini-Generated-Image-k1h11zk1h11zk1h1.png"

# *** הלינק מוטמע כאן ישירות כדי למנוע תקלות ***
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
        border-radius: 15px; padding: 15px 25px !important; display: flex !important;
        align-items: center !important; justify-content: center !important; margin-bottom: 25px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.5); border: 2px solid rgba(255,255,255,0.4); width: 100%;
    }}
    .comp-banner-logo {{ height: 55px !important; margin-right: 20px; filter: drop-shadow(0 4px 6px rgba(0,0,0,0.3)); }}
    .comp-banner-text {{ margin: 0 !important; font-size: 1.8rem !important; font-weight: 900 !important; text-transform: uppercase; letter-spacing: 2px !important; font-family: 'Montserrat', sans-serif !important; }}

    @media only screen and (max-width: 768px) {{
        .comp-banner-text {{ display: none !important; }}
        .comp-banner-logo {{ margin-right: 0 !important; height: 60px !important; }}
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

# --- 3. BACKEND FUNCTIONS ---
@st.cache_data(ttl=30)
def get_data_from_sheets():
    try:
        # שימוש במשתנה SHEET_URL שמוגדר למעלה בקוד, ולא מתוך st.secrets
        gc = gspread.service_account_from_dict(st.secrets["service_account"])
        sh = gc.open_by_url(SHEET_URL)
        
        matches_sheet = sh.get_worksheet(0)
        competitions_sheet = sh.get_worksheet(1)
        data = matches_sheet.get_all_records()
        competitions_data = competitions_sheet.get_all_records()
        
        try:
            val = matches_sheet.cell(1, 10).value
            initial_bankroll = float(str(val).replace(',', '')) if val else 5000.0
        except:
            initial_bankroll = 5000.0
            
        return data, matches_sheet, competitions_sheet, competitions_data, initial_bankroll
    except Exception as e:
        st.error(f"Connection Error: {e}")
        return [], None, None, [], 5000.0

def update_bankroll(sheet, val):
    if sheet is None: return False
    try:
        sheet.update_cell(1, 10, val)
        get_data_from_sheets.clear()
        return True
    except: return False

def safe_float_conversion(value, default=0.0):
    try: return float(str(value).replace(',', '.'))
    except: return default

def calculate_logic(raw_data, br_base, af_base):
    processed = []
    next_bets = {"Brighton": float(br_base), "Africa Cup of Nations": float(af_base)}
    cycle_invest = {"Brighton": 0.0, "Africa Cup of Nations": 0.0}
    
    for idx, row in enumerate(raw_data):
        try:
            comp = str(row.get('Competition', 'Brighton')).strip() or 'Brighton'
            home = str(row.get('Home Team', '')).strip()
            away = str(row.get('Away Team', '')).strip()
            match_name = f"{home} vs {away}"
            date_val = str(row.get('Date', ''))
            
            odds = safe_float_conversion(row.get('Odds', 1), 1.0)
            stake_val = row.get('Stake')
            
            if stake_val in [None, '', ' ']:
                exp = next_bets.get(comp, 30.0)
            else:
                exp = safe_float_conversion(stake_val, next_bets.get(comp, 30.0))
            
            res = str(row.get('Result', '')).strip()
            
            if res == "Pending":
                processed.append({
                    "Row": idx + 2, "Date": date_val, "Comp": comp, "Match": match_name,
                    "Odds": odds, "Expense": 0.0, "Income": 0.0, "Net Profit": 0.0,
                    "Status": "⏳ Pending", "ROI": "N/A"
                })
                continue
            
            cycle_invest[comp] = cycle_invest.get(comp, 0) + exp
            is_win = "Draw (X)" in res
            
            if is_win:
                inc = exp * odds
                net = inc - cycle_invest[comp]
                try: roi = f"{(net / cycle_invest[comp]) * 100:.1f}%"
                except: roi = "0.0%"
                next_bets[comp] = float(br_base if "Brighton" in comp else af_base)
                cycle_invest[comp] = 0.0
                status = "✅ Won"
            else:
                inc = 0.0
                net = -exp
                roi = "N/A"
                next_bets[comp] = exp * 2.0
                status = "❌ Lost"
            
            processed.append({
                "Row": idx + 2, "Date": date_val, "Comp": comp, "Match": match_name,
                "Odds": odds, "Expense": exp, "Income": inc, "Net Profit": net,
                "Status": status, "ROI": roi
            })
        except: continue
    return processed, next_bets

def get_competition_stats(df, initial_bankroll):
    if df.empty: return []
    stats = []
    for comp in df['Comp'].unique():
        comp_df = df[df['Comp'] == comp].copy()
        total_matches = len(comp_df)
        wins = len(comp_df[comp_df['Status'] == "✅ Won"])
        net_profit = comp_df['Income'].sum() - comp_df['Expense'].sum()
        stats.append({'Competition': comp, 'Matches': total_matches, 'Wins': wins, 'Net Profit': net_profit})
    return stats

def add_competition(comp_sheet, name, initial_bet, goal, logo_url, color1, color2, text_color):
    if comp_sheet is None: return False
    try:
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        comp_sheet.append_row([name, "Active", initial_bet, goal, logo_url, color1, color2, text_color, today, "", 0])
        get_data_from_sheets.clear()
        return True
    except: return False

def get_active_competitions(competitions_data):
    return [comp['Competition Name'] for comp in competitions_data if comp.get('Status') == 'Active']

def get_competition_config(comp_name, competitions_data):
    for comp in competitions_data:
        if comp.get('Competition Name') == comp_name:
            return {
                'logo': comp.get('Logo URL', APP_LOGO_URL),
                'color1': comp.get('Banner Color 1', '#4CABFF'),
                'color2': comp.get('Banner Color 2', '#E6F7FF'),
                'text_color': comp.get('Text Color', '#004085'),
                'initial_bet': comp.get('Initial Bet', 30)
            }
    return None

def add_match_to_sheet(sheet, date, comp, home, away, odds, result, stake):
    if sheet is None: return False
    try:
        sheet.append_row([date, comp, home, away, odds, result, stake, 0.0])
        get_data_from_sheets.clear()
        return True
    except: return False

def update_match_result(sheet, row_num, result):
    if sheet is None: return False
    try:
        sheet.update_cell(row_num, 6, result)
        get_data_from_sheets.clear()
        return True
    except: return False

def delete_last_row(sheet, row_count):
    if sheet is None or row_count == 0: return False
    try:
        sheet.delete_rows(row_count + 1)
        get_data_from_sheets.clear()
        return True
    except: return False

# --- 4. EXECUTION ---
raw_data, matches_sheet, competitions_sheet, competitions_data, saved_br = get_data_from_sheets()
processed, next_stakes = calculate_logic(raw_data, 30.0, 20.0)
if processed:
    df = pd.DataFrame(processed)
    current_bal = saved_br + (df['Income'].sum() - df['Expense'].sum())
else:
    df = pd.DataFrame()
    current_bal = saved_br
active_competitions = get_active_competitions(competitions_data)

# --- 5. SIDEBAR ---
with st.sidebar:
    try: st.image(APP_LOGO_URL, use_container_width=True)
    except: pass
    st.markdown("## WALLET CONTROL")
    st.metric("Base Bankroll", f"₪{saved_br:,.0f}")
    amt = st.number_input("Amount", min_value=0.0, value=100.0, step=50.0, label_visibility="collapsed")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Deposit", use_container_width=True):
            if update_bankroll(matches_sheet, saved_br + amt): st.rerun()
    with c2:
        if st.button("Withdraw", use_container_width=True):
            if update_bankroll(matches_sheet, saved_br - amt): st.rerun()
    st.divider()
    if st.button("➕ New Competition", use_container_width=True, type="primary"):
        st.session_state.show_new_comp_modal = True
    st.divider()
    
    dropdown_options = ["📊 Overview"] + active_competitions + ["📚 History"]
    track = st.selectbox("Track", dropdown_options, label_visibility="collapsed")
    
    if st.button("🔄 Sync Cloud", use_container_width=True):
        get_data_from_sheets.clear()
        st.rerun()

# NEW COMPETITION MODAL
if st.session_state.get('show_new_comp_modal', False):
    with st.form("new_competition_form"):
        st.markdown("### 🆕 Create New Competition")
        comp_name = st.text_input("Competition Name")
        comp_initial_bet = st.number_input("Initial Bet (₪)", min_value=1.0, value=30.0)
        comp_logo = st.text_input("Logo URL")
        c1, c2 = st.columns(2)
        with c1: comp_color1 = st.color_picker("Color 1", "#4CABFF")
        with c2: comp_color2 = st.color_picker("Color 2", "#E6F7FF")
        comp_text_color = st.color_picker("Text Color", "#004085")
        
        if st.form_submit_button("✅ Create"):
            if comp_name:
                if add_competition(competitions_sheet, comp_name, comp_initial_bet, "", comp_logo or APP_LOGO_URL, comp_color1, comp_color2, comp_text_color):
                    st.success("Created!")
                    st.session_state.show_new_comp_modal = False
                    st.rerun()

# --- MAIN CONTENT ---
if track == "📊 Overview":
    st.markdown(f"""
        <div class="comp-banner-box" style="background: linear-gradient(90deg, #40916c 0%, #95d5b2 50%, #40916c 100%);">
            <img src="{APP_LOGO_URL}" class="comp-banner-logo">
            <h1 class="comp-banner-text" style="color: #081c15 !important;">OVERVIEW</h1>
        </div>
    """, unsafe_allow_html=True)
    st.markdown(f"""<div style="text-align: center; margin-bottom: 50px;"><div style="font-size: 2.3rem; font-weight: 300; color: #ffffff;">₪{current_bal:,.2f}</div><div style="font-size: 0.8rem; font-weight: 600; color: #cccccc;">LIVE BANKROLL</div></div>""", unsafe_allow_html=True)
    
    if not df.empty:
        comp_stats = get_competition_stats(df, saved_br)
        for stat in comp_stats:
            st.markdown(f"""
                <div style="background: white; border-radius: 15px; padding: 20px; margin-bottom: 15px; display: flex; justify-content: space-between; align-items: center;">
                    <h3 style="color: black !important; margin:0;">{stat['Competition']}</h3>
                    <div style="font-size: 1.5rem; font-weight: 900; color: {'#2d6a4f' if stat['Net Profit'] >= 0 else '#d32f2f'};">₪{stat['Net Profit']:,.0f}</div>
                </div>
            """, unsafe_allow_html=True)

elif track == "📚 History":
    st.markdown("<h1 style='text-align: center; color: white;'>📚 Competition History</h1>", unsafe_allow_html=True)
    archived = [c for c in competitions_data if c.get('Status') == 'Archived']
    if archived:
        for c in archived:
            st.write(f"### {c['Competition Name']} (Closed)")
    else:
        st.info("No archived competitions.")

else:
    # Active Competition
    comp_config = get_competition_config(track, competitions_data)
    if comp_config:
        logo_src = comp_config['logo']
        gradient = f"linear-gradient(90deg, {comp_config['color1']} 0%, {comp_config['color2']} 50%, {comp_config['color1']} 100%)"
        text_color = comp_config['text_color']
        initial_bet = comp_config['initial_bet']
    else:
        logo_src = APP_LOGO_URL
        gradient = "linear-gradient(90deg, #1b4332 0%, #40916c 100%)"
        text_color = "#FFFFFF"
        initial_bet = 30.0

    st.markdown(f"""
        <div class="comp-banner-box" style="background: {gradient};">
            <img src="{logo_src}" class="comp-banner-logo">
            <h1 class="comp-banner-text" style="color: {text_color} !important;">{track.upper()}</h1>
        </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""<div style="text-align: center; margin-bottom: 35px;"><div style="font-size: 2.3rem; font-weight: 300; color: #ffffff;">₪{current_bal:,.2f}</div><div style="font-size: 0.8rem; font-weight: 600; color: #cccccc;">LIVE BANKROLL</div></div>""", unsafe_allow_html=True)

    if not df.empty:
        f_df = df[df['Comp'] == track].copy()
    else:
        f_df = pd.DataFrame()

    if not f_df.empty:
        m_exp = f_df['Expense'].sum()
        m_inc = f_df['Income'].sum()
        m_net = m_inc - m_exp
    else:
        m_exp, m_inc, m_net = 0.0, 0.0, 0.0

    c1, c2, c3 = st.columns(3)
    with c1: st.markdown(f"""<div class="custom-metric-box"><div class="metric-card-label">TOTAL EXPENSES</div><div class="metric-card-value">₪{m_exp:,.0f}</div></div>""", unsafe_allow_html=True)
    with c2: st.markdown(f"""<div class="custom-metric-box"><div class="metric-card-label">TOTAL REVENUE</div><div class="metric-card-value">₪{m_inc:,.0f}</div></div>""", unsafe_allow_html=True)
    with c3:
        color_net = '#2d6a4f' if m_net >= 0 else '#d32f2f'
        st.markdown(f"""<div class="custom-metric-box"><div class="metric-card-label">NET PROFIT</div><div class="metric-card-value" style="color: {color_net} !important;">₪{m_net:,.0f}</div></div>""", unsafe_allow_html=True)

    next_val = next_stakes.get(track, initial_bet)
    st.markdown(f"""<div style="text-align: center; margin: 30px 0;"><span style="font-size: 1.4rem; color: white;">Next Bet: </span><span style="font-size: 1.6rem; color: #4CAF50; font-weight: 900;">₪{next_val:,.0f}</span></div>""", unsafe_allow_html=True)

    col_form, col_chart = st.columns([1, 1])
    with col_form:
        with st.form("new_match"):
            st.subheader("Add Match")
            h_team = st.text_input("Home")
            a_team = st.text_input("Away")
            odds_val = st.number_input("Odds", value=3.2)
            stake_val = st.number_input("Stake", value=float(next_val))
            result_val = st.radio("Result", ["Pending", "Draw (X)", "No Draw"], horizontal=True)
            if st.form_submit_button("Submit"):
                if h_team and a_team:
                    if add_match_to_sheet(matches_sheet, str(datetime.date.today()), track, h_team, a_team, odds_val, result_val, stake_val):
                        st.toast("Added!", icon="✅")
                        st.rerun()

    if st.button("🏁 Close Competition", use_container_width=True):
        cell = competitions_sheet.find(track)
        competitions_sheet.update_cell(cell.row, 2, "Archived")
        st.success("Competition Archived!")
        st.rerun()

    st.markdown("""<h2 style="color: #ffffff !important; margin-bottom: 20px;">📜 Activity Log</h2>""", unsafe_allow_html=True)
    if not f_df.empty:
        f_df_sorted = f_df.sort_index(ascending=False)
        for idx, match in f_df_sorted.iterrows():
            if 'Won' in str(match['Status']): card_class = "activity-card-won"
            elif 'Pending' in str(match['Status']): card_class = "activity-card-pending"
            else: card_class = "activity-card-lost"
            
            # Update Buttons for Pending
            if 'Pending' in str(match['Status']):
                st.markdown("#### ⏳ Update")
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1: st.write(f"**{match['Match']}**")
                with col2:
                    if st.button("✅ Won", key=f"w_{idx}", use_container_width=True):
                        update_match_result(matches_sheet, int(match['Row']), "Draw (X)")
                        st.rerun()
                with col3:
                    if st.button("❌ Lost", key=f"l_{idx}", use_container_width=True):
                        update_match_result(matches_sheet, int(match['Row']), "No Draw")
                        st.rerun()

            st.markdown(f"""
<div class="activity-card {card_class}">
    <div style="display:flex; justify-content:space-between; align-items:center;">
        <div>
            <div style="font-weight:900; font-size:1.1rem; color:black;">{match['Match']}</div>
            <div style="color:#555; font-size:0.8rem;">{match['Date']}</div>
        </div>
        <div style="text-align:right;">
            <div style="font-weight:900; font-size:1.3rem; color:black;">₪{match['Net Profit']:,.0f}</div>
            <div style="font-size:0.8rem; color:black;">{match['Status']}</div>
        </div>
    </div>
</div>
            """, unsafe_allow_html=True)