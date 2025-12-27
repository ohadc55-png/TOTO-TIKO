import streamlit as st
import pandas as pd
import plotly.express as px
import gspread
import datetime

# --- 1. CONFIGURATION ---
# שימוש במרכאות כפולות למניעת שגיאות
APP_LOGO_URL = "https://i.postimg.cc/8Cr6SypK/yzwb-ll-sm.png"
BG_IMAGE_URL = "https://i.postimg.cc/GmFZ4KS7/Gemini-Generated-Image-k1h11zk1h11zk1h1.png"

st.set_page_config(
    page_title="Elite Football Tracker",
    layout="wide",
    page_icon=APP_LOGO_URL,
    initial_sidebar_state="expanded"
)

# --- 2. CSS STYLING (The Professional Fix) ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;600;900&family=Inter:wght@400;600&display=swap');
    
    /* MAIN BACKGROUND IMAGE */
    [data-testid="stAppViewContainer"] {{
        background-image: linear-gradient(rgba(0, 0, 0, 0.7), rgba(0, 0, 0, 0.7)), url("{BG_IMAGE_URL}");
        background-attachment: fixed;
        background-size: cover;
        background-position: center;
    }}
    [data-testid="stHeader"] {{ background: transparent !important; }}

    /* --- SIDEBAR DESIGN (Deep Navy & Clean) --- */
    [data-testid="stSidebar"] {{
        background-color: #0B1E33 !important; /* Elite Navy Blue */
        border-right: 1px solid rgba(255,255,255,0.1);
    }}
    
    /* Sidebar Text - Naturally White on Dark Background */
    [data-testid="stSidebar"] h1, 
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3, 
    [data-testid="stSidebar"] label, 
    [data-testid="stSidebar"] .stMarkdown,
    [data-testid="stSidebar"] p {{
        color: #ffffff !important;
        font-family: 'Montserrat', sans-serif;
        text-shadow: none !important; /* Clean text, no blur */
    }}
    
    /* Sidebar Metrics */
    [data-testid="stSidebar"] [data-testid="stMetricValue"] {{
        color: #4CAF50 !important; /* Green for money */
        font-weight: bold;
    }}

    /* --- MAIN PAGE CONTENT --- */
    /* Headers and big text on the main page (over the stadium) */
    .main h1, .main h2, .main h3, .main .stMetricLabel, .main .stMetricValue {{
        color: #ffffff !important;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.8);
    }}

    /* --- LIGHT ZONES (Tables & Forms) --- */
    /* These areas have WHITE backgrounds, so text must be DARK */

    /* 1. The Dataframe (Activity Log) */
    [data-testid="stDataFrame"] {{
        background-color: white !important;
        border-radius: 8px;
        padding: 5px;
    }}
    [data-testid="stDataFrame"] *, 
    [data-testid="stDataFrame"] th, 
    [data-testid="stDataFrame"] td {{
        color: #111111 !important; /* Dark Grey/Black */
        text-shadow: none !important;
        font-family: 'Inter', sans-serif;
    }}

    /* 2. Forms */
    [data-testid="stForm"] {{
        background-color: rgba(255, 255, 255, 0.95);
        border-radius: 15px;
        padding: 25px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.5);
    }}
    [data-testid="stForm"] label, [data-testid="stForm"] p, [data-testid="stForm"] h3 {{
        color: #111111 !important;
        text-shadow: none !important;
    }}

    /* 3. Metric Cards (Custom HTML) */
    .custom-metric-box {{
        background-color: rgba(255, 255, 255, 0.95);
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }}
    .metric-card-label {{
        color: #555555 !important;
        font-size: 13px;
        font-weight: 700;
        text-transform: uppercase;
        text-shadow: none !important;
    }}
    .metric-card-value {{
        color: #1b4332 !important;
        font-size: 26px;
        font-weight: 900;
        text-shadow: none !important;
    }}

    /* --- UI ELEMENTS --- */
    /* Inputs */
    input {{
        color: #000000 !important;
        font-weight: 600;
    }}
    
    /* Buttons */
    div[data-testid="stButton"] button {{
        background-color: #2E7D32; /* Solid Green */
        color: white;
        border: none;
        border-radius: 6px;
        font-weight: 600;
        transition: all 0.3s;
    }}
    div[data-testid="stButton"] button:hover {{
        background-color: #1B5E20;
        border-color: white;
    }}
    
    /* Expander (Admin) */
    .streamlit-expanderContent {{
        background-color: #f8f9fa;
        color: #000000 !important;
    }}
    .streamlit-expanderContent p {{
        color: #000000 !important;
    }}
    </style>
""", unsafe_allow_html=True)

# --- 3. BACKEND LOGIC ---
def get_data_from_sheets():
    try:
        gc = gspread.service_account_from_dict(st.secrets["service_account"])
        sh = gc.open_by_url(st.secrets["sheet_url"])
        worksheet = sh.get_worksheet(0)
        data = worksheet.get_all_records()
        try:
            val = worksheet.cell(1, 10).value
            initial_bankroll = float(str(val).replace(',', '')) if val else 5000.0
        except: initial_bankroll = 5000.0
        return data, worksheet, initial_bankroll
    except Exception as e:
        st.error(f"Connection Error: {e}")
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

    for row in raw_data:
        try:
            comp = str(row.get('Competition', 'Brighton')).strip()
            if not comp: comp = 'Brighton'
            
            try: odds = float(str(row.get('Odds', 1)).replace(',', '.'))
            except: odds = 1.0

            try:
                stake_val = row.get('Stake')
                if stake_val in [None, '', ' ']: exp = next_bets[comp]
                else: exp = float(str(stake_val).replace(',', ''))
            except: exp = next_bets[comp]

            res = str(row.get('Result', '')).strip()
            cycle_invest[comp] += exp
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
        except: continue
    return processed, next_bets

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

# SIDEBAR
with st.sidebar:
    try:
        st.image(APP_LOGO_URL, use_container_width=True)
    except:
        st.subheader("⚽ GoalMetric")
        
    st.markdown("---") # Divider
    st.markdown("### 🏦 WALLET CONTROL")
    st.metric("Base Bankroll", f"₪{saved_br:,.0f}")
    
    st.write("Transaction:")
    amt = st.number_input("Amount", min_value=0.0, value=100.0, step=50.0, label_visibility="collapsed")
    
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("➕ Deposit", use_container_width=True):
            if update_bankroll(worksheet, saved_br + amt): st.rerun()
    with col_btn2:
        if st.button("➖ Withdraw", use_container_width=True):
            if update_bankroll(worksheet, saved_br - amt): st.rerun()
            
    st.markdown("---")
    st.write("Select Track:")
    track = st.selectbox("Track", ["Brighton", "Africa Cup of Nations"], label_visibility="collapsed")
    if st.button("🔄 Sync Data", use_container_width=True): st.rerun()

# BANNER
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
    <div style="
        background: {banner_bg};
        border-radius: 15px;
        padding: 20px;
        display: flex;
        align-items: center;
        margin-bottom: 30px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.5);
        border: 2px solid rgba(255,255,255,0.4);
    ">
        <img src="{logo_src}" style="height: 70px; margin-right: 25px; filter: drop-shadow(0 4px 6px rgba(0,0,0,0.3));">
        <h1 style="
            margin: 0;
            font-size: 2.2rem;
            font-weight: 900;
            text-transform: uppercase;
            color: {text_color} !important;
            text-shadow: {shadow_style};
            font-family: 'Montserrat', sans-serif;
            letter-spacing: 2px;
            flex: 1;
            text-align: left;
        ">{track.upper()}</h1>
    </div>
""", unsafe_allow_html=True)

# LIVE BANKROLL
st.markdown(f"""
    <div style="text-align: center; margin-bottom: 35px;">
        <div style="
            font-size: 2.3rem; 
            font-weight: 300; 
            color: #ffffff; 
            text-shadow: 0 0 20px rgba(255,255,255,0.3); 
            line-height: 1; 
            margin-bottom: 8px;">
            ₪{current_bal:,.2f}
        </div>
        <div style="
            font-size: 0.8rem; 
            font-weight: 600; 
            color: #cccccc; 
            letter-spacing: 3px; 
            text-transform: uppercase;">
            LIVE BANKROLL
        </div>
    </div>
""", unsafe_allow_html=True)

# METRICS
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
    st.markdown(f"""<div class="custom-