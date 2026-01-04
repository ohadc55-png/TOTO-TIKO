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
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    [data-testid="stSidebarNav"] {display: none;}
    
    [data-testid="collapsedControl"], [data-testid="stSidebarCollapsedControl"], button[kind="header"] {
        display: block !important;
        visibility: visible !important;
    }

    [data-testid="stAppViewContainer"] {
        background-image: linear-gradient(rgba(0, 0, 0, 0.7), rgba(0, 0, 0, 0.7)), url("{BG_IMAGE_URL}");
        background-attachment: fixed;
        background-size: cover;
        background-position: center;
    }

    [data-testid="stSidebar"] {
        background-color: #f8f9fa !important;
        border-right: 1px solid #ddd;
    }
    [data-testid="stSidebar"] * {
        color: #000000 !important;
        text-shadow: none !important;
        font-family: 'Montserrat', sans-serif;
    }
    [data-testid="stSidebar"] input {
        color: #000000 !important;
        background-color: #ffffff !important;
        border: 1px solid #ccc;
    }
    [data-testid="stSidebar"] button {
        color: #ffffff !important;
    }

    .main h1, .main h2, .main h3, .main h4, .main p {
        color: #ffffff !important;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.8);
    }

    [data-testid="stDataFrame"] { background-color: white !important; border-radius: 8px; }
    [data-testid="stDataFrame"] * { color: #000000 !important; text-shadow: none !important; }
    [data-testid="stForm"] { background-color: rgba(255, 255, 255, 0.95); border-radius: 15px; padding: 25px; }
    [data-testid="stForm"] * { color: #000000 !important; text-shadow: none !important; }

    .custom-metric-box {
        background-color: rgba(255, 255, 255, 0.95);
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }
    .metric-card-label { color: #555 !important; font-weight: 700; font-size: 13px; text-shadow: none !important; }
    .metric-card-value { color: #1b4332 !important; font-weight: 900; font-size: 26px; text-shadow: none !important; }

    /* Competition Banners - Proportional Size */
    .comp-banner-box {
        border-radius: 15px;
        padding: 15px 25px; /* Reduced padding for better proportion */
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        margin-bottom: 25px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.5);
        border: 2px solid rgba(255,255,255,0.4);
        width: 100%;
    }
    .comp-banner-logo {
        height: 55px !important; /* Scaled logo */
        margin-right: 20px;
        filter: drop-shadow(0 4px 6px rgba(0,0,0,0.3));
    }
    .comp-banner-text {
        margin: 0 !important;
        font-size: 1.8rem !important; /* Scaled text */
        font-weight: 900 !important;
        text-transform: uppercase !important;
        letter-spacing: 2px !important;
        font-family: 'Montserrat', sans-serif !important;
    }

    /* Activity Cards */
    .activity-card {border-radius: 15px !important; padding: 25px !important; margin-bottom: 20px !important; box-shadow: 0 8px 25px rgba(0,0,0,0.4) !important; transition: all 0.3s ease !important; position: relative !important; overflow: hidden !important;}
    .activity-card::before {content: '' !important; position: absolute !important; top: 0 !important; left: 0 !important; right: 0 !important; height: 4px !important; transition: height 0.3s ease !important;}
    .activity-card:hover {transform: translateY(-5px) !important; box-shadow: 0 12px 35px rgba(0,0,0,0.5) !important;}
    .activity-card:hover::before {height: 6px !important;}
    .activity-card-won {background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 50%, #b1dfbb 100%) !important; border-left: 6px solid #28a745 !important;}
    .activity-card-won::before {background: linear-gradient(90deg, #28a745 0%, #20c997 100%) !important;}
    .activity-card-lost {background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 50%, #f1b0b7 100%) !important; border-left: 6px solid #dc3545 !important;}
    .activity-card-lost::before {background: linear-gradient(90deg, #dc3545 0%, #c82333 100%) !important;}
    .activity-card-pending {background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 50%, #fdcb6e 100%) !important; border-left: 6px solid #ffc107 !important;}
    .activity-card-pending::before {background: linear-gradient(90deg, #ffc107 0%, #ffb300 100%) !important;}
    .activity-header {display: flex !important; justify-content: space-between !important; align-items: center !important; margin-bottom: 15px !important; padding-bottom: 12px !important; border-bottom: 2px solid rgba(0,0,0,0.1) !important;}
    .activity-match {font-size: 1.2rem !important; font-weight: 900 !important; color: #1a1a1a !important; text-shadow: none !important; letter-spacing: 0.5px !important;}
    .activity-date {font-size: 0.9rem !important; color: #555 !important; text-shadow: none !important; font-weight: 600 !important; margin-top: 3px !important;}
    .activity-stats {display: flex !important; flex-wrap: wrap !important; gap: 20px !important; margin-top: 15px !important;}
    .activity-stat-item {flex: 1 !important; min-width: 90px !important; background: rgba(255, 255, 255, 0.7) !important; padding: 10px !important; border-radius: 8px !important; text-align: center !important; transition: all 0.2s ease !important;}
    .activity-stat-item:hover {background: rgba(255, 255, 255, 0.9) !important; transform: scale(1.05) !important;}
    .activity-stat-label {font-size: 0.7rem !important; color: #666 !important; text-transform: uppercase !important; letter-spacing: 1px !important; text-shadow: none !important; font-weight: 700 !important; margin-bottom: 5px !important;}
    .activity-stat-value {font-size: 1.1rem !important; font-weight: 900 !important; color: #1a1a1a !important; text-shadow: none !important;}
    .activity-status {display: inline-block !important; padding: 8px 16px !important; border-radius: 25px !important; font-size: 0.9rem !important; font-weight: 900 !important; text-shadow: none !important; box-shadow: 0 2px 8px rgba(0,0,0,0.2) !important; transition: all 0.2s ease !important;}
    .activity-status:hover {transform: scale(1.05) !important; box-shadow: 0 4px 12px rgba(0,0,0,0.3) !important;}
    .status-won {background: linear-gradient(135deg, #28a745 0%, #20c997 100%) !important; color: #ffffff !important;}
    .status-lost {background: linear-gradient(135deg, #dc3545 0%, #c82333 100%) !important; color: #ffffff !important;}
    .status-pending {background: linear-gradient(135deg, #ffc107 0%, #ff9800 100%) !important; color: #ffffff !important;}

    /* Mobile Optimization: Hide text, show only logo in banners */
    @media only screen and (max-width: 768px) {
        .comp-banner-text { display: none !important; }
        .comp-banner-logo { margin-right: 0 !important; height: 50px !important; }
        .comp-banner-box { padding: 15px !important; }
        
        [data-testid="stDataFrame"] * {font-size: 12px !important;}
    }
    
    /* Loading Spinner */
    [data-testid="stStatusWidget"] {position: fixed !important; top: 50% !important; left: 50% !important; transform: translate(-50%, -50%) !important; z-index: 9999 !important; background: rgba(0, 0, 0, 0.9) !important; width: 100vw !important; height: 100vh !important; display: flex !important; align-items: center !important; justify-content: center !important;}
    [data-testid="stStatusWidget"]::before {content: '' !important; width: 80px !important; height: 80px !important; border: 8px solid rgba(255, 255, 255, 0.2) !important; border-top: 8px solid #4CAF50 !important; border-radius: 50% !important; animation: spin 1s linear infinite !important; position: absolute !important;}
    [data-testid="stStatusWidget"]::after {content: 'DRAW IT' !important; color: #ffffff !important; font-size: 1.5rem !important; font-weight: 900 !important; font-family: 'Montserrat', sans-serif !important; letter-spacing: 3px !important; position: absolute !important; margin-top: 120px !important; text-shadow: 0 0 20px rgba(76, 175, 80, 0.8) !important;}
    @keyframes spin {0% {transform: rotate(0deg);} 100% {transform: rotate(360deg);}}
    </style>
""", unsafe_allow_html=True)

# --- BACKEND FUNCTIONS ---
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
            val = matches_sheet.cell(