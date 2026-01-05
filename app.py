import streamlit as st
import pandas as pd
import plotly.express as px
import gspread
import datetime

# --- 1. CONFIGURATION ---
APP_LOGO_URL = "https://i.postimg.cc/8Cr6SypK/yzwb-ll-sm.png"
BG_IMAGE_URL = "https://i.postimg.cc/GmFZ4KS7/Gemini-Generated-Image-k1h11zk1h11zk1h1.png"

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
    [data-testid="stSidebar"] input {{
        color: #000000 !important;
        background-color: #ffffff !important;
        border: 1px solid #ccc;
    }}
    [data-testid="stSidebar"] button {{
        color: #ffffff !important;
    }}

    .main h1, .main h2, .main h3, .main h4, .main p {{
        color: #ffffff !important;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.8);
    }}

    [data-testid="stDataFrame"] {{ background-color: white !important; border-radius: 8px; }}
    [data-testid="stDataFrame"] * {{ color: #000000 !important; text-shadow: none !important; }}
    [data-testid="stForm"] {{ background-color: rgba(255, 255, 255, 0.95); border-radius: 15px; padding: 25px; }}
    [data-testid="stForm"] * {{ color: #000000 !important; text-shadow: none !important; }}

    .custom-metric-box {{
        background-color: rgba(255, 255, 255, 0.95);
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }}
    .metric-card-label {{ color: #555 !important; font-weight: 700; font-size: 13px; text-shadow: none !important; }}
    .metric-card-value {{ color: #1b4332 !important; font-weight: 900; font-size: 26px; text-shadow: none !important; }}

    /* NEW ACTIVITY LOG DESIGN */
    .activity-card {{
        border-radius: 15px !important;
        padding: 25px !important;
        margin-bottom: 20px !important;
        box-shadow: 0 8px 25px rgba(0,0,0,0.4) !important;
        transition: all 0.3s ease !important;
        position: relative !important;
        overflow: hidden !important;
    }}
    .activity-card::before {{
        content: '' !important;
        position: absolute !important;
        top: 0 !important;
        left: 0 !important;
        right: 0 !important;
        height: 4px !important;
        transition: height 0.3s ease !important;
    }}
    .activity-card:hover {{
        transform: translateY(-5px) !important;
        box-shadow: 0 12px 35px rgba(0,0,0,0.5) !important;
    }}
    .activity-card:hover::before {{
        height: 6px !important;
    }}
    .activity-card-won {{
        background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 50%, #b1dfbb 100%) !important;
        border-left: 6px solid #28a745 !important;
    }}
    .activity-card-won::before {{
        background: linear-gradient(90deg, #28a745 0%, #20c997 100%) !important;
    }}
    .activity-card-lost {{
        background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 50%, #f1b0b7 100%) !important;
        border-left: 6px solid #dc3545 !important;
    }}
    .activity-card-lost::before {{
        background: linear-gradient(90deg, #dc3545 0%, #c82333 100%) !important;
    }}
    .activity-card-pending {{
        background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 50%, #fdcb6e 100%) !important;
        border-left: 6px solid #ffc107 !important;
    }}
    .activity-card-pending::before {{
        background: linear-gradient(90deg, #ffc107 0%, #ffb300 100%) !important;
    }}
    .activity-header {{
        display: flex !important;
        justify-content: space-between !important;
        align-items: center !important;
        margin-bottom: 15px !important;
        padding-bottom: 12px !important;
        border-bottom: 2px solid rgba(0,0,0,0.1) !important;
    }}
    .activity-match {{
        font-size: 1.2rem !important;
        font-weight: 900 !important;
        color: #1a1a1a !important;
        text-shadow: none !important;
        letter-spacing: 0.5px !important;
    }}
    .activity-date {{
        font-size: 0.9rem !important;
        color: #555 !important;
        text-shadow: none !important;
        font-weight: 600 !important;
        margin-top: 3px !important;
    }}
    .activity-stats {{
        display: flex !important;
        flex-wrap: wrap !important;
        gap: 20px !important;
        margin-top: 15px !important;
    }}
    .activity-stat-item {{
        flex: 1 !important;
        min-width: 90px !important;
        background: rgba(255, 255, 255, 0.7) !important;
        padding: 10px !important;
        border-radius: 8px !important;
        text-align: center !important;
        transition: all 0.2s ease !important;
    }}
    .activity-stat-item:hover {{
        background: rgba(255, 255, 255, 0.9) !important;
        transform: scale(1.05) !important;
    }}
    .activity-stat-label {{
        font-size: 0.7rem !important;
        color: #666 !important;
        text-transform: uppercase !important;
        letter-spacing: 1px !important;
        text-shadow: none !important;
        font-weight: 700 !important;
        margin-bottom: 5px !important;
    }}
    .activity-stat-value {{
        font-size: 1.1rem !important;
        font-weight: 900 !important;
        color: #1a1a1a !important;
        text-shadow: none !important;
    }}
    .activity-status {{
        display: inline-block !important;
        padding: 8px 16px !important;
        border-radius: 25px !important;
        font-size: 0.9rem !important;
        font-weight: 900 !important;
        text-shadow: none !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.2) !important;
        transition: all 0.2s ease !important;
    }}
    .activity-status:hover {{
        transform: scale(1.05) !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3) !important;
    }}
    .status-won {{
        background: linear-gradient(135deg, #28a745 0%, #20c997 100%) !important;
        color: #ffffff !important;
    }}
    .status-lost {{
        background: linear-gradient(135deg, #dc3545 0%, #c82333 100%) !important;
        color: #ffffff !important;
    }}
    .status-pending {{
        background: linear-gradient(135deg, #ffc107 0%, #ff9800 100%) !important;
        color: #ffffff !important;
    }}

    @media only screen and (max-width: 768px) {{
        .banner-text {{ display: none !important; }}
        .banner-container {{ justify-content: center !important; padding: 10px !important; }}
        .banner-img {{ height: 120px !important; margin: 0 !important; }}
        [data-testid="stDataFrame"] * {{ font-size: 12px !important; }}
    }}
    
    /* Custom Loading Spinner */
    .stSpinner > div {{
        display: none !important;
    }}
    [data-testid="stStatusWidget"] {{
        position: fixed !important;
        top: 50% !important;
        left: 50% !important;
        transform: translate(-50%, -50%) !important;
        z-index: 9999 !important;
        background: rgba(0, 0, 0, 0.9) !important;
        width: 100vw !important;
        height: 100vh !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }}
    [data-testid="stStatusWidget"]::before {{
        content: '' !important;
        width: 80px !important;
        height: 80px !important;
        border: 8px solid rgba(255, 255, 255, 0.2) !important;
        border-top: 8px solid #4CAF50 !important;
        border-radius: 50% !important;
        animation: spin 1s linear infinite !important;
        position: absolute !important;
    }}
    [data-testid="stStatusWidget"]::after {{
        content: 'DRAW IT' !important;
        color: #ffffff !important;
        font-size: 1.5rem !important;
        font-weight: 900 !important;
        font-family: 'Montserrat', sans-serif !important;
        letter-spacing: 3px !important;
        position: absolute !important;
        margin-top: 120px !important;
        text-shadow: 0 0 20px rgba(76, 175, 80, 0.8) !important;
    }}
    @keyframes spin {{
        0% {{ transform: rotate(0deg); }}
        100% {{ transform: rotate(360deg); }}
    }}
    </style>
""", unsafe_allow_html=True)

# --- 3. BACKEND LOGIC ---
@st.cache_data(ttl=30)
def get_data_from_sheets():
    try:
        gc = gspread.service_account_from_dict(st.secrets["service_account"])
        sh = gc.open_by_url(st.secrets["sheet_url"])
        worksheet = sh.get_worksheet(0)
        data = worksheet.get_all_records()
        try:
            val = worksheet.cell(1, 10).value
            initial_bankroll = float(str(val).replace(',', '')) if val else 5000.0
        except (ValueError, AttributeError, TypeError):
            initial_bankroll = 5000.0
        return data, worksheet, initial_bankroll
    except gspread.exceptions.APIError as e:
        st.error(f"Google Sheets API Error: {e}")
        return [], None, 5000.0
    except Exception as e:
        st.error(f"Connection Error: {e}")
        return [], None, 5000.0

def update_bankroll(worksheet, val):
    if worksheet is None:
        return False
    try:
        worksheet.update_cell(1, 10, val)
        get_data_from_sheets.clear()
        return True
    except:
        return False

def safe_float_conversion(value, default=0.0):
    try:
        return float(str(value).replace(',', '.'))
    except (ValueError, AttributeError, TypeError):
        return default

def calculate_logic(raw_data, br_base, af_base):
    processed = []
    next_bets = {"Brighton": float(br_base), "Africa Cup of Nations": float(af_base)}
    cycle_invest = {"Brighton": 0.0, "Africa Cup of Nations": 0.0}

    for idx, row in enumerate(raw_data):
        try:
            comp = str(row.get('Competition', 'Brighton')).strip()
            if not comp:
                comp = 'Brighton'
            odds = safe_float_conversion(row.get('Odds', 1), 1.0)
            stake_val = row.get('Stake')
            if stake_val in [None, '', ' ']:
                exp = next_bets[comp]
            else:
                exp = safe_float_conversion(stake_val, next_bets[comp])
            res = str(row.get('Result', '')).strip()
            
            if res == "Pending":
                processed.append({
                    "Row": idx + 2,
                    "Date": row.get('Date', ''),
                    "Comp": comp,
                    "Match": f"{row.get('Home Team','')} vs {row.get('Away Team','')}",
                    "Odds": odds,
                    "Expense": 0.0,
                    "Income": 0.0,
                    "Net Profit": 0.0,
                    "Status": "⏳ Pending",
                    "ROI": "N/A"
                })
                continue
            
            cycle_invest[comp] += exp
            is_win = "Draw (X)" in res
            
            if is_win:
                inc = exp * odds
                net = inc - cycle_invest[comp]
                try:
                    roi = f"{(net / cycle_invest[comp]) * 100:.1f}%"
                except ZeroDivisionError:
                    roi = "0.0%"
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
                "Row": idx + 2,
                "Date": row.get('Date', ''),
                "Comp": comp,
                "Match": f"{row.get('Home Team','')} vs {row.get('Away Team','')}",
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
    if df.empty:
        return []
    stats = []
    for comp in df['Comp'].unique():
        comp_df = df[df['Comp'] == comp].copy()
        comp_df_sorted = comp_df.sort_values('Date') if 'Date' in comp_df.columns else comp_df
        first_date = comp_df_sorted.iloc[0]['Date'] if len(comp_df_sorted) > 0 else ''
        total_matches = len(comp_df)
        wins = len(comp_df[comp_df['Status'] == "✅ Won"])
        total_expense = comp_df['Expense'].sum()
        total_income = comp_df['Income'].sum()
        net_profit = total_income - total_expense
        profit_pct = (net_profit / initial_bankroll * 100) if initial_bankroll > 0 else 0
        stats.append({
            'Competition': comp,
            'First Date': first_date,
            'Matches': total_matches,
            'Wins': wins,
            'Net Profit': net_profit,
            'Profit %': profit_pct
        })
    stats_df = pd.DataFrame(stats)
    if not stats_df.empty and 'First Date' in stats_df.columns:
        try:
            stats_df['First Date'] = pd.to_datetime(stats_df['First Date'], errors='coerce')
            stats_df = stats_df.sort_values('First Date', ascending=False)
        except:
            pass
    return stats_df.to_dict('records') if not stats_df.empty else []

def add_match_to_sheet(worksheet, date, comp, home, away, odds, result, stake):
    if worksheet is None:
        st.error("No connection to Google Sheets")
        return False
    try:
        worksheet.append_row([date, comp, home, away, odds, result, stake, 0.0])
        get_data_from_sheets.clear()
        return True
    except:
        return False

def update_match_result(worksheet, row_num, result):
    if worksheet is None:
        return False
    try:
        worksheet.update_cell(row_num, 6, result)
        get_data_from_sheets.clear()
        return True
    except:
        return False

def delete_last_row(worksheet, row_count):
    if worksheet is None or row_count == 0:
        return False
    try:
        worksheet.delete_rows(row_count + 1)
        get_data_from_sheets.clear()
        return True
    except:
        return False

# --- 4. EXECUTION ---
raw_data, worksheet, saved_br = get_data_from_sheets()
processed, next_stakes = calculate_logic(raw_data, 30.0, 20.0)

if processed:
    df = pd.DataFrame(processed)
    current_bal = saved_br + (df['Income'].sum() - df['Expense'].sum())
else:
    df = pd.DataFrame()
    current_bal = saved_br

# --- 5. UI LAYOUT ---
with st.sidebar:
    try:
        st.image(APP_LOGO_URL, use_container_width=True)
    except:
        pass
    st.markdown("## WALLET CONTROL")
    st.metric("Base Bankroll", f"₪{saved_br:,.0f}")
    st.write("Transaction Amount:")
    amt = st.number_input("Amount", min_value=0.0, value=100.0, step=50.0, label_visibility="collapsed")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Deposit", use_container_width=True):
            if update_bankroll(worksheet, saved_br + amt):
                st.rerun()
    with c2:
        if st.button("Withdraw", use_container_width=True):
            if update_bankroll(worksheet, saved_br - amt):
                st.rerun()
    st.divider()
    st.write("Current Track:")
    track = st.selectbox("Track", ["📊 Overview", "Brighton", "Africa Cup of Nations"], label_visibility="collapsed")
    if st.button("🔄 Sync Cloud", use_container_width=True):
        get_data_from_sheets.clear()
        st.rerun()

if track == "📊 Overview":
    st.markdown(f"""
        <div style="background: linear-gradient(90deg, #40916c 0%, #95d5b2 50%, #40916c 100%); border-radius: 15px; padding: 20px; display: flex !important; align-items: center !important; justify-content: center !important; margin-bottom: 30px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); border: 2px solid rgba(255,255,255,0.4);">
            <img src="{APP_LOGO_URL}" style="height: 70px !important; margin-right: 25px !important; filter: drop-shadow(0 4px 6px rgba(0,0,0,0.3)) !important;">
            <h1 style="margin: 0 !important; font-size: 2.2rem !important; font-weight: 900 !important; text-transform: uppercase !important; color: #081c15 !important; text-shadow: 1px 1px 2px rgba(255,255,255,0.3) !important; font-family: 'Montserrat', sans-serif !important; letter-spacing: 2px !important;">OVERVIEW</h1>
        </div>
    """, unsafe_allow_html=True)
    st.markdown(f"""
        <div style="text-align: center; margin-bottom: 50px;">
            <div style="font-size: 2.3rem; font-weight: 300; color: #ffffff; text-shadow: 0 0 20px rgba(255,255,255,0.3); line-height: 1; margin-bottom: 8px;">₪{current_bal:,.2f}</div>
            <div style="font-size: 0.8rem; font-weight: 600; color: #cccccc; letter-spacing: 3px; text-transform: uppercase;">LIVE BANKROLL</div>
        </div>
    """, unsafe_allow_html=True)
    
    comp_stats = get_competition_stats(df, saved_br)
    brighton_logo = "https://i.postimg.cc/x8kdQh5H/Brighton_Hove_Albion_logo.png"
    afcon_logo = "https://i.postimg.cc/5yHtJTgz/2025_Africa_Cup_of_Nations_logo.png"
    
    if comp_stats:
        for stat in comp_stats:
            comp_name = stat['Competition']
            if "Brighton" in comp_name or "brighton" in comp_name.lower():
                logo_src = brighton_logo
                gradient = "linear-gradient(90deg, #4CABFF 0%, #E6F7FF 50%, #4CABFF 100%)"
                text_color = "#004085"
                shadow_style = "none"
            elif "Africa" in comp_name or "africa" in comp_name.lower():
                logo_src = afcon_logo
                gradient = "linear-gradient(90deg, #CE1126 0%, #FCD116 50%, #007A33 100%)"
                text_color = "#FFFFFF"
                shadow_style = "2px 2px 4px #000000"
            else:
                logo_src = APP_LOGO_URL
                gradient = "linear-gradient(90deg, #1b4332 0%, #40916c 100%)"
                text_color = "#FFFFFF"
                shadow_style = "2px 2px 4px rgba(0,0,0,0.5)"
            profit_color = "#2d6a4f" if stat['Net Profit'] >= 0 else "#d32f2f"
            st.markdown(f"""
<div style="background: {gradient}; border-radius: 15px; padding: 25px; margin-bottom: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); border: 2px solid rgba(255,255,255,0.4);">
    <div style="display: flex; align-items: center; margin-bottom: 20px;">
        <img src="{logo_src}" style="height: 60px; margin-right: 20px; filter: drop-shadow(0 4px 6px rgba(0,0,0,0.3));">
        <h2 style="margin: 0; font-size: 1.8rem; font-weight: 900; text-transform: uppercase; color: {text_color}; text-shadow: {shadow_style}; font-family: 'Montserrat', sans-serif; letter-spacing: 2px;">{comp_name}</h2>
    </div>
    <div style="background-color: rgba(255, 255, 255, 0.95); border-radius: 10px; padding: 20px;">
        <div style="display: flex; flex-wrap: wrap; gap: 30px;">
            <div style="flex: 1; min-width: 120px;"><div style="font-size: 0.75rem; color: #666; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px; text-shadow: none;">Matches</div><div style="font-size: 1.6rem; font-weight: 900; color: #1b4332; text-shadow: none;">{stat['Matches']}</div></div>
            <div style="flex: 1; min-width: 120px;"><div style="font-size: 0.75rem; color: #666; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px; text-shadow: none;">Wins</div><div style="font-size: 1.6rem; font-weight: 900; color: #1b4332; text-shadow: none;">{stat['Wins']}</div></div>
            <div style="flex: 1; min-width: 120px;"><div style="font-size: 0.75rem; color: #666; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px; text-shadow: none;">Net Profit</div><div style="font-size: 1.6rem; font-weight: 900; color: {profit_color}; text-shadow: none;">₪{stat['Net Profit']:,.0f}</div></div>
            <div style="flex: 1; min-width: 120px;"><div style="font-size: 0.75rem; color: #666; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px; text-shadow: none;">Profit %</div><div style="font-size: 1.6rem; font-weight: 900; color: {profit_color}; text-shadow: none;">{stat['Profit %']:.1f}%</div></div>
        </div>
    </div>
</div>
            """, unsafe_allow_html=True)
    else:
        st.info("No competitions yet. Start betting!")

else:
    brighton_logo = "https://i.postimg.cc/x8kdQh5H/Brighton_Hove_Albion_logo.png"
    afcon_logo = "https://i.postimg.cc/5yHtJTgz/2025_Africa_Cup_of_Nations_logo.png"

    if track == "Brighton":
        banner_bg = "linear-gradient(90deg, #4CABFF 0%, #E6F7FF 50%, #4CABFF 100%)"
        text_color = "#004085"
        logo_src = brighton_logo
        shadow_style = "none"
    else:
        banner_bg = "linear-gradient(90deg, #CE1126 0%, #FCD116 50%, #007A33 100%)"
        text_color = "#FFFFFF"
        logo_src = afcon_logo
        shadow_style = "2px 2px 4px #000000"

    st.markdown(f"""
        <div style="background: {banner_bg}; border-radius: 15px; padding: 20px; display: flex !important; align-items: center !important; justify-content: center !important; margin-bottom: 30px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); border: 2px solid rgba(255,255,255,0.4);">
            <img src="{logo_src}" style="height: 70px !important; margin-right: 25px !important; filter: drop-shadow(0 4px 6px rgba(0,0,0,0.3)) !important;">
            <h1 style="margin: 0 !important; font-size: 2.2rem !important; font-weight: 900 !important; text-transform: uppercase !important; color: {text_color} !important; text-shadow: {shadow_style} !important; font-family: 'Montserrat', sans-serif !important; letter-spacing: 2px !important;">{track.upper()}</h1>
        </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
        <div style="text-align: center; margin-bottom: 35px;">
            <div style="font-size: 2.3rem; font-weight: 300; color: #ffffff; text-shadow: 0 0 20px rgba(255,255,255,0.3); line-height: 1; margin-bottom: 8px;">₪{current_bal:,.2f}</div>
            <div style="font-size: 0.8rem; font-weight: 600; color: #cccccc; letter-spacing: 3px; text-transform: uppercase;">LIVE BANKROLL</div>
        </div>
    """, unsafe_allow_html=True)

    if not df.empty:
        f_df = df[df['Comp'] == track].copy()
    else:
        f_df = pd.DataFrame()

    if not f_df.empty:
        m_exp = f_df['Expense'].sum()
        m_inc = f_df['Income'].sum()
        m_net = m_inc - m_exp
    else:
        m_exp = 0.0
        m_inc = 0.0
        m_net = 0.0

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"""<div class="custom-metric-box"><div class="metric-card-label">TOTAL EXPENSES</div><div class="metric-card-value">₪{m_exp:,.0f}</div></div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class="custom-metric-box"><div class="metric-card-label">TOTAL REVENUE</div><div class="metric-card-value">₪{m_inc:,.0f}</div></div>""", unsafe_allow_html=True)
    with c3:
        color_net = '#2d6a4f' if m_net >= 0 else '#d32f2f'
        st.markdown(f"""<div class="custom-metric-box"><div class="metric-card-label">NET PROFIT</div><div class="metric-card-value" style="color: {color_net} !important;">₪{m_net:,.0f}</div></div>""", unsafe_allow_html=True)

    next_val = next_stakes.get(track, 30.0)
    st.markdown(f"""
        <div style="text-align: center; margin: 30px 0;">
            <span style="font-size: 1.4rem; color: white; font-weight: bold;">Next Bet: </span>
            <span style="font-size: 1.6rem; color: #4CAF50; font-weight: 900; text-shadow: 0 0 10px rgba(76,175,80,0.6);">₪{next_val:,.0f}</span>
        </div>
    """, unsafe_allow_html=True)

    col_form, col_chart = st.columns([1, 1])
    with col_form:
        with st.form("new_match"):
            st.subheader("Add Match")
            h_team = st.text_input("Home Team", value="Brighton" if track == "Brighton" else "")
            a_team = st.text_input("Away Team")
            odds_val = st.number_input("Odds", value=3.2, step=0.1)
            stake_val = st.number_input("Stake", value=float(next_val), step=10.0)
            result_val = st.radio("Result", ["Pending", "Draw (X)", "No Draw"], horizontal=True)
            if st.form_submit_button("Submit Game", use_container_width=True):
                if h_team and a_team:
                    if add_match_to_sheet(worksheet, str(datetime.date.today()), track, h_team, a_team, odds_val, result_val, stake_val):
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
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0.2)', font=dict(color='white'), margin=dict(l=20, r=20, t=20, b=20), height=300)
            st.plotly_chart(fig, use_container_width=True)
            wins = len(f_df[f_df['Status'] == "✅ Won"])
            losses = len(f_df[f_df['Status'] == "❌ Lost"])
            rate = (wins / len(f_df) * 100) if len(f_df) > 0 else 0
            st.caption(f"Win Rate: {rate:.1f}% ({wins} W / {losses} L)")

    # Activity Log Header
    st.markdown("""
        <h2 style="color: #ffffff !important; text-shadow: 3px 3px 8px rgba(0,0,0,1) !important; font-weight: 900 !important; font-size: 1.8rem !important; margin-bottom: 20px !important;">
            📜 Activity Log
        </h2>
    """, unsafe_allow_html=True)
    if not f_df.empty:
        f_df_sorted = f_df.sort_index(ascending=False)
        for idx, match in f_df_sorted.iterrows():
            if 'Won' in str(match['Status']):
                card_class = "activity-card-won"
                status_class = "status-won"
            elif 'Pending' in str(match['Status']):
                card_class = "activity-card-pending"
                status_class = "status-pending"
            else:
                card_class = "activity-card-lost"
                status_class = "status-lost"
            profit_color = "#2d6a4f" if match['Net Profit'] >= 0 else "#d32f2f"
            
            # If pending, add update buttons ABOVE the card
            if 'Pending' in str(match['Status']):
                st.markdown("#### ⏳ Update Result")
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    st.write(f"**{match['Match']}**")
                with col2:
                    row_num = int(match.get('Row', 0))
                    if st.button("✅ Draw (Won)", key=f"draw_{row_num}_{idx}", use_container_width=True):
                        if row_num > 0:
                            try:
                                if update_match_result(worksheet, row_num, "Draw (X)"):
                                    st.success("Updated!")
                                    st.rerun()
                                else:
                                    st.error(f"Update failed - Row: {row_num}")
                            except Exception as e:
                                st.error(f"Error: {e}")
                        else:
                            st.error(f"Invalid row number: {row_num}")
                with col3:
                    if st.button("❌ No Draw (Lost)", key=f"nodraw_{row_num}_{idx}", use_container_width=True):
                        if row_num > 0:
                            try:
                                if update_match_result(worksheet, row_num, "No Draw"):
                                    st.success("Updated!")
                                    st.rerun()
                                else:
                                    st.error(f"Update failed - Row: {row_num}")
                            except Exception as e:
                                st.error(f"Error: {e}")
                        else:
                            st.error(f"Invalid row number: {row_num}")
            
            # Display card
            st.markdown(f"""
<div class="activity-card {card_class}">
    <div class="activity-header">
        <div>
            <div class="activity-match">{match['Match']}</div>
            <div class="activity-date">📅 {match['Date']}</div>
        </div>
        <span class="activity-status {status_class}">{match['Status']}</span>
    </div>
    <div class="activity-stats">
        <div class="activity-stat-item"><div class="activity-stat-label">Odds</div><div class="activity-stat-value">{match['Odds']:.2f}</div></div>
        <div class="activity-stat-item"><div class="activity-stat-label">Stake</div><div class="activity-stat-value">₪{match['Expense']:,.0f}</div></div>
        <div class="activity-stat-item"><div class="activity-stat-label">Return</div><div class="activity-stat-value">₪{match['Income']:,.0f}</div></div>
        <div class="activity-stat-item"><div class="activity-stat-label">Profit</div><div class="activity-stat-value" style="color: {profit_color};">₪{match['Net Profit']:,.0f}</div></div>
        <div class="activity-stat-item"><div class="activity-stat-label">ROI</div><div class="activity-stat-value">{match['ROI']}</div></div>
    </div>
</div>
            """, unsafe_allow_html=True)
    else:
        st.info("No matches found.")

    with st.expander("🛠️ Admin Actions"):
        if st.button("Undo Last Entry"):
            if len(raw_data) > 0:
                if delete_last_row(worksheet, len(raw_data)):
                    st.toast("Last entry deleted", icon="✅")
                    st.rerun()
            else:
                st.warning("Empty")