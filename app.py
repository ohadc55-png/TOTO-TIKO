import streamlit as st
import pandas as pd
import plotly.express as px
import gspread
import datetime

# --- 1. CONFIGURATION ---
APP_LOGO = "https://i.postimg.cc/8Cr6SypK/yzwb-ll-sm.png"
BG_IMAGE = "https://i.postimg.cc/GmFZ4KS7/Gemini-Generated-Image-k1h11zk1h11zk1h1.png"
SIDEBAR_BG = "https://i.postimg.cc/NfdK3hck/'yzwb-ll'-sm-(1).png"

st.set_page_config(
    page_title="GoalMetric Elite Dashboard",
    layout="wide",
    page_icon=APP_LOGO,
    initial_sidebar_state="expanded"
)

# --- 2. ADVANCED CSS (FOCUSED ON MOBILE & CLEAN BANNERS) ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;700;900&display=swap');
    
    /* 1. Global Style Reset */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    [data-testid="stDecoration"] {{display: none;}}
    header[data-testid="stHeader"] {{ background: transparent !important; }}
    
    /* 2. Arrows & Tooltips Fix */
    [data-testid="stSidebarCollapsedControl"] {{
        background-color: rgba(0, 0, 0, 0.6) !important;
        border-radius: 50% !important;
        width: 45px !important; height: 45px !important;
        display: flex !important; align-items: center !important; justify-content: center !important;
        margin: 10px !important;
    }}
    [data-testid="stSidebarCollapsedControl"] svg {{ fill: white !important; }}
    [data-testid="stTooltipContent"], .stTooltipIcon {{ display: none !important; }}
    
    /* 3. Global Backgrounds */
    [data-testid="stAppViewContainer"] {{
        background-image: linear-gradient(rgba(0, 0, 0, 0.7), rgba(0, 0, 0, 0.7)), url("{BG_IMAGE}");
        background-attachment: fixed; background-size: cover; background-position: center;
    }}
    [data-testid="stSidebar"] {{
        background-color: rgba(255, 255, 255, 0.85) !important;
    }}
    [data-testid="stSidebar"]::before {{
        content: ""; position: absolute; top: 0; left: 0; width: 100%; height: 100%;
        background-image: url("{SIDEBAR_BG}"); background-size: cover;
        filter: blur(4px); z-index: -1;
    }}

    /* 4. Typography (Main area forced white) */
    .main h1, .main h2, .main h3, .main p, .main span, .main label {{
        color: #ffffff !important;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.8);
        font-family: 'Montserrat', sans-serif;
    }}
    [data-testid="stSidebar"] * {{ color: #000000 !important; text-shadow: none !important; }}

    /* 5. Metrics & Forms */
    .custom-metric-card {{
        background-color: rgba(255, 255, 255, 0.95);
        border-radius: 15px; padding: 20px; text-align: center;
        box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    }}
    .c-label {{ color: #555 !important; font-weight: 700; font-size: 12px; text-transform: uppercase; }}
    .c-value {{ color: #1b4332 !important; font-weight: 900; font-size: 26px; }}

    [data-testid="stForm"] {{ background-color: rgba(255, 255, 255, 0.95); border-radius: 15px; padding: 20px; }}
    [data-testid="stForm"] * {{ color: black !important; }}

    /* 6. Activity Log Banners (50% Opacity) */
    .log-banner {{
        padding: 15px 25px;
        border-radius: 12px;
        margin-bottom: 12px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.4);
        border-left: 8px solid;
    }}
    .banner-win {{
        background-color: rgba(46, 204, 113, 0.5) !important;
        border-color: #27ae60;
    }}
    .banner-loss {{
        background-color: rgba(231, 76, 60, 0.5) !important;
        border-color: #c0392b;
    }}
    .banner-text-main {{ font-size: 1.1rem; font-weight: 800; color: white !important; }}
    .banner-text-sub {{ font-size: 0.85rem; opacity: 0.9; color: white !important; }}
    .banner-profit {{ font-size: 1.4rem; font-weight: 900; color: white !important; }}

    /* --- 7. MOBILE OPTIMIZATION ENGINE --- */
    @media only screen and (max-width: 768px) {{
        /* Headers scaling */
        h1 {{ font-size: 1.5rem !important; }}
        h2 {{ font-size: 1.8rem !important; }}
        
        /* Competition Banner - Center image, ensure title is gone if any remains */
        .banner-container {{
            justify-content: center !important;
            padding: 15px !important;
            margin-bottom: 25px !important;
        }}
        .banner-container img {{
            height: 70px !important;
            margin-right: 0 !important;
        }}
        
        /* Metric cards stacked for mobile */
        [data-testid="column"] {{
            width: 100% !important;
            flex: 1 1 100% !important;
            margin-bottom: 10px !important;
        }}
        
        /* Activity banners reformatted to columns */
        .log-banner {{
            flex-direction: column !important;
            text-align: center !important;
            gap: 10px;
        }}
        .log-banner > div {{
            width: 100% !important;
        }}
    }}
    </style>
""", unsafe_allow_html=True)

# --- 3. DATA ENGINE ---

def get_connection():
    try:
        gc = gspread.service_account_from_dict(st.secrets["service_account"])
        sh = gc.open_by_url(st.secrets["sheet_url"])
        ws = sh.get_worksheet(0)
        data = ws.get_all_records()
        try:
            br_cell = ws.cell(1, 10).value
            base_br = float(str(br_cell).replace(',', '')) if br_cell else 5000.0
        except: base_br = 5000.0
        return data, ws, base_br
    except Exception as e:
        st.error(f"Sync Error: {e}")
        return [], None, 5000.0

def process_data(raw_data):
    if not raw_data: return pd.DataFrame()
    processed = []
    cycle_trackers = {}
    
    for row in raw_data:
        try:
            comp = str(row.get('Competition', 'Brighton')).strip() or 'Brighton'
            if comp not in cycle_trackers:
                cycle_trackers[comp] = 0.0
                
            odds = float(str(row.get('Odds', 1)).replace(',', '.'))
            stake = float(str(row.get('Stake', 0)).replace(',', '')) if row.get('Stake') else 0.0
            res = str(row.get('Result', '')).strip()
            
            is_win = "Draw (X)" in res
            income = stake * odds if is_win else 0.0
            cycle_trackers[comp] += stake
            
            if is_win:
                cycle_profit = income - cycle_trackers[comp]
                cycle_trackers[comp] = 0.0
            else:
                cycle_profit = -stake
            
            processed.append({
                "Date": row.get('Date', ''),
                "Comp": comp,
                "Match": f"{row.get('Home Team','')} vs {row.get('Away Team','')}",
                "Odds": odds,
                "Expense": stake,
                "Income": income,
                "Cycle_Profit": cycle_profit,
                "Status": "✅ Won