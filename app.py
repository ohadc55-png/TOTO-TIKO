import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import datetime
import plotly.express as px

# --- 1. CONFIGURATION ---
APP_LOGO_URL = "https://i.postimg.cc/8Cr6SypK/yzwb-ll-sm.png"
BG_IMAGE_URL = "https://i.postimg.cc/GmFZ4KS7/Gemini-Generated-Image-k1h11zk1h11zk1h1.png"

# Competition Logos
BRIGHTON_LOGO = "https://i.postimg.cc/x8kdQh5H/Brighton_Hove_Albion_logo.png"
AFCON_LOGO = "https://i.postimg.cc/5yHtJTgz/2025_Africa_Cup_of_Nations_logo.png"

# Constants
DEFAULT_STAKE = 30.0
DEFAULT_BANKROLL = 5000.0
BANKROLL_CELL_ROW = 1
BANKROLL_CELL_COL = 10
RESULT_COL = 6

# Competition styling
COMPETITION_STYLES = {
    "Brighton": {
        "gradient": "linear-gradient(135deg, #0057B8 0%, #4CABFF 50%, #E6F7FF 100%)",
        "text_color": "#004085",
        "logo": BRIGHTON_LOGO
    },
    "Africa Cup of Nations": {
        "gradient": "linear-gradient(135deg, #009639 0%, #FFCD00 50%, #EF3340 100%)",
        "text_color": "#1a1a1a",
        "logo": AFCON_LOGO
    }
}

st.set_page_config(page_title="Elite Football Tracker", layout="wide", page_icon=APP_LOGO_URL)

# --- 2. CSS STYLING ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;600;900&display=swap');
    
    * {{
        font-family: 'Montserrat', sans-serif;
    }}
    
    [data-testid="stAppViewContainer"] {{
        background-image: linear-gradient(rgba(0,0,0,0.75), rgba(0,0,0,0.75)), url("{BG_IMAGE_URL}");
        background-attachment: fixed; 
        background-size: cover;
    }}
    
    /* Make text white on the main background (stadium image) */
    [data-testid="stAppViewContainer"] > div > div > div > div > section[data-testid="stMain"] h1,
    [data-testid="stAppViewContainer"] > div > div > div > div > section[data-testid="stMain"] h2,
    [data-testid="stAppViewContainer"] > div > div > div > div > section[data-testid="stMain"] h3,
    [data-testid="stAppViewContainer"] > div > div > div > div > section[data-testid="stMain"] h4,
    [data-testid="stAppViewContainer"] > div > div > div > div > section[data-testid="stMain"] p,
    [data-testid="stAppViewContainer"] > div > div > div > div > section[data-testid="stMain"] span,
    [data-testid="stAppViewContainer"] > div > div > div > div > section[data-testid="stMain"] label {{
        color: white !important;
    }}
    
    /* Sidebar - Dark text on light background */
    [data-testid="stSidebar"] {{
        background: linear-gradient(180deg, #f8f9fa 0%, #e9ecef 100%) !important;
    }}
    
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] h4,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] .stMarkdown {{
        color: #2d3748 !important;
    }}
    
    [data-testid="stSidebar"] [data-testid="stMetricValue"] {{
        color: #1a365d !important;
    }}
    
    [data-testid="stSidebar"] [data-testid="stMetricLabel"] {{
        color: #4a5568 !important;
    }}
    
    /* Form elements - Labels should be WHITE (they're on dark background, outside the card) */
    [data-testid="stForm"] label {{
        color: white !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        text-shadow: 1px 1px 3px rgba(0,0,0,0.5) !important;
    }}
    
    [data-testid="stForm"] input {{
        color: #2d3748 !important;
    }}
    
    /* Radio buttons in form - WHITE text */
    [data-testid="stForm"] [data-testid="stMarkdownContainer"] {{
        color: white !important;
        text-shadow: 1px 1px 3px rgba(0,0,0,0.5) !important;
    }}
    
    [data-testid="stForm"] [data-baseweb="radio"] {{
        color: white !important;
    }}
    
    [data-testid="stForm"] [data-baseweb="radio"] div {{
        color: white !important;
        text-shadow: 1px 1px 3px rgba(0,0,0,0.5) !important;
    }}
    
    /* Radio button labels specifically */
    [data-testid="stForm"] .stRadio label {{
        color: white !important;
        text-shadow: 1px 1px 3px rgba(0,0,0,0.5) !important;
    }}
    
    [data-testid="stForm"] .stRadio p {{
        color: white !important;
        text-shadow: 1px 1px 3px rgba(0,0,0,0.5) !important;
    }}
    
    /* Form Card Styling - Soft and Inviting */
    .form-card {{
        background: linear-gradient(145deg, rgba(255, 255, 255, 0.95), rgba(245, 247, 250, 0.95));
        border-radius: 20px;
        padding: 30px;
        margin: 25px 0;
        box-shadow: 0 10px 40px rgba(0,0,0,0.15);
        border: 1px solid rgba(255,255,255,0.8);
    }}
    
    .form-card-title {{
        color: #2d3748 !important;
        font-size: 1.3rem;
        font-weight: 600;
        margin-bottom: 20px;
        display: flex;
        align-items: center;
        gap: 10px;
    }}
    
    /* Style form inputs */
    .form-card .stTextInput > div > div > input,
    .form-card .stNumberInput > div > div > input {{
        background: white !important;
        border: 2px solid #e2e8f0 !important;
        border-radius: 12px !important;
        padding: 12px 16px !important;
        color: #2d3748 !important;
        font-size: 1rem !important;
        transition: all 0.3s ease !important;
    }}
    
    .form-card .stTextInput > div > div > input:focus,
    .form-card .stNumberInput > div > div > input:focus {{
        border-color: #4CABFF !important;
        box-shadow: 0 0 0 3px rgba(76, 171, 255, 0.2) !important;
    }}
    
    .form-card label {{
        color: #4a5568 !important;
        font-weight: 500 !important;
        font-size: 0.9rem !important;
    }}
    
    /* Match Activity Cards */
    .match-card {{
        border-radius: 16px;
        padding: 20px 24px;
        margin-bottom: 14px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 6px 20px rgba(0,0,0,0.25);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }}
    
    .match-card:hover {{
        transform: translateY(-3px);
        box-shadow: 0 10px 30px rgba(0,0,0,0.35);
    }}
    
    .match-card-won {{
        background: linear-gradient(135deg, rgba(40, 167, 69, 0.6) 0%, rgba(40, 167, 69, 0.35) 100%);
        border: 2px solid rgba(40, 167, 69, 0.7);
    }}
    
    .match-card-lost {{
        background: linear-gradient(135deg, rgba(220, 53, 69, 0.6) 0%, rgba(220, 53, 69, 0.35) 100%);
        border: 2px solid rgba(220, 53, 69, 0.7);
    }}
    
    .match-card-pending {{
        background: linear-gradient(135deg, rgba(255, 193, 7, 0.6) 0%, rgba(255, 193, 7, 0.35) 100%);
        border: 2px solid rgba(255, 193, 7, 0.7);
    }}
    
    .match-card .match-info {{
        flex: 1;
    }}
    
    .match-card .match-name {{
        font-size: 1.15rem;
        font-weight: 600;
        color: white !important;
        margin-bottom: 6px;
        text-shadow: 1px 1px 3px rgba(0,0,0,0.4);
    }}
    
    .match-card .match-details {{
        font-size: 0.85rem;
        color: rgba(255,255,255,0.95) !important;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
    }}
    
    .match-card .match-profit {{
        font-size: 1.4rem;
        font-weight: 700;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.4);
    }}
    
    .match-profit-positive {{
        color: #90EE90 !important;
    }}
    
    .match-profit-negative {{
        color: #FFB6C1 !important;
    }}
    
    .match-profit-neutral {{
        color: #FFE066 !important;
    }}
    
    /* Competition Banner */
    .comp-banner-box {{
        border-radius: 20px;
        padding: 30px 40px;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-bottom: 30px;
        box-shadow: 0 15px 40px rgba(0,0,0,0.4);
        border: 3px solid rgba(255,255,255,0.3);
        backdrop-filter: blur(10px);
    }}
    
    .comp-banner-box img {{
        height: 100px;
        margin-right: 30px;
        filter: drop-shadow(3px 3px 8px rgba(0,0,0,0.5));
    }}
    
    .comp-banner-box h1 {{
        margin: 0;
        font-weight: 900;
        font-size: 2.2rem;
        letter-spacing: 2px;
    }}
    
    /* Banner text - hidden on mobile */
    .comp-banner-text {{
        margin: 0;
        font-weight: 900;
        font-size: 2.2rem;
        letter-spacing: 2px;
    }}
    
    /* Mobile Responsive - Competition Banner */
    @media (max-width: 768px) {{
        .comp-banner-box {{
            padding: 20px;
        }}
        
        .comp-banner-box img {{
            height: 80px;
            margin-right: 0;
        }}
        
        .comp-banner-box h1,
        .comp-banner-box .comp-banner-text {{
            display: none !important;
        }}
        
        .overview-comp-header h3 {{
            font-size: 1.1rem;
        }}
        
        .overview-comp-header img {{
            height: 50px;
            margin-right: 12px;
        }}
        
        .overview-comp-profit {{
            font-size: 1.4rem;
        }}
        
        .overview-stats-row {{
            flex-wrap: wrap;
        }}
        
        .overview-stat-item {{
            flex: 1 1 33%;
            padding: 8px 5px;
        }}
        
        .stat-box {{
            min-width: 100px;
            padding: 15px 10px;
        }}
        
        .stat-box .stat-value {{
            font-size: 1.2rem;
        }}
        
        .match-card {{
            flex-direction: column;
            align-items: flex-start;
            gap: 10px;
        }}
        
        .match-card .match-profit {{
            align-self: flex-end;
        }}
    }}
    
    /* Stats Boxes */
    .stats-container {{
        display: flex;
        gap: 15px;
        margin: 25px 0;
        flex-wrap: wrap;
    }}
    
    .stat-box {{
        flex: 1;
        min-width: 150px;
        border-radius: 15px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 8px 25px rgba(0,0,0,0.3);
        backdrop-filter: blur(10px);
    }}
    
    .stat-box-total {{
        background: linear-gradient(135deg, rgba(52, 152, 219, 0.8) 0%, rgba(41, 128, 185, 0.6) 100%);
        border: 2px solid rgba(52, 152, 219, 0.5);
    }}
    
    .stat-box-income {{
        background: linear-gradient(135deg, rgba(46, 204, 113, 0.8) 0%, rgba(39, 174, 96, 0.6) 100%);
        border: 2px solid rgba(46, 204, 113, 0.5);
    }}
    
    .stat-box-profit {{
        background: linear-gradient(135deg, rgba(155, 89, 182, 0.8) 0%, rgba(142, 68, 173, 0.6) 100%);
        border: 2px solid rgba(155, 89, 182, 0.5);
    }}
    
    .stat-box-loss {{
        background: linear-gradient(135deg, rgba(231, 76, 60, 0.8) 0%, rgba(192, 57, 43, 0.6) 100%);
        border: 2px solid rgba(231, 76, 60, 0.5);
    }}
    
    .stat-box .stat-label {{
        font-size: 0.85rem;
        color: rgba(255,255,255,0.9) !important;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 8px;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
    }}
    
    .stat-box .stat-value {{
        font-size: 1.6rem;
        font-weight: 700;
        color: white !important;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.4);
    }}
    
    /* Overview Competition Cards - Banner Style */
    .overview-comp-card {{
        border-radius: 20px;
        padding: 25px 30px;
        margin-bottom: 20px;
        box-shadow: 0 15px 40px rgba(0,0,0,0.4);
        border: 3px solid rgba(255,255,255,0.3);
        backdrop-filter: blur(10px);
    }}
    
    .overview-comp-header {{
        display: flex;
        align-items: center;
        margin-bottom: 20px;
        padding-bottom: 20px;
        border-bottom: 2px solid rgba(255,255,255,0.2);
    }}
    
    .overview-comp-header img {{
        height: 85px;
        margin-right: 25px;
        filter: drop-shadow(3px 3px 8px rgba(0,0,0,0.5));
    }}
    
    .overview-comp-header h3 {{
        margin: 0;
        font-weight: 800;
        font-size: 1.6rem;
        letter-spacing: 1px;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }}
    
    .overview-comp-profit {{
        font-size: 2rem;
        font-weight: 700;
        text-align: right;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }}
    
    .overview-profit-positive {{
        color: #90EE90 !important;
    }}
    
    .overview-profit-negative {{
        color: #FFB6C1 !important;
    }}
    
    .overview-stats-row {{
        display: flex;
        justify-content: space-around;
        text-align: center;
    }}
    
    .overview-stat-item {{
        padding: 10px 20px;
    }}
    
    .overview-stat-label {{
        font-size: 0.85rem;
        color: rgba(255,255,255,0.8) !important;
        margin-bottom: 5px;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
    }}
    
    .overview-stat-value {{
        font-size: 1.3rem;
        font-weight: 600;
        color: white !important;
        text-shadow: 1px 1px 3px rgba(0,0,0,0.3);
    }}
    
    .overview-stat-value-green {{
        color: #90EE90 !important;
    }}
    
    /* Next Bet Display */
    .next-bet-display {{
        text-align: center;
        margin: 25px 0;
        padding: 20px;
        background: linear-gradient(135deg, rgba(76, 175, 80, 0.3) 0%, rgba(76, 175, 80, 0.1) 100%);
        border-radius: 15px;
        border: 2px solid rgba(76, 175, 80, 0.4);
    }}
    
    .next-bet-label {{
        font-size: 1rem;
        color: rgba(255,255,255,0.85) !important;
        margin-bottom: 5px;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
    }}
    
    .next-bet-value {{
        font-size: 2.2rem;
        font-weight: 700;
        color: #4CAF50 !important;
        text-shadow: 0 0 20px rgba(76, 175, 80, 0.5);
    }}
    
    /* Section Titles */
    .section-title {{
        color: white !important;
        font-size: 1.3rem;
        font-weight: 600;
        margin: 25px 0 15px 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
        display: flex;
        align-items: center;
        gap: 10px;
    }}
    
    /* Balance Display */
    .balance-container {{
        text-align: center;
        margin: 25px 0;
        padding: 20px;
    }}
    
    .balance-label {{
        color: rgba(255,255,255,0.8) !important;
        font-size: 1rem;
        margin-bottom: 5px;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
    }}
    
    .balance-value {{
        font-size: 3rem;
        font-weight: 700;
        text-shadow: 0 0 30px rgba(0,0,0,0.3);
    }}
    
    /* Info messages */
    .info-message {{
        background: rgba(255,255,255,0.15);
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        color: white !important;
        border: 1px solid rgba(255,255,255,0.2);
        text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
    }}
    
    /* Football Loading Animation */
    .loading-container {{
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        min-height: 300px;
        gap: 20px;
    }}
    
    .football-loader {{
        width: 80px;
        height: 80px;
        background: linear-gradient(135deg, #ffffff 0%, #e0e0e0 100%);
        border-radius: 50%;
        position: relative;
        animation: roll 1s linear infinite;
        box-shadow: 
            inset -5px -5px 15px rgba(0,0,0,0.2),
            inset 5px 5px 15px rgba(255,255,255,0.3),
            0 10px 30px rgba(0,0,0,0.4);
    }}
    
    .football-loader::before {{
        content: '';
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        width: 25px;
        height: 25px;
        background: #1a1a1a;
        clip-path: polygon(50% 0%, 100% 38%, 82% 100%, 18% 100%, 0% 38%);
    }}
    
    .football-loader::after {{
        content: '';
        position: absolute;
        top: 10px;
        left: 50%;
        transform: translateX(-50%);
        width: 12px;
        height: 12px;
        background: #1a1a1a;
        clip-path: polygon(50% 0%, 100% 38%, 82% 100%, 18% 100%, 0% 38%);
    }}
    
    @keyframes roll {{
        0% {{
            transform: rotate(0deg) translateX(0);
        }}
        25% {{
            transform: rotate(90deg) translateX(10px);
        }}
        50% {{
            transform: rotate(180deg) translateX(0);
        }}
        75% {{
            transform: rotate(270deg) translateX(-10px);
        }}
        100% {{
            transform: rotate(360deg) translateX(0);
        }}
    }}
    
    .loading-text {{
        color: white;
        font-size: 1.2rem;
        font-weight: 500;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
        animation: pulse 1.5s ease-in-out infinite;
    }}
    
    @keyframes pulse {{
        0%, 100% {{ opacity: 0.6; }}
        50% {{ opacity: 1; }}
    }}
    
    /* Override Streamlit's default spinner with football */
    [data-testid="stSpinner"] {{
        display: flex;
        justify-content: center;
        align-items: center;
    }}
    
    [data-testid="stSpinner"] > div {{
        display: none !important;
    }}
    
    [data-testid="stSpinner"]::after {{
        content: '';
        width: 50px;
        height: 50px;
        background: 
            radial-gradient(circle at 30% 30%, rgba(255,255,255,0.8) 0%, transparent 50%),
            linear-gradient(135deg, #ffffff 0%, #cccccc 100%);
        border-radius: 50%;
        animation: football-spin 0.8s linear infinite;
        box-shadow: 
            inset -3px -3px 10px rgba(0,0,0,0.15),
            inset 3px 3px 10px rgba(255,255,255,0.5),
            0 5px 20px rgba(0,0,0,0.3);
        position: relative;
    }}
    
    @keyframes football-spin {{
        0% {{
            transform: rotate(0deg) translateY(0px);
        }}
        25% {{
            transform: rotate(90deg) translateY(-5px);
        }}
        50% {{
            transform: rotate(180deg) translateY(0px);
        }}
        75% {{
            transform: rotate(270deg) translateY(-5px);
        }}
        100% {{
            transform: rotate(360deg) translateY(0px);
        }}
    }}
    
    /* Full page loading overlay */
    .page-loader {{
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        background: rgba(0, 0, 0, 0.85);
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        z-index: 9999;
        gap: 25px;
    }}
    
    .page-loader .football {{
        width: 100px;
        height: 100px;
        background: 
            radial-gradient(circle at 30% 30%, rgba(255,255,255,0.9) 0%, transparent 40%),
            conic-gradient(from 0deg, #fff 0deg, #fff 60deg, #1a1a1a 60deg, #1a1a1a 120deg, #fff 120deg, #fff 180deg, #1a1a1a 180deg, #1a1a1a 240deg, #fff 240deg, #fff 300deg, #1a1a1a 300deg, #1a1a1a 360deg);
        border-radius: 50%;
        animation: bounce-roll 1.2s ease-in-out infinite;
        box-shadow: 
            inset -8px -8px 20px rgba(0,0,0,0.2),
            inset 8px 8px 20px rgba(255,255,255,0.3),
            0 15px 40px rgba(0,0,0,0.5);
    }}
    
    @keyframes bounce-roll {{
        0%, 100% {{
            transform: translateY(0) rotate(0deg);
        }}
        25% {{
            transform: translateY(-30px) rotate(90deg);
        }}
        50% {{
            transform: translateY(0) rotate(180deg);
        }}
        75% {{
            transform: translateY(-15px) rotate(270deg);
        }}
    }}
    
    .page-loader .loader-text {{
        color: white;
        font-size: 1.4rem;
        font-weight: 600;
        letter-spacing: 2px;
        text-shadow: 2px 2px 8px rgba(0,0,0,0.5);
        animation: pulse 1.5s ease-in-out infinite;
    }}
    
    /* Overview cards - hide text on mobile */
    .overview-comp-name {{
        margin: 0;
        font-weight: 800;
        font-size: 1.6rem;
        letter-spacing: 1px;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        color: white !important;
    }}
    
    @media (max-width: 768px) {{
        .overview-comp-name {{
            display: none !important;
        }}
        
        .overview-comp-header {{
            justify-content: space-between;
        }}
        
        .overview-comp-header img {{
            margin-right: 0;
        }}
    }}
    </style>
""", unsafe_allow_html=True)

# Add page loader JavaScript
st.markdown("""
    <script>
        // Show loader on page navigation
        document.addEventListener('DOMContentLoaded', function() {
            // Create loader element
            const loader = document.createElement('div');
            loader.id = 'page-loader';
            loader.className = 'page-loader';
            loader.innerHTML = '<div class="football"></div><div class="loader-text">Loading...</div>';
            
            // Add to body initially hidden
            loader.style.display = 'none';
            document.body.appendChild(loader);
            
            // Show loader on Streamlit rerun
            const observer = new MutationObserver(function(mutations) {
                mutations.forEach(function(mutation) {
                    if (mutation.target.classList && mutation.target.classList.contains('stApp')) {
                        // Page is updating
                    }
                });
            });
        });
    </script>
""", unsafe_allow_html=True)

# Show loading placeholder while data loads
def show_page_loader():
    """Display full-page football loading animation"""
    st.markdown("""
        <div class="page-loader" id="initial-loader">
            <div class="football"></div>
            <div class="loader-text">Loading...</div>
        </div>
        <script>
            setTimeout(function() {
                var loader = document.getElementById('initial-loader');
                if (loader) loader.style.display = 'none';
            }, 500);
        </script>
    """, unsafe_allow_html=True)

# --- 3. GOOGLE SHEETS CONNECTION ---
@st.cache_data(ttl=15)
def connect_to_sheets():
    """
    Connect to Google Sheets and retrieve data.
    Returns: (raw_data, worksheet, bankroll, error_message)
    """
    # Check for required secrets
    if "service_account" not in st.secrets:
        return None, None, DEFAULT_BANKROLL, "Missing [service_account] in Secrets"
    if "sheet_id" not in st.secrets:
        return None, None, DEFAULT_BANKROLL, "Missing 'sheet_id' in Secrets"
    
    try:
        # Define required scopes
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        
        # Create credentials with scopes
        creds = Credentials.from_service_account_info(
            st.secrets["service_account"],
            scopes=scopes
        )
        
        # Authorize gspread client
        gc = gspread.authorize(creds)
        
    except Exception as e:
        return None, None, DEFAULT_BANKROLL, f"Authentication Error: {str(e)}"
    
    # Try to open the spreadsheet
    try:
        sh = gc.open_by_key(st.secrets["sheet_id"])
    except gspread.exceptions.APIError as e:
        bot_email = st.secrets["service_account"].get("client_email", "Unknown")
        return None, None, DEFAULT_BANKROLL, f"API Error. Share the sheet with: '{bot_email}'. Error: {e}"
    except gspread.exceptions.SpreadsheetNotFound:
        return None, None, DEFAULT_BANKROLL, "Spreadsheet not found. Check the sheet_id in Secrets."
    except Exception as e:
        bot_email = st.secrets["service_account"].get("client_email", "Unknown")
        return None, None, DEFAULT_BANKROLL, f"Access Denied. Share the sheet with: '{bot_email}'. Error: {e}"
    
    # Get the first worksheet
    try:
        worksheet = sh.get_worksheet(0)
    except Exception as e:
        return None, None, DEFAULT_BANKROLL, f"Error accessing worksheet: {str(e)}"
    
    # Read data from worksheet
    try:
        raw_values = worksheet.get_all_values()
        if len(raw_values) > 1:
            headers = [h.strip() for h in raw_values[0]]
            data = [dict(zip(headers, row)) for row in raw_values[1:] if any(cell.strip() for cell in row)]
        else:
            data = []
    except Exception as e:
        data = []
        st.warning(f"Could not read data: {str(e)}")
    
    # Read bankroll value
    try:
        val = worksheet.cell(BANKROLL_CELL_ROW, BANKROLL_CELL_COL).value
        bankroll = float(str(val).replace(',', '').replace('₪', '').strip()) if val else DEFAULT_BANKROLL
    except Exception as e:
        bankroll = DEFAULT_BANKROLL
        st.warning(f"Could not read bankroll, using default: {str(e)}")
    
    return data, worksheet, bankroll, None


def get_worksheet_for_update():
    """
    Get a fresh worksheet connection for updates (bypasses cache).
    """
    if "service_account" not in st.secrets or "sheet_id" not in st.secrets:
        return None
    
    try:
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        creds = Credentials.from_service_account_info(
            st.secrets["service_account"],
            scopes=scopes
        )
        gc = gspread.authorize(creds)
        sh = gc.open_by_key(st.secrets["sheet_id"])
        return sh.get_worksheet(0)
    except Exception as e:
        st.error(f"Connection error: {str(e)}")
        return None


# --- 4. DATA PROCESSING ---
def process_data(raw):
    """
    Process raw data from Google Sheets and calculate betting cycles.
    READS THE ACTUAL RESULT FROM SHEETS - does not override!
    
    The Martingale system works as follows:
    - Start with DEFAULT_STAKE
    - On loss: double the stake for next bet
    - On win: collect winnings and reset stake to DEFAULT_STAKE
    - Profit on win = (stake * odds) - total_invested_in_cycle
    
    Returns: (DataFrame, next_stakes_dict, competition_stats_dict)
    """
    if not raw:
        empty_stats = {
            comp: {"total_staked": 0, "total_income": 0, "net_profit": 0}
            for comp in COMPETITION_STYLES.keys()
        }
        return pd.DataFrame(), {comp: DEFAULT_STAKE for comp in COMPETITION_STYLES.keys()}, empty_stats, 0.0
    
    processed = []
    
    # Track cycle investment per competition
    cycle_investment = {comp: 0.0 for comp in COMPETITION_STYLES.keys()}
    next_bets = {comp: DEFAULT_STAKE for comp in COMPETITION_STYLES.keys()}
    
    # Track overall stats per competition
    comp_stats = {
        comp: {"total_staked": 0.0, "total_income": 0.0, "net_profit": 0.0}
        for comp in COMPETITION_STYLES.keys()
    }
    
    for i, row in enumerate(raw):
        if not isinstance(row, dict):
            continue
        
        # Extract and clean data
        comp = str(row.get('Competition', 'Brighton')).strip()
        if comp not in COMPETITION_STYLES:
            comp = 'Brighton'  # Default fallback
            
        home = str(row.get('Home Team', '')).strip()
        away = str(row.get('Away Team', '')).strip()
        match_name = f"{home} vs {away}" if home and away else "Unknown Match"
        
        # Parse odds
        try:
            odds = float(str(row.get('Odds', '1')).replace(',', '.').strip())
            if odds <= 0:
                odds = 1.0
        except (ValueError, TypeError):
            odds = 1.0
        
        # Parse stake
        try:
            stake_str = str(row.get('Stake', '')).replace(',', '.').replace('₪', '').strip()
            stake = float(stake_str) if stake_str else 0.0
        except (ValueError, TypeError):
            stake = 0.0
        
        # If stake is 0, use the calculated next bet for this competition
        if stake == 0:
            stake = next_bets.get(comp, DEFAULT_STAKE)
        
        # GET THE ACTUAL RESULT FROM SHEETS - THIS IS CRITICAL!
        result = str(row.get('Result', '')).strip()
        date = str(row.get('Date', '')).strip()
        
        # Handle pending bets - no calculations yet
        if result == "Pending" or result == "" or not result:
            processed.append({
                "Row": i + 2,
                "Comp": comp,
                "Match": match_name,
                "Date": date,
                "Profit": 0,
                "Status": "Pending",
                "Stake": stake,
                "Odds": odds,
                "Income": 0,
                "Expense": stake
            })
            continue
        
        # Add stake to cycle investment (this bet was placed)
        cycle_investment[comp] += stake
        comp_stats[comp]["total_staked"] += stake
        
        # Check ACTUAL result from sheet
        # WIN condition: Result is exactly "Draw (X)" or just "Draw"
        # IMPORTANT: "No Draw" should NOT be a win!
        result_lower = result.lower().strip()
        is_win = (result == "Draw (X)" or 
                  result_lower == "draw" or 
                  result_lower == "draw (x)")
        
        # Make sure "No Draw" is NOT a win
        if "no draw" in result_lower or "no_draw" in result_lower:
            is_win = False
        
        if is_win:
            # WIN - Calculate profit based on Martingale
            # Income = stake × odds
            # Net profit = income - all stakes in this cycle (including this bet)
            income = stake * odds
            net_profit = income - cycle_investment[comp]
            
            comp_stats[comp]["total_income"] += income
            comp_stats[comp]["net_profit"] += net_profit
            
            # Reset cycle for next sequence
            cycle_investment[comp] = 0.0
            next_bets[comp] = DEFAULT_STAKE
            status = "Won"
        else:
            # LOSS - No Draw
            # In Martingale, losses are NOT counted as negative profit
            # because they will be covered by the next win
            # The cycle_investment already tracks the total spent
            income = 0.0
            net_profit = 0  # Don't count loss here - it's accounted for in cycle_investment
            
            # Double the stake for next bet (Martingale)
            next_bets[comp] = stake * 2.0
            status = "Lost"
        
        processed.append({
            "Row": i + 2,
            "Comp": comp,
            "Match": match_name,
            "Date": date,
            "Profit": net_profit,
            "Status": status,
            "Stake": stake,
            "Odds": odds,
            "Income": income,
            "Expense": stake
        })
    
    # Calculate pending losses - money still invested in open cycles that hasn't been recovered yet
    # This is important for accurate bankroll display
    pending_losses = sum(cycle_investment.values())
    
    return pd.DataFrame(processed), next_bets, comp_stats, pending_losses


def show_loading(message="Loading data..."):
    """Display football loading animation"""
    st.markdown(f"""
        <div class="loading-container">
            <div class="football-loader"></div>
            <div class="loading-text">{message}</div>
        </div>
    """, unsafe_allow_html=True)


def show_inline_loader():
    """Display inline football loader for smaller operations"""
    st.markdown("""
        <div style="display: flex; justify-content: center; padding: 20px;">
            <div class="football-loader" style="width: 50px; height: 50px;"></div>
        </div>
    """, unsafe_allow_html=True)


# --- 5. LOAD DATA ---
# Use spinner while loading data
with st.spinner(''):
    raw_data, worksheet, initial_bankroll, error_msg = connect_to_sheets()
    df, next_stakes, competition_stats, pending_losses = process_data(raw_data)

# Current balance = Initial bankroll + Net profits from wins - Money still invested in open cycles
current_bal = initial_bankroll + (df['Profit'].sum() if not df.empty else 0) - pending_losses


# --- 6. SIDEBAR ---
with st.sidebar:
    st.image(APP_LOGO_URL, use_container_width=True)
    
    if error_msg:
        st.error("⚠️ Offline Mode")
        if "service_account" in st.secrets:
            bot_email = st.secrets["service_account"].get("client_email", "Unknown")
            st.info(f"🤖 Bot Email:\n`{bot_email}`")
    else:
        st.success("✅ Connected")
    
    st.divider()
    
    # Bankroll Management
    st.markdown("### 💰 Bankroll")
    st.metric("Current", f"₪{initial_bankroll:,.0f}")
    
    amt = st.number_input("Amount", min_value=10.0, value=100.0, step=50.0)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("➕ Deposit", use_container_width=True):
            ws = get_worksheet_for_update()
            if ws:
                ws.update_cell(BANKROLL_CELL_ROW, BANKROLL_CELL_COL, initial_bankroll + amt)
                connect_to_sheets.clear()
                st.rerun()
    with col2:
        if st.button("➖ Withdraw", use_container_width=True):
            ws = get_worksheet_for_update()
            if ws:
                ws.update_cell(BANKROLL_CELL_ROW, BANKROLL_CELL_COL, initial_bankroll - amt)
                connect_to_sheets.clear()
                st.rerun()
    
    st.divider()
    
    # Navigation
    st.markdown("### 🧭 Navigation")
    track = st.selectbox(
        "Select View",
        ["📊 Overview", "Brighton", "Africa Cup of Nations"],
        label_visibility="collapsed"
    )
    
    st.divider()
    
    if st.button("🔄 Refresh Data", use_container_width=True):
        connect_to_sheets.clear()
        st.rerun()


# --- 7. MAIN DISPLAY ---
if error_msg:
    st.error(f"⚠️ Connection Error: {error_msg}")
    st.info("The app is running in offline mode. Please check your connection settings.")
    st.stop()

# --- OVERVIEW PAGE ---
if track == "📊 Overview":
    # Overview Banner - Dark green gradient, NO logo/icon
    st.markdown("""
        <div class="comp-banner-box" style="background: linear-gradient(135deg, #1a472a 0%, #2d5a3d 50%, #4a7c59 100%);">
            <h1 style="color: white; margin: 0; font-size: 2.5rem; letter-spacing: 3px; text-shadow: 2px 2px 4px rgba(0,0,0,0.4);">OVERVIEW</h1>
        </div>
    """, unsafe_allow_html=True)
    
    # Total Balance Display
    balance_color = "#4CAF50" if current_bal >= initial_bankroll else "#FF5252"
    st.markdown(f"""
        <div class="balance-container">
            <p class="balance-label">TOTAL BALANCE</p>
            <h1 class="balance-value" style="color: {balance_color};">₪{current_bal:,.2f}</h1>
        </div>
    """, unsafe_allow_html=True)
    
    # Competition Cards
    st.markdown('<p class="section-title">📈 Competition Performance</p>', unsafe_allow_html=True)
    
    if not df.empty:
        for comp_name, style in COMPETITION_STYLES.items():
            comp_df = df[df['Comp'] == comp_name]
            comp_profit = comp_df['Profit'].sum() if not comp_df.empty else 0
            stats = competition_stats.get(comp_name, {"total_staked": 0, "total_income": 0, "net_profit": 0})
            
            profit_class = "overview-profit-positive" if comp_profit >= 0 else "overview-profit-negative"
            profit_sign = "+" if comp_profit >= 0 else ""
            
            st.markdown(f"""
                <div class="overview-comp-card" style="background: {style['gradient']};">
                    <div class="overview-comp-header">
                        <img src="{style['logo']}" alt="{comp_name}">
                        <h3 class="overview-comp-name">{comp_name}</h3>
                        <div style="flex: 1;"></div>
                        <span class="overview-comp-profit {profit_class}">{profit_sign}₪{comp_profit:,.0f}</span>
                    </div>
                    <div class="overview-stats-row">
                        <div class="overview-stat-item">
                            <div class="overview-stat-label">Total Staked</div>
                            <div class="overview-stat-value">₪{stats['total_staked']:,.0f}</div>
                        </div>
                        <div class="overview-stat-item">
                            <div class="overview-stat-label">Total Won</div>
                            <div class="overview-stat-value overview-stat-value-green">₪{stats['total_income']:,.0f}</div>
                        </div>
                        <div class="overview-stat-item">
                            <div class="overview-stat-label">Matches</div>
                            <div class="overview-stat-value">{len(comp_df)}</div>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
    else:
        show_loading()  # Show football loading when no data

# --- COMPETITION PAGES ---
else:
    comp_name = track
    style = COMPETITION_STYLES.get(comp_name, COMPETITION_STYLES["Brighton"])
    
    # Competition Banner
    st.markdown(f"""
        <div class="comp-banner-box" style="background: {style['gradient']};">
            <img src="{style['logo']}" alt="{comp_name}">
            <h1 class="comp-banner-text" style="color: {style['text_color']};">{comp_name.upper()}</h1>
        </div>
    """, unsafe_allow_html=True)
    
    # Current Balance
    balance_color = "#4CAF50" if current_bal >= initial_bankroll else "#FF5252"
    st.markdown(f"""
        <div class="balance-container">
            <p class="balance-label">CURRENT BALANCE</p>
            <h1 class="balance-value" style="color: {balance_color};">₪{current_bal:,.2f}</h1>
        </div>
    """, unsafe_allow_html=True)
    
    # Filter data for this competition
    comp_df = df[df['Comp'] == comp_name].copy() if not df.empty else pd.DataFrame()
    stats = competition_stats.get(comp_name, {"total_staked": 0, "total_income": 0, "net_profit": 0})
    
    # Statistics Boxes
    st.markdown(f"""
        <div class="stats-container">
            <div class="stat-box stat-box-total">
                <div class="stat-label">💰 Total Staked</div>
                <div class="stat-value">₪{stats['total_staked']:,.0f}</div>
            </div>
            <div class="stat-box stat-box-income">
                <div class="stat-label">🏆 Total Won</div>
                <div class="stat-value">₪{stats['total_income']:,.0f}</div>
            </div>
            <div class="stat-box stat-box-profit">
                <div class="stat-label">📈 Net Profit</div>
                <div class="stat-value">₪{stats['net_profit']:,.0f}</div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # Next Bet Display
    next_bet = next_stakes.get(comp_name, DEFAULT_STAKE)
    st.markdown(f"""
        <div class="next-bet-display">
            <div class="next-bet-label">NEXT RECOMMENDED BET</div>
            <div class="next-bet-value">₪{next_bet:,.0f}</div>
        </div>
    """, unsafe_allow_html=True)
    
    # Add Match Form - Soft and Inviting Design
    st.markdown("""
        <div class="form-card">
            <div class="form-card-title">
                <span style="font-size: 1.5rem;">⚽</span>
                <span style="color: #2d3748 !important;">Add New Match</span>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    with st.form("add_match_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            home_team = st.text_input("Home Team", placeholder="Enter home team name")
        with col2:
            away_team = st.text_input("Away Team", placeholder="Enter away team name")
        
        col3, col4 = st.columns(2)
        with col3:
            odds = st.number_input("Odds", min_value=1.01, value=3.20, step=0.1)
        with col4:
            stake = st.number_input("Stake (₪)", min_value=1.0, value=float(next_bet), step=10.0)
        
        st.write("")  # Spacing
        result = st.radio(
            "Match Result",
            ["Pending", "Draw (X)", "No Draw"],
            horizontal=True
        )
        
        st.write("")  # Spacing
        submitted = st.form_submit_button("✅ Add Match", use_container_width=True, type="primary")
        
        if submitted:
            if home_team and away_team:
                with st.spinner('⚽ Adding match...'):
                    ws = get_worksheet_for_update()
                    if ws:
                        new_row = [
                            str(datetime.date.today()),
                            comp_name,
                            home_team,
                            away_team,
                            odds,
                            result,
                            stake,
                            0
                        ]
                        ws.append_row(new_row)
                        connect_to_sheets.clear()
                    st.success(f"✅ Added: {home_team} vs {away_team}")
                    st.rerun()
            else:
                st.error("⚠️ Please enter both team names")
    
    # Match History
    st.markdown('<p class="section-title">📜 Match History</p>', unsafe_allow_html=True)
    
    if not comp_df.empty:
        for _, row in comp_df.sort_index(ascending=False).iterrows():
            # Determine card style based on ACTUAL status from data
            if row['Status'] == "Won":
                card_class = "match-card-won"
                profit_class = "match-profit-positive"
                profit_prefix = "+"
            elif row['Status'] == "Lost":
                card_class = "match-card-lost"
                profit_class = "match-profit-negative"
                profit_prefix = ""
            else:  # Pending
                card_class = "match-card-pending"
                profit_class = "match-profit-neutral"
                profit_prefix = ""
            
            st.markdown(f"""
                <div class="match-card {card_class}">
                    <div class="match-info">
                        <div class="match-name">{row['Match']}</div>
                        <div class="match-details">
                            📅 {row['Date']} &nbsp;|&nbsp; 💵 Stake: ₪{row['Stake']:,.0f} &nbsp;|&nbsp; 📊 Odds: {row['Odds']:.2f} &nbsp;|&nbsp; 
                            <strong>{row['Status']}</strong>
                        </div>
                    </div>
                    <div class="match-profit {profit_class}">
                        {profit_prefix}₪{row['Profit']:,.0f}
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            # Action buttons for pending matches
            if row['Status'] == "Pending":
                col1, col2, col3 = st.columns([1, 1, 2])
                with col1:
                    if st.button("✅ WIN", key=f"win_{row['Row']}", use_container_width=True):
                        with st.spinner('⚽'):
                            ws = get_worksheet_for_update()
                            if ws:
                                ws.update_cell(row['Row'], RESULT_COL, "Draw (X)")
                                connect_to_sheets.clear()
                                st.rerun()
                with col2:
                    if st.button("❌ LOSS", key=f"loss_{row['Row']}", use_container_width=True):
                        with st.spinner('⚽'):
                            ws = get_worksheet_for_update()
                            if ws:
                                ws.update_cell(row['Row'], RESULT_COL, "No Draw")
                                connect_to_sheets.clear()
                                st.rerun()
    else:
        st.markdown("""
            <div class="info-message">
                📭 No matches recorded yet for this competition. Add your first match above!
            </div>
        """, unsafe_allow_html=True)


# --- FOOTER ---
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("""
    <div style="text-align: center; color: rgba(255,255,255,0.5); font-size: 0.8rem; padding: 20px; text-shadow: 1px 1px 2px rgba(0,0,0,0.5);">
        Elite Football Tracker v2.0 | Built with ❤️ using Streamlit
    </div>
""", unsafe_allow_html=True)