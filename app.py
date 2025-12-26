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
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;700;900&family=Inter:wght@400;700&display=swap');
    
    /* 1. Main Background with Dark Overlay */
    [data-testid="stAppViewContainer"] {{
        background-image: linear-gradient(rgba(0, 0, 0, 0.5), rgba(0, 0, 0, 0.5)), url("{bg_img_url}");
        background-attachment: fixed;
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
    }}
    
    /* 2. Header Transparency */
    [data-testid="stHeader"] {{ 
        background: rgba(0,0,0,0) !important; 
    }}

    /* 3. Global Text Visibility - White with Black Shadow */
    h1, h2, h3, h4, h5, h6, p, label, 
    .stMarkdown, 
    div[data-testid="stMetricLabel"],
    div[data-testid="stMetricValue"],
    .stSubheader,
    .stText {{
        color: #ffffff !important;
        text-shadow: 3px 3px 6px #000000, 1px 1px 2px #000000 !important;
        font-family: 'Montserrat', sans-serif;
        font-weight: 700 !important;
    }}
    
    /* Exception: Text inside white forms and metric cards - BLACK */
    div[data-testid="stForm"],
    div[data-testid="stForm"] *,
    div[data-testid="stForm"] label,
    div[data-testid="stForm"] p,
    div[data-testid="stForm"] input,
    div[data-testid="stForm"] .stTextInput,
    div[data-testid="stForm"] .stTextInput *,
    div[data-testid="stForm"] .stTextInput label,
    div[data-testid="stForm"] .stNumberInput,
    div[data-testid="stForm"] .stNumberInput *,
    div[data-testid="stForm"] .stNumberInput label,
    div[data-testid="stForm"] .stRadio,
    div[data-testid="stForm"] .stRadio *,
    div[data-testid="stForm"] .stRadio label,
    div[data-testid="stForm"] h3,
    div[data-testid="stForm"] h4,
    div[data-testid="stForm"] h5,
    div[data-testid="stForm"] h6,
    .custom-metric-box,
    .custom-metric-box *,
    .custom-metric-box div,
    .metric-card-label,
    .metric-card-value,
    div[data-testid="stDataFrame"],
    div[data-testid="stDataFrame"] *,
    div[data-testid="stDataFrame"] table,
    div[data-testid="stDataFrame"] th,
    div[data-testid="stDataFrame"] td {{
        color: #111111 !important;
        text-shadow: none !important;
    }}

    /* 4. Sidebar Styling */
    [data-testid="stSidebar"] {{
        background-color: rgba(0, 0, 0, 0.75) !important;
        backdrop-filter: blur(10px);
        border-right: 1px solid rgba(255,255,255,0.2);
    }}
    
    [data-testid="stSidebar"] * {{
        color: #ffffff !important;
        text-shadow: 2px 2px 4px #000000 !important;
    }}
    
    [data-testid="stSidebar"] label {{
        color: #ffffff !important;
        text-shadow: 2px 2px 4px #000000 !important;
    }}

    /* 5. Custom Metric Cards (White Box) */
    .custom-metric-box {{
        background-color: rgba(255, 255, 255, 0.95);
        border-radius: 15px;
        padding: 25px;
        text-align: center;
        box-shadow: 0 6px 20px rgba(0,0,0,0.6);
        margin-bottom: 20px;
        border: 2px solid rgba(255,255,255,0.3);
    }}
    .metric-card-label {{
        font-size: 14px;
        font-weight: bold;
        text-transform: uppercase;
        color: #555 !important;
        letter-spacing: 1px;
        margin-bottom: 10px;
    }}
    .metric-card-value {{
        font-size: 28px;
        font-weight: 900;
        color: #1b4332 !important;
        line-height: 1.2;
    }}

    /* 6. Form Styling - White Background */
    div[data-testid="stForm"] {{
        background-color: rgba(255, 255, 255, 0.95) !important;
        border-radius: 20px;
        padding: 30px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.6);
        border: 2px solid rgba(255,255,255,0.3);
    }}
    
    /* 7. Streamlit Metric Component Override */
    div[data-testid="stMetric"] {{
        background-color: rgba(255, 255, 255, 0.1);
        padding: 15px;
        border-radius: 10px;
        border: 1px solid rgba(255,255,255,0.2);
    }}
    
    /* 8. Button Styling - FIXED FOR SIDEBAR */
    div[data-testid="stButton"] > button {{
        background-color: rgba(45, 106, 79, 0.9);
        color: white;
        font-weight: 600 !important; /* Slightly lighter bold */
        font-size: 13px !important; /* Smaller text */
        border: none;
        border-radius: 8px;
        padding: 8px 5px !important; /* Minimal side padding */
        width: 100%; /* Force full width */
        white-space: nowrap; /* Prevent text wrapping */
        transition: all 0.3s;
    }}
    
    div[data-testid="stButton"] > button:hover {{
        background-color: rgba(27, 67, 50, 1);
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.3);
    }}
    
    /* 9. Input Fields in Forms */
    div[data-testid="stForm"] input,
    div[data-testid="stForm"] .stTextInput > div > div > input {{
        background-color: #ffffff;
        color: #000000;
        border: 2px solid #ddd;
    }}
    
    /* 10. Table Styling - White Background with Black Text */
    .stDataFrame,
    div[data-testid="stDataFrame"],
    div[data-testid="stDataFrame"] *,
    div[data-testid="stDataFrame"] table,
    div[data-testid="stDataFrame"] thead,
    div[data-testid="stDataFrame"] tbody,
    div[data-testid="stDataFrame"] tr,
    div[data-testid="stDataFrame"] th,
    div[data-testid="stDataFrame"] td {{
        background-color: rgba(255, 255, 255, 0.95) !important;
        border-radius: 10px;
        padding: 10px;
        color: #111111 !important;
        text-shadow: none !important;
    }}
    
    /* 11. Additional White Container Text Fix */
    div[style*="background-color: rgba(255, 255, 255"],
    div[style*="background-color: white"],
    div[style*="background: rgba(255, 255, 255"],
    div[style*="background: white"] {{
        color: #111111 !important;
    }}
    
    div[style*="background-color: rgba(255, 255, 255"] *,
    div[style*="background-color: white"] *,
    div[style*="background: rgba(255, 255, 255"] *,
    div[style*="background: white"] * {{
        color: #111111 !important;
        text-shadow: none !important;
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