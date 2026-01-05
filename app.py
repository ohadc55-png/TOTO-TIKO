import streamlit as st
import pandas as pd
import plotly.express as px
import gspread
import datetime

# --- CONFIGURATION ---
APP_LOGO_URL = "https://i.postimg.cc/8Cr6SypK/yzwb-ll-sm.png"
BG_IMAGE_URL = "https://i.postimg.cc/GmFZ4KS7/Gemini-Generated-Image-k1h11zk1h11zk1h1.png"

st.set_page_config(
    page_title="Elite Football Tracker",
    layout="wide",
    page_icon=APP_LOGO_URL,
    initial_sidebar_state="expanded"
)

# --- CSS STYLING ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;600;900&family=Inter:wght@400;600&display=swap');
    
    #MainMenu, footer, [data-testid="stSidebarNav"] {{display: none;}}
    [data-testid="collapsedControl"], [data-testid="stSidebarCollapsedControl"], button[kind="header"] {{display: block !important; visibility: visible !important;}}

    [data-testid="stAppViewContainer"] {{
        background-image: linear-gradient(rgba(0, 0, 0, 0.7), rgba(0, 0, 0, 0.7)), url("{BG_IMAGE_URL}");
        background-attachment: fixed;
        background-size: cover;
        background-position: center;
    }}

    [data-testid="stSidebar"] {{background-color: #f8f9fa !important; border-right: 1px solid #ddd;}}
    [data-testid="stSidebar"] * {{color: #000000 !important; text-shadow: none !important; font-family: 'Montserrat', sans-serif;}}
    [data-testid="stSidebar"] input {{color: #000000 !important; background-color: #ffffff !important; border: 1px solid #ccc;}}
    [data-testid="stSidebar"] button {{color: #ffffff !important;}}

    .main h1, .main h2, .main h3, .main h4, .main p {{color: #ffffff !important; text-shadow: 2px 2px 4px rgba(0,0,0,0.8);}}
    [data-testid="stDataFrame"] {{background-color: white !important; border-radius: 8px;}}
    [data-testid="stDataFrame"] * {{color: #000000 !important; text-shadow: none !important;}}
    [data-testid="stForm"] {{background-color: rgba(255, 255, 255, 0.95); border-radius: 15px; padding: 25px;}}
    [data-testid="stForm"] * {{color: #000000 !important; text-shadow: none !important;}}

    .custom-metric-box {{background-color: rgba(255, 255, 255, 0.95); border-radius: 12px; padding: 20px; text-align: center; box-shadow: 0 4px 15px rgba(0,0,0,0.3);}}
    .metric-card-label {{color: #555 !important; font-weight: 700; font-size: 13px; text-shadow: none !important;}}
    .metric-card-value {{color: #1b4332 !important; font-weight: 900; font-size: 26px; text-shadow: none !important;}}

    /* Banner */
    .comp-banner-box {{border-radius: 15px; padding: 15px 25px !important; display: flex !important; align-items: center !important; justify-content: center !important; margin-bottom: 25px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); border: 2px solid rgba(255,255,255,0.4);}}
    .comp-banner-logo {{height: 55px !important; margin-right: 20px; filter: drop-shadow(0 4px 6px rgba(0,0,0,0.3));}}
    .comp-banner-text {{margin: 0 !important; font-size: 1.8rem !important; font-weight: 900 !important; text-transform: uppercase; letter-spacing: 2px !important; font-family: 'Montserrat', sans-serif !important;}}

    /* Activity Cards */
    .activity-card {{border-radius: 15px !important; padding: 20px !important; margin-bottom: 15px !important; box-shadow: 0 8px 25px rgba(0,0,0,0.4) !important; position: relative !important; overflow: hidden !important;}}
    .activity-card-won {{background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 50%, #b1dfbb 100%) !important; border-left: 6px solid #28a745 !important;}}
    .activity-card-lost {{background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 50%, #f1b0b7 100%) !important; border-left: 6px solid #dc3545 !important;}}
    .activity-card-pending {{background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 50%, #fdcb6e 100%) !important; border-left: 6px solid #ffc107 !important;}}

    @media only screen and (max-width: 768px) {{
        .comp-banner-text {{display: none !important;}}
        .comp-banner-logo {{margin-right: 0 !important; height: 60px !important;}}
        .comp-banner-box {{padding: 15px !important;}}
        [data-testid="stDataFrame"] * {{font-size: 12px !important;}}
    }}
    
    /* Loading Spinner */
    [data-testid="stStatusWidget"] {{position: fixed !important; top: 50% !important; left: 50% !important; transform: translate(-50%, -50%) !important; z-index: 9999 !important; background: rgba(0, 0, 0, 0.9) !important; width: 100vw !important; height: 100vh !important; display: flex !important; align-items: center !important; justify-content: center !important;}}
    [data-testid="stStatusWidget"]::before {{content: '' !important; width: 80px !important; height: 80px !important; border: 8px solid rgba(255, 255, 255, 0.2) !important; border-top: 8px solid #4CAF50 !important; border-radius: 50% !important; animation: spin 1s linear infinite !important; position: absolute !important;}}
    [data-testid="stStatusWidget"]::after {{content: 'DRAW IT' !important; color: #ffffff !important; font-size: 1.5rem !important; font-weight: 900 !important; font-family: 'Montserrat', sans-serif !important; letter-spacing: 3px !important; position: absolute !important; margin-top: 120px !important; text-shadow: 0 0 20px rgba(76, 175, 80, 0.8) !important;}}
    @keyframes spin {{0% {{transform: rotate(0deg);}} 100% {{transform: rotate(360deg);}}}}
    </style>
""", unsafe_allow_html=True)

# --- BACKEND FUNCTIONS ---
@st.cache_data(ttl=30)
def get_data_from_sheets():
    """Fetch data from Google Sheets - DEBUG VERSION"""
    try:
        # ============ DEBUG START ============
        st.write("🔍 **Available secrets:**", list(st.secrets.keys()))
        
        if "service_account" in st.secrets:
            st.write("🔑 **Service account keys:**", list(st.secrets["service_account"].keys()))
        else:
            st.error("❌ 'service_account' not found in secrets!")
            return [], None, None, [], 5000.0
        
        if "sheet_url" not in st.secrets:
            st.error("❌ 'sheet_url' not found in secrets!")
            return [], None, None, [], 5000.0
        
        st.write("📄 **Sheet URL:**", st.secrets["sheet_url"][:50] + "...")
        # ============ DEBUG END ============
        
	creds = dict(st.secrets["service_account"])
	creds["private_key"] = creds["private_key"].replace("\\n", "\n")
	gc = gspread.service_account_from_dict(creds)
        sh = gc.open_by_url(st.secrets["sheet_url"])
        
        matches_sheet = sh.get_worksheet(0)
        competitions_sheet = sh.get_worksheet(1)
        
        data = matches_sheet.get_all_records()
        competitions_data = competitions_sheet.get_all_records()
        
        try:
            val = matches_sheet.cell(1, 10).value
            initial_bankroll = float(str(val).replace(',', '')) if val else 5000.0
        except:
            initial_bankroll = 5000.0
        
        st.success("✅ Connected successfully!")  # DEBUG
        return data, matches_sheet, competitions_sheet, competitions_data, initial_bankroll
        
    except Exception as e:
        st.error(f"❌ **Full error:** {type(e).__name__}: {e}")
        import traceback
        st.code(traceback.format_exc())
        return [], None, None, [], 5000.0

def update_bankroll(sheet, val):
    """Update bankroll in sheet"""
    if sheet is None: 
        return False
    try:
        sheet.update_cell(1, 10, val)
        get_data_from_sheets.clear()
        return True
    except Exception as e:
        st.error(f"Failed to update: {e}")
        return False

def safe_float_conversion(value, default=0.0):
    """Safely convert to float"""
    try: 
        return float(str(value).replace(',', '.'))
    except: 
        return default

def calculate_logic(raw_data, default_bets):
    """Calculate betting logic - FIXED VERSION"""
    processed = []
    next_bets = default_bets.copy()
    cycle_invest = {comp: 0.0 for comp in default_bets.keys()}
    
    for idx, row in enumerate(raw_data):
        try:
            comp = str(row.get('Competition', '')).strip()
            if not comp:
                continue
                
            home = str(row.get('Home Team', '')).strip()
            away = str(row.get('Away Team', '')).strip()
            match_name = f"{home} vs {away}"
            date_val = str(row.get('Date', ''))
            
            odds = safe_float_conversion(row.get('Odds', 1), 1.0)
            stake_val = row.get('Stake')
            
            # Get initial bet for this competition
            initial_bet = default_bets.get(comp, 30.0)
            
            if stake_val in [None, '', ' ']:
                exp = next_bets.get(comp, initial_bet)
            else:
                exp = safe_float_conversion(stake_val, next_bets.get(comp, initial_bet))
            
            res = str(row.get('Result', '')).strip()
            
            # Pending matches
            if res == "Pending":
                processed.append({
                    "Row": idx + 2,
                    "Date": date_val,
                    "Comp": comp,
                    "Match": match_name,
                    "Odds": odds,
                    "Expense": 0.0,
                    "Income": 0.0,
                    "Net Profit": 0.0,
                    "Status": "⏳ Pending",
                    "ROI": "N/A"
                })
                continue
            
            # Process completed matches
            if comp not in cycle_invest:
                cycle_invest[comp] = 0.0
            
            cycle_invest[comp] += exp
            is_win = "Draw (X)" in res
            
            if is_win:
                inc = exp * odds
                net = inc - cycle_invest[comp]
                try: 
                    roi = f"{(net / cycle_invest[comp]) * 100:.1f}%"
                except: 
                    roi = "0.0%"
                next_bets[comp] = initial_bet
                cycle_invest[comp] = 0.0
                status = "✅ Won"
            else:
                inc = 0.0
                net = -exp
                roi = "N/A"
                next_bets[comp] = exp * 2.0
                status = "❌ Lost"
            
            processed.append({
                "Row": idx + 2,
                "Date": date_val,
                "Comp": comp,
                "Match": match_name,
                "Odds": odds,
                "Expense": exp,
                "Income": inc,
                "Net Profit": net,
                "Status": status,
                "ROI": roi
            })
        except Exception as e:
            continue
    
    return processed, next_bets

def get_competition_stats(df, initial_bankroll):
    """Get stats for each competition"""
    if df.empty: 
        return []
    stats = []
    for comp in df['Comp'].unique():
        comp_df = df[df['Comp'] == comp].copy()
        total_matches = len(comp_df)
        wins = len(comp_df[comp_df['Status'] == "✅ Won"])
        net_profit = comp_df['Income'].sum() - comp_df['Expense'].sum()
        profit_pct = (net_profit / initial_bankroll * 100) if initial_bankroll > 0 else 0
        stats.append({
            'Competition': comp,
            'Matches': total_matches,
            'Wins': wins,
            'Net Profit': net_profit,
            'Profit %': profit_pct
        })
    return stats

def add_competition(comp_sheet, name, initial_bet, goal, logo_url, color1, color2, text_color):
    """Add new competition"""
    if comp_sheet is None: 
        return False
    try:
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        comp_sheet.append_row([name, "Active", initial_bet, goal, logo_url, color1, color2, text_color, today, "", 0])
        get_data_from_sheets.clear()
        return True
    except Exception as e:
        st.error(f"Failed to add: {e}")
        return False

def get_active_competitions(competitions_data):
    """Get list of active competitions"""
    return [comp['Competition Name'] for comp in competitions_data if comp.get('Status') == 'Active']

def get_competition_config(comp_name, competitions_data):
    """Get competition configuration"""
    for comp in competitions_data:
        if comp.get('Competition Name') == comp_name:
            return {
                'logo': comp.get('Logo URL', APP_LOGO_URL),
                'color1': comp.get('Banner Color 1', '#4CABFF'),
                'color2': comp.get('Banner Color 2', '#E6F7FF'),
                'text_color': comp.get('Text Color', '#004085'),
                'initial_bet': float(comp.get('Initial Bet', 30))
            }
    return None

def build_default_bets(competitions_data):
    """Build default bets dictionary from competitions"""
    default_bets = {}
    for comp in competitions_data:
        if comp.get('Status') == 'Active':
            comp_name = comp.get('Competition Name')
            initial_bet = float(comp.get('Initial Bet', 30))
            default_bets[comp_name] = initial_bet
    return default_bets

def add_match_to_sheet(sheet, date, comp, home, away, odds, result, stake):
    """Add match to sheet"""
    if sheet is None: 
        return False
    try:
        sheet.append_row([date, comp, home, away, odds, result, stake, 0.0])
        get_data_from_sheets.clear()
        return True
    except Exception as e:
        st.error(f"Failed: {e}")
        return False

def update_match_result(sheet, row_num, result):
    """Update match result"""
    if sheet is None: 
        return False
    try:
        sheet.update_cell(row_num, 6, result)
        get_data_from_sheets.clear()
        return True
    except Exception as e:
        st.error(f"Failed: {e}")
        return False

def close_competition(comp_sheet, comp_name, final_profit):
    """Close a competition"""
    if comp_sheet is None:
        return False
    try:
        cell = comp_sheet.find(comp_name)
        if cell:
            today = datetime.datetime.now().strftime("%Y-%m-%d")
            comp_sheet.update_cell(cell.row, 2, "Archived")  # Status
            comp_sheet.update_cell(cell.row, 10, today)  # Closed Date
            comp_sheet.update_cell(cell.row, 11, final_profit)  # Final Profit
            get_data_from_sheets.clear()
            return True
    except Exception as e:
        st.error(f"Failed to close: {e}")
    return False

def reopen_competition(comp_sheet, comp_name):
    """Reopen archived competition"""
    if comp_sheet is None:
        return False
    try:
        cell = comp_sheet.find(comp_name)
        if cell:
            comp_sheet.update_cell(cell.row, 2, "Active")  # Status
            comp_sheet.update_cell(cell.row, 10, "")  # Clear Closed Date
            get_data_from_sheets.clear()
            return True
    except Exception as e:
        st.error(f"Failed to reopen: {e}")
    return False

def delete_last_row(sheet, row_count):
    """Delete last row"""
    if sheet is None or row_count == 0: 
        return False
    try:
        sheet.delete_rows(row_count + 1)
        get_data_from_sheets.clear()
        return True
    except Exception as e:
        st.error(f"Failed: {e}")
        return False

# --- EXECUTION ---
raw_data, matches_sheet, competitions_sheet, competitions_data, saved_br = get_data_from_sheets()

# Build default bets from competitions
default_bets = build_default_bets(competitions_data)
processed, next_stakes = calculate_logic(raw_data, default_bets)

if processed:
    df = pd.DataFrame(processed)
    current_bal = saved_br + (df['Income'].sum() - df['Expense'].sum())
else:
    df = pd.DataFrame()
    current_bal = saved_br

active_competitions = get_active_competitions(competitions_data)

# --- SIDEBAR ---
with st.sidebar:
    try: 
        st.image(APP_LOGO_URL, use_container_width=True)
    except: 
        pass
    
    st.markdown("## WALLET CONTROL")
    st.metric("Base Bankroll", f"₪{saved_br:,.0f}")
    amt = st.number_input("Amount", min_value=0.0, value=100.0, step=50.0, label_visibility="collapsed")
    
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Deposit", use_container_width=True):
            if update_bankroll(matches_sheet, saved_br + amt): 
                st.rerun()
    with c2:
        if st.button("Withdraw", use_container_width=True):
            if update_bankroll(matches_sheet, saved_br - amt): 
                st.rerun()
    
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
        
        comp_name = st.text_input("Competition Name *")
        comp_initial_bet = st.number_input("Initial Bet (₪) *", min_value=1.0, value=30.0)
        comp_goal = st.text_area("Goal (Optional)")
        comp_logo = st.text_input("Logo URL (Optional)")
        
        c1, c2 = st.columns(2)
        with c1: 
            comp_color1 = st.color_picker("Color 1", "#4CABFF")
        with c2: 
            comp_color2 = st.color_picker("Color 2", "#E6F7FF")
        
        comp_text_color = st.color_picker("Text Color", "#004085")
        
        col_submit, col_cancel = st.columns(2)
        with col_submit:
            if st.form_submit_button("✅ Create", use_container_width=True):
                if comp_name:
                    if add_competition(competitions_sheet, comp_name, comp_initial_bet, comp_goal, comp_logo or APP_LOGO_URL, comp_color1, comp_color2, comp_text_color):
                        st.success(f"✅ '{comp_name}' created!")
                        st.session_state.show_new_comp_modal = False
                        st.rerun()
                else:
                    st.warning("Please enter a name")
        
        with col_cancel:
            if st.form_submit_button("❌ Cancel", use_container_width=True):
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
            comp_config = get_competition_config(stat['Competition'], competitions_data)
            if comp_config:
                logo_src = comp_config['logo']
                gradient = f"linear-gradient(90deg, {comp_config['color1']} 0%, {comp_config['color2']} 50%, {comp_config['color1']} 100%)"
                text_color = comp_config['text_color']
            else:
                logo_src = APP_LOGO_URL
                gradient = "linear-gradient(90deg, #1b4332 0%, #40916c 100%)"
                text_color = "#FFFFFF"
            
            profit_color = "#2d6a4f" if stat['Net Profit'] >= 0 else "#d32f2f"
            
            st.markdown(f"""
<div style="background: {gradient}; border-radius: 15px; padding: 20px; margin-bottom: 15px; box-shadow: 0 8px 20px rgba(0,0,0,0.4);">
    <div style="display: flex; align-items: center; justify-content: center; margin-bottom: 15px;">
        <img src="{logo_src}" style="height: 50px; margin-right: 15px;">
        <h2 style="margin: 0; font-size: 1.5rem; font-weight: 900; color: {text_color};">{stat['Competition']}</h2>
    </div>
    <div style="background: rgba(255,255,255,0.95); border-radius: 10px; padding: 15px;">
        <div style="display: flex; justify-content: space-around; text-align: center;">
            <div><div style="font-size: 0.7rem; color: #666;">Matches</div><div style="font-size: 1.2rem; font-weight: 900; color: #1b4332;">{stat['Matches']}</div></div>
            <div><div style="font-size: 0.7rem; color: #666;">Wins</div><div style="font-size: 1.2rem; font-weight: 900; color: #1b4332;">{stat['Wins']}</div></div>
            <div><div style="font-size: 0.7rem; color: #666;">Profit</div><div style="font-size: 1.2rem; font-weight: 900; color: {profit_color};">₪{stat['Net Profit']:,.0f}</div></div>
            <div><div style="font-size: 0.7rem; color: #666;">ROI %</div><div style="font-size: 1.2rem; font-weight: 900; color: {profit_color};">{stat['Profit %']:.1f}%</div></div>
        </div>
    </div>
</div>
            """, unsafe_allow_html=True)
    else:
        st.info("No competitions yet. Create one using the button above!")

elif track == "📚 History":
    st.markdown("<h1 style='text-align: center; color: white;'>📚 Competition History</h1>", unsafe_allow_html=True)
    
    archived = [c for c in competitions_data if c.get('Status') == 'Archived']
    if archived:
        for comp in archived:
            comp_name = comp.get('Competition Name')
            final_profit = comp.get('Final Profit', 0)
            closed_date = comp.get('Closed Date', 'N/A')
            
            st.markdown(f"""
<div style="background: rgba(255,255,255,0.95); border-radius: 15px; padding: 20px; margin-bottom: 15px;">
    <h3 style="color: black; margin: 0 0 10px 0;">{comp_name} <span style="font-size:0.8rem; color:#888;">(ARCHIVED)</span></h3>
    <div style="color: black;"><strong>Closed:</strong> {closed_date}</div>
    <div style="color: black;"><strong>Final Profit:</strong> ₪{final_profit:,.0f}</div>
</div>
            """, unsafe_allow_html=True)
            
            if st.button(f"🔓 Reopen {comp_name}", key=f"reopen_{comp_name}"):
                if reopen_competition(competitions_sheet, comp_name):
                    st.success(f"Reopened {comp_name}!")
                    st.rerun()
    else:
        st.info("No archived competitions yet.")

else:
    # Active Competition Page
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
    with c1:
        st.markdown(f"""<div class="custom-metric-box"><div class="metric-card-label">TOTAL EXPENSES</div><div class="metric-card-value">₪{m_exp:,.0f}</div></div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class="custom-metric-box"><div class="metric-card-label">TOTAL REVENUE</div><div class="metric-card-value">₪{m_inc:,.0f}</div></div>""", unsafe_allow_html=True)
    with c3:
        color_net = '#2d6a4f' if m_net >= 0 else '#d32f2f'
        st.markdown(f"""<div class="custom-metric-box"><div class="metric-card-label">NET PROFIT</div><div class="metric-card-value" style="color: {color_net} !important;">₪{m_net:,.0f}</div></div>""", unsafe_allow_html=True)

    next_val = next_stakes.get(track, initial_bet)
    st.markdown(f"""<div style="text-align: center; margin: 30px 0;"><span style="font-size: 1.4rem; color: white;">Next Bet: </span><span style="font-size: 1.6rem; color: #4CAF50; font-weight: 900;">₪{next_val:,.0f}</span></div>""", unsafe_allow_html=True)

    col_form, col_chart = st.columns([1, 1])
    with col_form:
        with st.form("new_match"):
            st.subheader("Add Match")
            h_team = st.text_input("Home Team")
            a_team = st.text_input("Away Team")
            odds_val = st.number_input("Odds", value=3.2, step=0.1)
            stake_val = st.number_input("Stake", value=float(next_val), step=10.0)
            result_val = st.radio("Result", ["Pending", "Draw (X)", "No Draw"], horizontal=True)
            
            if st.form_submit_button("Submit Game", use_container_width=True):
                if h_team and a_team:
                    if add_match_to_sheet(matches_sheet, str(datetime.date.today()), track, h_team, a_team, odds_val, result_val, stake_val):
                        st.toast("Match Added!", icon="✅")
                        st.rerun()
                else:
                    st.warning("Please enter team names")

    with col_chart:
        st.subheader("Performance")
        if not f_df.empty:
            f_df['Balance'] = saved_br + (f_df['Income'].cumsum() - f_df['Expense'].cumsum())
            fig = px.line(f_df, y='Balance', x=f_df.index, title=None)
            fig.update_traces(line_color='#00ff88', line_width=3)
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0.2)',
                font=dict(color='white'),
                margin=dict(l=20, r=20, t=20, b=20),
                height=300
            )
            st.plotly_chart(fig, use_container_width=True)
            wins = len(f_df[f_df['Status'] == "✅ Won"])
            losses = len(f_df[f_df['Status'] == "❌ Lost"])
            rate = (wins / len(f_df) * 100) if len(f_df) > 0 else 0
            st.caption(f"Win Rate: {rate:.1f}% ({wins} W / {losses} L)")

    # Close Competition Button
    if st.button("🏁 Close Competition", use_container_width=True, type="secondary"):
        if close_competition(competitions_sheet, track, m_net):
            st.success(f"Competition '{track}' archived!")
            st.rerun()

    # Activity Log
    st.markdown("""<h2 style="color: #ffffff !important; text-shadow: 3px 3px 8px rgba(0,0,0,1) !important; font-weight: 900 !important; margin-bottom: 20px !important;">📜 Activity Log</h2>""", unsafe_allow_html=True)
    
    if not f_df.empty:
        f_df_sorted = f_df.sort_index(ascending=False)
        
        for idx, match in f_df_sorted.iterrows():
            if 'Won' in str(match['Status']):
                card_class = "activity-card-won"
            elif 'Pending' in str(match['Status']):
                card_class = "activity-card-pending"
            else:
                card_class = "activity-card-lost"
            
            profit_color = "#2d6a4f" if match['Net Profit'] >= 0 else "#d32f2f"
            
            # Update buttons for pending matches
            if 'Pending' in str(match['Status']):
                st.markdown("#### ⏳ Update Result")
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    st.write(f"**{match['Match']}**")
                with col2:
                    if st.button("✅ Draw (Won)", key=f"w_{idx}", use_container_width=True):
                        if update_match_result(matches_sheet, int(match['Row']), "Draw (X)"):
                            st.success("Updated!")
                            st.rerun()
                with col3:
                    if st.button("❌ No Draw (Lost)", key=f"l_{idx}", use_container_width=True):
                        if update_match_result(matches_sheet, int(match['Row']), "No Draw"):
                            st.success("Updated!")
                            st.rerun()
            
            # Display card
            st.markdown(f"""
<div class="activity-card {card_class}">
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <div>
            <div style="font-weight: 900; font-size: 1.1rem; color: #1a1a1a; text-shadow: none;">{match['Match']}</div>
            <div style="color: #555; font-size: 0.85rem; text-shadow: none;">📅 {match['Date']}</div>
        </div>
        <div style="text-align: right;">
            <div style="font-weight: 900; font-size: 1.3rem; color: {profit_color}; text-shadow: none;">₪{match['Net Profit']:,.0f}</div>
            <div style="font-size: 0.85rem; color: #1a1a1a; text-shadow: none;">{match['Status']}</div>
        </div>
    </div>
    <div style="display: flex; gap: 15px; margin-top: 10px; flex-wrap: wrap;">
        <div style="flex: 1; min-width: 80px; background: rgba(255,255,255,0.7); padding: 8px; border-radius: 6px; text-align: center;">
            <div style="font-size: 0.7rem; color: #666; text-shadow: none;">ODDS</div>
            <div style="font-size: 1rem; font-weight: 700; color: #1a1a1a; text-shadow: none;">{match['Odds']:.2f}</div>
        </div>
        <div style="flex: 1; min-width: 80px; background: rgba(255,255,255,0.7); padding: 8px; border-radius: 6px; text-align: center;">
            <div style="font-size: 0.7rem; color: #666; text-shadow: none;">STAKE</div>
            <div style="font-size: 1rem; font-weight: 700; color: #1a1a1a; text-shadow: none;">₪{match['Expense']:,.0f}</div>
        </div>
        <div style="flex: 1; min-width: 80px; background: rgba(255,255,255,0.7); padding: 8px; border-radius: 6px; text-align: center;">
            <div style="font-size: 0.7rem; color: #666; text-shadow: none;">RETURN</div>
            <div style="font-size: 1rem; font-weight: 700; color: #1a1a1a; text-shadow: none;">₪{match['Income']:,.0f}</div>
        </div>
        <div style="flex: 1; min-width: 80px; background: rgba(255,255,255,0.7); padding: 8px; border-radius: 6px; text-align: center;">
            <div style="font-size: 0.7rem; color: #666; text-shadow: none;">ROI</div>
            <div style="font-size: 1rem; font-weight: 700; color: #1a1a1a; text-shadow: none;">{match['ROI']}</div>
        </div>
    </div>
</div>
            """, unsafe_allow_html=True)
    else:
        st.info("No matches found for this competition.")

    with st.expander("🛠️ Admin Actions"):
        if st.button("Undo Last Entry"):
            if len(raw_data) > 0:
                if delete_last_row(matches_sheet, len(raw_data)):
                    st.toast("Last entry deleted", icon="✅")
                    st.rerun()
            else:
                st.warning("No entries to delete")