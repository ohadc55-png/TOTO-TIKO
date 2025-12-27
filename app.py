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

# --- 2. THE "ULTIMATE" CSS (FORCE STYLING V3) ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;700;900&display=swap');
    
    /* Global Reset & Cleanup */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    [data-testid="stDecoration"] {{display: none;}}
    header[data-testid="stHeader"] {{ background: transparent !important; }}
    
    /* 1. ARROW FIX V3 - AGGRESSIVE TEXT HIDING */
    /* Outer Arrow (Open Sidebar) */
    [data-testid="stSidebarCollapsedControl"] {{
        background-color: rgba(0, 0, 0, 0.5) !important;
        border-radius: 12px !important;
        width: 45px !important; height: 45px !important;
        display: flex !important; align-items: center !important; justify-content: center !important;
        margin: 15px !important;
        /* Ensure container text is transparent, only show SVG icon color */
        color: transparent !important; 
    }}
    [data-testid="stSidebarCollapsedControl"] svg {{ 
        fill: white !important; 
        width: 25px !important; height: 25px !important; 
    }}
    
    /* Inner Arrow (Close Sidebar) */
    section[data-testid="stSidebar"] button[kind="header"] {{
        color: transparent !important; /* Hide text like "Collapse" */
    }}
    section[data-testid="stSidebar"] button[kind="header"] svg {{
        fill: #000000 !important; /* Force icon black */
        width: 25px !important; height: 25px !important;
    }}

    /* Kill tooltips globally */
    .stTooltipIcon, [data-testid="stTooltipContent"] {{ display: none !important; }}


    /* 2. MAIN AREA TEXT - FORCE WHITE & SHADOW */
    [data-testid="stAppViewContainer"] h1, 
    [data-testid="stAppViewContainer"] h2, 
    [data-testid="stAppViewContainer"] h3, 
    [data-testid="stAppViewContainer"] p, 
    [data-testid="stAppViewContainer"] span,
    [data-testid="stAppViewContainer"] label,
    .stMarkdown p {{
        color: #ffffff !important;
        text-shadow: 2px 2px 8px rgba(0,0,0,1) !important;
        font-family: 'Montserrat', sans-serif !important;
    }}
    [data-testid="stMetricValue"] {{ color: white !important; text-shadow: 2px 2px 4px black !important; }}
    [data-testid="stMetricLabel"] {{ color: #eeeeee !important; }}

    /* 3. BACKGROUND ARCHITECTURE */
    [data-testid="stAppViewContainer"] {{
        background-image: linear-gradient(rgba(0, 0, 0, 0.65), rgba(0, 0, 0, 0.65)), url("{BG_IMAGE}");
        background-attachment: fixed; background-size: cover; background-position: center;
    }}
    [data-testid="stSidebar"] {{
        background-color: rgba(255, 255, 255, 0.85) !important;
        border-right: 1px solid rgba(255,255,255,0.2);
    }}
    [data-testid="stSidebar"]::before {{
        content: ""; position: absolute; top: 0; left: 0; width: 100%; height: 100%;
        background-image: url("{SIDEBAR_BG}"); background-size: cover;
        filter: blur(4px); z-index: -1;
    }}

    /* 4. SIDEBAR CONTENT (BLACK) */
    [data-testid="stSidebar"] *, [data-testid="stSidebar"] p, [data-testid="stSidebar"] label {{
        color: #000000 !important;
        text-shadow: none !important;
    }}

    /* 5. ACTIVITY LOG BANNER CARDS (V2 - Enhanced Data) */
    .activity-banner {{
        padding: 15px 20px;
        border-radius: 15px;
        margin-bottom: 12px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 8px 20px rgba(0,0,0,0.4);
        border-left: 8px solid;
    }}
    .banner-win {{
        background: linear-gradient(90deg, rgba(20, 50, 40, 0.95), rgba(40, 90, 70, 0.95));
        border-color: #00ff88;
    }}
    .banner-loss {{
        background: linear-gradient(90deg, rgba(80, 10, 10, 0.95), rgba(130, 20, 20, 0.95));
        border-color: #ff4b4b;
    }}
    .banner-details-right {{
        text-align: right;
        line-height: 1.2;
    }}

    /* 6. FORM & CARDS */
    [data-testid="stForm"] {{ 
        background-color: rgba(255, 255, 255, 0.1) !important; 
        border-radius: 20px; border: 1px solid rgba(255,255,255,0.25);
    }}
    .metric-card-box {{
        background-color: rgba(255, 255, 255, 0.95);
        border-radius: 15px; padding: 20px; text-align: center;
        box-shadow: 0 10px 25px rgba(0,0,0,0.5);
    }}
    .card-lbl {{ color: #444 !important; font-weight: 700; font-size: 13px; text-shadow: none !important; }}
    .card-val {{ color: #1b4332 !important; font-weight: 900; font-size: 26px; text-shadow: none !important; }}

    </style>
""", unsafe_allow_html=True)

# --- 3. DATA BACKEND ---
def connect_to_cloud():
    try:
        gc = gspread.service_account_from_dict(st.secrets["service_account"])
        sh = gc.open_by_url(st.secrets["sheet_url"])
        ws = sh.get_worksheet(0)
        raw = ws.get_all_records()
        try:
            br_val = ws.cell(1, 10).value
            base_br = float(str(br_val).replace(',', '')) if br_val else 5000.0
        except: base_br = 5000.0
        return raw, ws, base_br
    except Exception as e:
        st.error(f"Sync Lost: {e}")
        return [], None, 5000.0

def process_engine(data):
    if not data: return pd.DataFrame()
    rows = []
    for r in data:
        try:
            c = str(r.get('Competition', 'Brighton')).strip() or 'Brighton'
            o = float(str(r.get('Odds', 1)).replace(',', '.'))
            s = float(str(r.get('Stake', 0)).replace(',', '')) if r.get('Stake') else 0.0
            res = str(r.get('Result', '')).strip()
            win = "Draw (X)" in res
            inc = s * o if win else 0.0
            rows.append({
                "Date": r.get('Date', ''), "Comp": c,
                "Match": f"{r.get('Home Team','')} vs {r.get('Away Team','')}",
                "Odds": o, "Out": s, "In": inc,
                "Status": "✅ Won" if win else "❌ Lost"
            })
        except: continue
    return pd.DataFrame(rows)

# --- 4. EXECUTION ---
raw_data, worksheet, initial_br = connect_to_cloud()
df = process_engine(raw_data)
live_br = initial_br + (df['In'].sum() - df['Out'].sum()) if not df.empty else initial_br

# --- 5. SIDEBAR ---
with st.sidebar:
    st.image(APP_LOGO, width=120)
    st.markdown("### WALLET CONTROL")
    st.metric("Base Bankroll", f"₪{initial_br:,.0f}")
    amt = st.number_input("Amount", min_value=0.0, value=100.0, step=50.0)
    c1, c2 = st.columns(2)
    if c1.button("Deposit", use_container_width=True):
        worksheet.update_cell(1, 10, initial_br + amt); st.rerun()
    if c2.button("Withdraw", use_container_width=True):
        worksheet.update_cell(1, 10, initial_br - amt); st.rerun()
    st.divider()
    view = st.selectbox("View", ["🏆 Overview", "Brighton", "Africa Cup of Nations"])
    if st.button("🔄 Sync Systems", use_container_width=True): st.rerun()

# --- 6. DISPLAY ---
if view == "🏆 Overview":
    st.markdown("<h1 style='text-align: center; font-size: 3.5rem;'>CENTRAL COMMAND</h1>", unsafe_allow_html=True)
    st.markdown(f"<h2 style='text-align: center; font-size: 3rem;'>₪{live_br:,.2f}</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>GLOBAL POSITION</p>", unsafe_allow_html=True)