import streamlit as st
import pandas as pd
import plotly.express as px
import gspread
import datetime

# --- Page Configuration ---
st.set_page_config(
    page_title="Elite Football Tracker",
    layout="wide",
    page_icon="🏟️",
    initial_sidebar_state="expanded"
)

# --- GLOBAL STYLES & BACKGROUND ---
bg_img_url = "https://i.postimg.cc/GmFZ4KS7/Gemini-Generated-Image-k1h11zk1h11zk1h1.png"

st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;700;900&family=Inter:wght@400;700&display=swap');
    
    /* 1. Main Background Fix */
    [data-testid="stAppViewContainer"] {{
        background-image: linear-gradient(rgba(0, 0, 0, 0.4), rgba(0, 0, 0, 0.6)), url("{bg_img_url}");
        background-attachment: fixed;
        background-size: cover;
        background-position: center;
    }}
    
    /* 2. Header Transparency */
    [data-testid="stHeader"] {{ background: rgba(0,0,0,0); }}

    /* 3. Text Visibility Optimization (Pop Effect) */
    h1, h2, h3, p, label, .stMarkdown, div[data-testid="stMetricLabel"] {{
        color: #ffffff !important;
        text-shadow: 2px 2px 4px #000000;
        font-family: 'Montserrat', sans-serif;
    }}
    
    /* Exception: Text inside white cards needs to be dark */
    div[data-testid="stForm"] label, div[data-testid="stForm"] p, 
    .metric-card-text, .metric-card-value, .metric-card-label {{
        color: #000000 !important;
        text-shadow: none !important;
    }}

    /* 4. Sidebar Styling */
    [data-testid="stSidebar"] {{
        background-color: rgba(0, 0, 0, 0.7) !important;
        backdrop-filter: blur(10px);
        border-right: 1px solid rgba(255,255,255,0.2);
    }}

    /* 5. Custom Metric Cards (White Box) */
    .custom-metric-box {{
        background-color: rgba(255, 255, 255, 0.95);
        border-radius: 15px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.5);
        margin-bottom: 20px;
    }}
    .metric-card-label {{
        font-size: 14px;
        font-weight: bold;
        text-transform: uppercase;
        color: #555 !important;
    }}
    .metric-card-value {{
        font-size: 32px;
        font-weight: 900;
        color: #1b4332 !important;
    }}

    /* 6. Form Styling */
    div[data-testid="stForm"] {{
        background-color: rgba(255, 255, 255, 0.95);
        border-radius: 20px;
        padding: 30px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    }}
    </style>
""", unsafe_allow_html=True)

# --- LOGIC (UNCHANGED) ---
def get_data_from_sheets():
    try:
        gc = gspread.service_account_from_dict(st.secrets["service_account"])
        sh = gc.open_by_url(st.secrets["sheet_url"])
        worksheet = sh.get_worksheet(0)
        data = worksheet.get_all_records()
        try:
            val = worksheet.cell(1, 10).value
            initial_bankroll = float(val) if val else 5000.0
        except: initial_bankroll = 5000.0
        return data, worksheet, initial_bankroll
    except Exception as e:
        st.error(f"Sync Error: {e}")
        return [], None, 5000.0

def update_bankroll(worksheet, val):
    try:
        worksheet.update_cell(1, 10, val)
        return True
    except: return False

def calculate_logic(raw_data, br_base, af_base):
    processed = []
    next_bets = {"Brighton": float(br_base), "Africa Cup of Nations": float(af_base)}
    cycle_invest = {"Brighton": 0.0, "Africa Cup of Nations": 0.0}

    for i, row in enumerate(raw_data):
        try:
            comp = str(row.get('Competition', 'Brighton')).strip()
            odds = float(str(row.get('Odds', 1)).replace(',', '.'))
            res = str(row.get('Result', '')).strip()
            exp = float(row.get('Stake', next_bets[comp]))
            cycle_invest[comp] += exp
            is_win = "Draw (X)" in res
            
            if is_win:
                inc = exp * odds
                net = inc - cycle_invest[comp]
                roi = f"{(net / cycle_invest[comp]) * 100:.1f}%"
                next_bets[comp] = float(br_base if "Brighton" in comp else af_base)
                cycle_invest[comp] = 0.0
                status = "✅ Won"
            else:
                inc, net, roi = 0.0, -exp, "N/A"
                next_bets[comp] = exp * 2.0
                status = "❌ Lost"
            
            processed.append({
                "Date": row.get('Date', ''), "Comp": comp, "Match": f"{row.get('Home Team', '')} vs {row.get('Away Team', '')}",
                "Odds": odds, "Expense": exp, "Income": inc, "Net Profit": net, "Status": status, "ROI": roi
            })
        except: continue
    return processed, next_bets

# --- DATA LOADING ---
raw_data, worksheet, saved_br = get_data_from_sheets()
processed, next_stakes = calculate_logic(raw_data, 30.0, 20.0)

if processed:
    df = pd.DataFrame(processed)
    current_bal = saved_br + (df['Income'].sum() - df['Expense'].sum())
else:
    current_bal, df = saved_br, pd.DataFrame()

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("## WALLET CONTROL")
    st.metric("Base Bankroll", f"₪{saved_br:,.0f}")
    amt = st.number_input("Transaction Amount", min_value=0.0, value=100.0)
    c1, c2 = st.columns(2)
    if c1.button("Deposit"):
        if update_bankroll(worksheet, saved_br + amt): st.rerun()
    if c2.button("Withdraw"):
        if update_bankroll(worksheet, saved_br - amt): st.rerun()
    st.divider()
    track = st.selectbox("Current Track", ["Brighton", "Africa Cup of Nations"])
    if st.button("🔄 Sync Cloud"): st.rerun()

# --- THE CUSTOM HEADER COMPONENT (HTML/CSS INJECTION) ---
# This ensures the banner is exactly as requested, regardless of Streamlit themes
brighton_logo = "https://i.postimg.cc/x8kdQh5H/Brighton_Hove_Albion_logo.png"
afcon_logo = "https://i.postimg.cc/5yHtJTgz/2025_Africa_Cup_of_Nations_logo.png"

if track == "Brighton":
    banner_bg = "linear-gradient(90deg, #0057B8 0%, #FFFFFF 50%, #4CABFF 100%)"
    text_color = "#0057B8" # Blue text for contrast against white center
    logo_src = brighton_logo
    shadow_style = "none" # Clean look for blue text
else:
    banner_bg = "linear-gradient(90deg, #CE1126 0%, #FCD116 50%, #007A33 100%)"
    text_color = "#FFFFFF" # White text
    logo_src = afcon_logo
    shadow_style = "2px 2px 4px #000000" # Shadow for white text

# Injecting the Banner HTML
st.markdown(f"""
    <div style="
        background: {banner_bg};
        border-radius: 20px;
        padding: 20px;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-bottom: 40px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.5);
        border: 2px solid rgba(255,255,255,0.3);
    ">
        <img src="{logo_src}" style="height: 100px; margin-right: 25px; filter: drop-shadow(0 5px 5px rgba(0,0,0,0.3));">
        <h1 style="
            margin: 0;
            font-size: 3.5rem;
            font-weight: 900;
            text-transform: uppercase;
            color: {text_color} !important;
            text-shadow: {shadow_style};
            font-family: 'Montserrat', sans-serif;
        ">{track.upper()}</h1>
    </div>
""", unsafe_allow_html=True)

# --- LIVE BALANCE HERO ---
st.markdown(f"""
    <div style="text-align: center; margin-bottom: 40px;">
        <div style="font-size: 6rem; font-weight: 900; color: white; text-shadow: 4px 4px 10px #000; line-height: 1;">
            ₪{current_bal:,.2f}
        </div>
        <div style="font-size: 1.2rem; font-weight: bold; color: #ddd; letter-spacing: 5px; text-shadow: 2px 2px 5px #000;">
            LIVE BANKROLL
        </div>
    </div>
""", unsafe_allow_html=True)

# --- METRIC CARDS ---
f_df = df[df['Comp'] == track] if not df.empty else pd.DataFrame()
t_exp = f_df['Expense'].sum() if not f_df.empty else 0.0
t_inc = f_df['Income'].sum() if not f_df.empty else 0.0
t_net = t_inc - t_exp

# Using HTML columns for perfect styling control
c1, c2, c3 = st.columns(3)
with c1:
    st.markdown(f"""
        <div class="custom-metric-box">
            <div class="metric-card-label">TOTAL OUT</div>
            <div class="metric-card-value">₪{t_exp:,.0f}</div>
        </div>
    """, unsafe_allow_html=True)
with c