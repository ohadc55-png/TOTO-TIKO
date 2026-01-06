import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import datetime

# --- 1. CONFIGURATION ---
APP_LOGO_URL = "https://i.postimg.cc/8Cr6SypK/yzwb-ll-sm.png"
BG_IMAGE_URL = "https://i.postimg.cc/GmFZ4KS7/Gemini-Generated-Image-k1h11zk1h11zk1h1.png"

# Constants
DEFAULT_STAKE = 30.0
DEFAULT_BANKROLL = 5000.0
BANKROLL_CELL_ROW = 1
BANKROLL_CELL_COL = 10
RESULT_COL = 6

# Sheet names
MATCHES_SHEET = 0  # First sheet (index 0)
COMPETITIONS_SHEET = "Competitions"

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
    
    /* Form elements - Labels should be WHITE (they're on dark background) */
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
    
    /* Banner text - hidden on mobile for competitions only */
    .comp-banner-text {{
        margin: 0;
        font-weight: 900;
        font-size: 2.2rem;
        letter-spacing: 2px;
    }}
    
    /* Overview banner text - always visible */
    .overview-banner-text {{
        margin: 0;
        font-weight: 900;
        font-size: 2.2rem;
        letter-spacing: 2px;
        color: white;
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
        
        /* Hide ONLY competition banner text, not overview */
        .comp-banner-box .comp-banner-text {{
            display: none !important;
        }}
        
        /* Keep overview banner text visible */
        .comp-banner-box .overview-banner-text {{
            display: block !important;
            font-size: 1.8rem;
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
    
    @keyframes roll {{
        0% {{ transform: rotate(0deg) translateX(0); }}
        25% {{ transform: rotate(90deg) translateX(10px); }}
        50% {{ transform: rotate(180deg) translateX(0); }}
        75% {{ transform: rotate(270deg) translateX(-10px); }}
        100% {{ transform: rotate(360deg) translateX(0); }}
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
    }}
    
    @keyframes football-spin {{
        0% {{ transform: rotate(0deg) translateY(0px); }}
        25% {{ transform: rotate(90deg) translateY(-5px); }}
        50% {{ transform: rotate(180deg) translateY(0px); }}
        75% {{ transform: rotate(270deg) translateY(-5px); }}
        100% {{ transform: rotate(360deg) translateY(0px); }}
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
    
    /* Expander styling for dark background */
    [data-testid="stExpander"] {{
        background: rgba(255, 255, 255, 0.1) !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 12px !important;
        margin-bottom: 10px !important;
    }}
    
    [data-testid="stExpander"] summary {{
        color: white !important;
        font-weight: 600 !important;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.5) !important;
    }}
    
    [data-testid="stExpander"] summary:hover {{
        color: #4CABFF !important;
    }}
    
    [data-testid="stExpander"] [data-testid="stMarkdownContainer"] p {{
        color: white !important;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.3) !important;
    }}
    
    [data-testid="stExpander"] label {{
        color: white !important;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.3) !important;
    }}
    
    /* Archive card styling */
    .archive-card {{
        background: linear-gradient(135deg, rgba(108, 117, 125, 0.6) 0%, rgba(73, 80, 87, 0.4) 100%);
        border: 2px solid rgba(108, 117, 125, 0.5);
        border-radius: 16px;
        padding: 20px;
        margin-bottom: 15px;
    }}
    
    .archive-card h4 {{
        color: white !important;
        margin: 0 0 10px 0;
    }}
    
    .archive-card p {{
        color: rgba(255,255,255,0.8) !important;
        margin: 5px 0;
    }}
    
    /* Settings card */
    .settings-card {{
        background: rgba(255,255,255,0.95);
        border-radius: 16px;
        padding: 25px;
        margin-bottom: 20px;
        box-shadow: 0 8px 30px rgba(0,0,0,0.2);
    }}
    
    .settings-card h3 {{
        color: #333 !important;
        margin-bottom: 20px;
    }}
    
    .settings-card label {{
        color: #555 !important;
    }}
    </style>
""", unsafe_allow_html=True)


# --- 3. GOOGLE SHEETS CONNECTION ---
@st.cache_data(ttl=15)
def connect_to_sheets():
    """Connect to Google Sheets and retrieve all data."""
    if "service_account" not in st.secrets:
        return None, None, None, DEFAULT_BANKROLL, [], "Missing [service_account] in Secrets"
    if "sheet_id" not in st.secrets:
        return None, None, None, DEFAULT_BANKROLL, [], "Missing 'sheet_id' in Secrets"
    
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
    except Exception as e:
        return None, None, None, DEFAULT_BANKROLL, [], f"Authentication Error: {str(e)}"
    
    try:
        sh = gc.open_by_key(st.secrets["sheet_id"])
    except Exception as e:
        bot_email = st.secrets["service_account"].get("client_email", "Unknown")
        return None, None, None, DEFAULT_BANKROLL, [], f"Access Denied. Share with: '{bot_email}'. Error: {e}"
    
    # Get Matches worksheet (first sheet)
    try:
        matches_ws = sh.get_worksheet(MATCHES_SHEET)
    except Exception as e:
        return None, None, None, DEFAULT_BANKROLL, [], f"Error accessing matches sheet: {str(e)}"
    
    # Get Competitions worksheet
    try:
        comp_ws = sh.worksheet(COMPETITIONS_SHEET)
    except Exception as e:
        return None, None, None, DEFAULT_BANKROLL, [], f"Error accessing Competitions sheet. Make sure it exists! Error: {str(e)}"
    
    # Read matches data
    try:
        raw_values = matches_ws.get_all_values()
        if len(raw_values) > 1:
            headers = [h.strip() for h in raw_values[0]]
            matches_data = [dict(zip(headers, row)) for row in raw_values[1:] if any(cell.strip() for cell in row)]
        else:
            matches_data = []
    except Exception as e:
        matches_data = []
    
    # Read competitions data
    try:
        comp_values = comp_ws.get_all_values()
        if len(comp_values) > 1:
            comp_headers = [h.strip() for h in comp_values[0]]
            competitions_data = [dict(zip(comp_headers, row)) for row in comp_values[1:] if any(cell.strip() for cell in row)]
        else:
            competitions_data = []
    except Exception as e:
        competitions_data = []
    
    # Read bankroll
    try:
        val = matches_ws.cell(BANKROLL_CELL_ROW, BANKROLL_CELL_COL).value
        bankroll = float(str(val).replace(',', '').replace('₪', '').strip()) if val else DEFAULT_BANKROLL
    except:
        bankroll = DEFAULT_BANKROLL
    
    return matches_data, matches_ws, comp_ws, bankroll, competitions_data, None


def get_spreadsheet():
    """Get fresh spreadsheet connection for updates."""
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
        return gc.open_by_key(st.secrets["sheet_id"])
    except Exception as e:
        st.error(f"Connection error: {str(e)}")
        return None


def get_matches_worksheet():
    """Get matches worksheet for updates."""
    sh = get_spreadsheet()
    if sh:
        return sh.get_worksheet(MATCHES_SHEET)
    return None


def get_competitions_worksheet():
    """Get competitions worksheet for updates."""
    sh = get_spreadsheet()
    if sh:
        try:
            return sh.worksheet(COMPETITIONS_SHEET)
        except:
            return None
    return None


# --- 4. DATA PROCESSING ---
def build_competitions_dict(competitions_data):
    """Build a dictionary of competitions with their settings."""
    comps = {}
    for comp in competitions_data:
        name = comp.get('Name', '').strip()
        if not name:
            continue
        
        # Parse colors
        color1 = comp.get('Color1', '#4CABFF').strip() or '#4CABFF'
        color2 = comp.get('Color2', '#E6F7FF').strip() or '#E6F7FF'
        text_color = comp.get('Text_Color', '#004085').strip() or '#004085'
        
        # Build gradient
        gradient = f"linear-gradient(135deg, {color1} 0%, {color2} 100%)"
        
        # Parse default stake
        try:
            default_stake = float(str(comp.get('Default_Stake', DEFAULT_STAKE)).replace(',', '.'))
        except:
            default_stake = DEFAULT_STAKE
        
        comps[name] = {
            'name': name,
            'description': comp.get('Description', ''),
            'default_stake': default_stake,
            'color1': color1,
            'color2': color2,
            'text_color': text_color,
            'gradient': gradient,
            'logo': comp.get('Logo_URL', ''),
            'status': comp.get('Status', 'Active').strip(),
            'created_date': comp.get('Created_Date', ''),
            'closed_date': comp.get('Closed_Date', ''),
            'row': competitions_data.index(comp) + 2  # +2 for header and 0-index
        }
    
    return comps


def process_data(raw, competitions_dict):
    """Process raw match data and calculate betting cycles."""
    if not raw:
        empty_stats = {name: {"total_staked": 0, "total_income": 0, "net_profit": 0} for name in competitions_dict.keys()}
        return pd.DataFrame(), {name: competitions_dict[name]['default_stake'] for name in competitions_dict.keys()}, empty_stats, 0.0
    
    processed = []
    cycle_investment = {name: 0.0 for name in competitions_dict.keys()}
    next_bets = {name: competitions_dict[name]['default_stake'] for name in competitions_dict.keys()}
    comp_stats = {name: {"total_staked": 0.0, "total_income": 0.0, "net_profit": 0.0} for name in competitions_dict.keys()}
    
    for i, row in enumerate(raw):
        if not isinstance(row, dict):
            continue
        
        comp = str(row.get('Competition', '')).strip()
        if comp not in competitions_dict:
            continue  # Skip unknown competitions
        
        comp_info = competitions_dict[comp]
        home = str(row.get('Home Team', '')).strip()
        away = str(row.get('Away Team', '')).strip()
        match_name = f"{home} vs {away}" if home and away else "Unknown Match"
        
        try:
            odds = float(str(row.get('Odds', '1')).replace(',', '.').strip())
            if odds <= 0:
                odds = 1.0
        except:
            odds = 1.0
        
        try:
            stake_str = str(row.get('Stake', '')).replace(',', '.').replace('₪', '').strip()
            stake = float(stake_str) if stake_str else 0.0
        except:
            stake = 0.0
        
        if stake == 0:
            stake = next_bets.get(comp, comp_info['default_stake'])
        
        result = str(row.get('Result', '')).strip()
        date = str(row.get('Date', '')).strip()
        
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
        
        cycle_investment[comp] += stake
        comp_stats[comp]["total_staked"] += stake
        
        result_lower = result.lower().strip()
        is_win = (result == "Draw (X)" or result_lower == "draw" or result_lower == "draw (x)")
        if "no draw" in result_lower or "no_draw" in result_lower:
            is_win = False
        
        if is_win:
            income = stake * odds
            net_profit = income - cycle_investment[comp]
            comp_stats[comp]["total_income"] += income
            comp_stats[comp]["net_profit"] += net_profit
            cycle_investment[comp] = 0.0
            next_bets[comp] = comp_info['default_stake']
            status = "Won"
        else:
            income = 0.0
            net_profit = 0
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
    
    pending_losses = sum(cycle_investment.values())
    return pd.DataFrame(processed), next_bets, comp_stats, pending_losses


def show_loading(message="Loading data..."):
    """Display football loading animation."""
    st.markdown(f"""
        <div class="loading-container">
            <div class="football-loader"></div>
            <div class="loading-text">{message}</div>
        </div>
    """, unsafe_allow_html=True)


# --- 5. LOAD DATA ---
with st.spinner(''):
    raw_data, matches_ws, comp_ws, initial_bankroll, competitions_raw, error_msg = connect_to_sheets()

# Build competitions dictionary
if competitions_raw:
    competitions = build_competitions_dict(competitions_raw)
else:
    competitions = {}

# Get active and archived competitions
active_competitions = {k: v for k, v in competitions.items() if v['status'] == 'Active'}
archived_competitions = {k: v for k, v in competitions.items() if v['status'] == 'Closed'}

# Process match data
df, next_stakes, competition_stats, pending_losses = process_data(raw_data, competitions) if not error_msg else (pd.DataFrame(), {}, {}, 0)
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
            ws = get_matches_worksheet()
            if ws:
                ws.update_cell(BANKROLL_CELL_ROW, BANKROLL_CELL_COL, initial_bankroll + amt)
                connect_to_sheets.clear()
                st.rerun()
    with col2:
        if st.button("➖ Withdraw", use_container_width=True):
            ws = get_matches_worksheet()
            if ws:
                ws.update_cell(BANKROLL_CELL_ROW, BANKROLL_CELL_COL, initial_bankroll - amt)
                connect_to_sheets.clear()
                st.rerun()
    
    st.divider()
    
    # Navigation
    st.markdown("### 🧭 Navigation")
    
    # Build navigation options with proper labels
    nav_options = ["📊 Overview"]
    comp_name_map = {}  # Map display name to actual name
    
    for name, info in active_competitions.items():
        # Use a shorter format for dropdown
        display_name = f"⚽ {name}"
        nav_options.append(display_name)
        comp_name_map[display_name] = name
    
    nav_options.append("➕ New Competition")
    if archived_competitions:
        nav_options.append("📁 Archive")
    nav_options.append("⚙️ Manage Competitions")
    
    track = st.selectbox("Select View", nav_options, label_visibility="collapsed")
    
    # Show competition logo below dropdown if a competition is selected
    if track.startswith("⚽ "):
        selected_comp = track.replace("⚽ ", "")
        if selected_comp in active_competitions:
            comp_logo = active_competitions[selected_comp].get('logo', '')
            if comp_logo:
                st.markdown(f"""
                    <div style="text-align: center; padding: 10px;">
                        <img src="{comp_logo}" style="height: 60px; filter: drop-shadow(2px 2px 4px rgba(0,0,0,0.3));">
                    </div>
                """, unsafe_allow_html=True)
    
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
    st.markdown("""
        <div class="comp-banner-box" style="background: linear-gradient(135deg, #1a472a 0%, #2d5a3d 50%, #4a7c59 100%);">
            <h1 class="overview-banner-text">OVERVIEW</h1>
        </div>
    """, unsafe_allow_html=True)
    
    balance_color = "#4CAF50" if current_bal >= initial_bankroll else "#FF5252"
    st.markdown(f"""
        <div class="balance-container">
            <p class="balance-label">TOTAL BALANCE</p>
            <h1 class="balance-value" style="color: {balance_color};">₪{current_bal:,.2f}</h1>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<p class="section-title">📈 Active Competitions</p>', unsafe_allow_html=True)
    
    if active_competitions and not df.empty:
        for comp_name, comp_info in active_competitions.items():
            comp_df = df[df['Comp'] == comp_name]
            comp_profit = comp_df['Profit'].sum() if not comp_df.empty else 0
            stats = competition_stats.get(comp_name, {"total_staked": 0, "total_income": 0, "net_profit": 0})
            
            profit_class = "overview-profit-positive" if comp_profit >= 0 else "overview-profit-negative"
            profit_sign = "+" if comp_profit >= 0 else ""
            
            logo_html = f'<img src="{comp_info["logo"]}" alt="{comp_name}">' if comp_info["logo"] else ''
            
            st.markdown(f"""
                <div class="overview-comp-card" style="background: {comp_info['gradient']};">
                    <div class="overview-comp-header">
                        {logo_html}
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
    elif not active_competitions:
        st.markdown("""
            <div class="info-message">
                📭 No active competitions. Create your first competition to get started!
            </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
            <div class="info-message">
                📭 No betting data available yet. Add your first match to get started!
            </div>
        """, unsafe_allow_html=True)

# --- NEW COMPETITION PAGE ---
elif track == "➕ New Competition":
    st.markdown("""
        <div class="comp-banner-box" style="background: linear-gradient(135deg, #6c5ce7 0%, #a29bfe 100%);">
            <h1 class="overview-banner-text">➕ NEW COMPETITION</h1>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
        <div class="form-card">
            <div class="form-card-title">
                <span style="font-size: 1.5rem;">🏆</span>
                <span style="color: #2d3748 !important;">Create New Competition</span>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    with st.form("new_competition_form"):
        comp_name = st.text_input("Competition Name *", placeholder="e.g., Premier League")
        comp_desc = st.text_input("Description", placeholder="e.g., English top division")
        
        col1, col2 = st.columns(2)
        with col1:
            default_stake = st.number_input("Default Stake (₪)", min_value=1.0, value=30.0, step=5.0)
        with col2:
            logo_url = st.text_input("Logo URL", placeholder="https://example.com/logo.png")
        
        st.markdown("**Colors:**")
        col3, col4, col5 = st.columns(3)
        with col3:
            color1 = st.color_picker("Primary Color", "#4CABFF")
        with col4:
            color2 = st.color_picker("Secondary Color", "#E6F7FF")
        with col5:
            text_color = st.color_picker("Text Color", "#004085")
        
        # Preview
        st.markdown("**Preview:**")
        preview_gradient = f"linear-gradient(135deg, {color1} 0%, {color2} 100%)"
        logo_preview = f'<img src="{logo_url}" style="height:50px; margin-right:15px;">' if logo_url else ''
        st.markdown(f"""
            <div style="background: {preview_gradient}; border-radius: 15px; padding: 20px; display: flex; align-items: center; justify-content: center;">
                {logo_preview}
                <span style="color: {text_color}; font-weight: bold; font-size: 1.3rem;">{comp_name or 'Competition Name'}</span>
            </div>
        """, unsafe_allow_html=True)
        
        submitted = st.form_submit_button("✅ Create Competition", use_container_width=True, type="primary")
        
        if submitted:
            if comp_name:
                if comp_name in competitions:
                    st.error(f"⚠️ Competition '{comp_name}' already exists!")
                else:
                    with st.spinner('⚽ Creating competition...'):
                        ws = get_competitions_worksheet()
                        if ws:
                            new_row = [
                                comp_name,
                                comp_desc,
                                default_stake,
                                color1,
                                color2,
                                text_color,
                                logo_url,
                                "Active",
                                str(datetime.date.today()),
                                ""
                            ]
                            ws.append_row(new_row)
                            connect_to_sheets.clear()
                            st.success(f"✅ Competition '{comp_name}' created!")
                            st.rerun()
            else:
                st.error("⚠️ Please enter a competition name")

# --- ARCHIVE PAGE ---
elif track == "📁 Archive":
    st.markdown("""
        <div class="comp-banner-box" style="background: linear-gradient(135deg, #636e72 0%, #b2bec3 100%);">
            <h1 class="overview-banner-text">📁 ARCHIVE</h1>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<p class="section-title">📜 Closed Competitions</p>', unsafe_allow_html=True)
    
    if archived_competitions:
        for comp_name, comp_info in archived_competitions.items():
            comp_df = df[df['Comp'] == comp_name]
            comp_profit = comp_df['Profit'].sum() if not comp_df.empty else 0
            stats = competition_stats.get(comp_name, {"total_staked": 0, "total_income": 0, "net_profit": 0})
            
            profit_color = "#90EE90" if comp_profit >= 0 else "#FFB6C1"
            logo_html = f'<img src="{comp_info["logo"]}" style="height:40px; margin-right:15px;">' if comp_info["logo"] else ''
            
            st.markdown(f"""
                <div class="archive-card">
                    <div style="display: flex; align-items: center; margin-bottom: 10px;">
                        {logo_html}
                        <h4>{comp_name}</h4>
                    </div>
                    <p>📅 Closed: {comp_info['closed_date'] or 'N/A'}</p>
                    <p>💰 Total Staked: ₪{stats['total_staked']:,.0f}</p>
                    <p>🏆 Total Won: ₪{stats['total_income']:,.0f}</p>
                    <p style="font-size: 1.2rem; color: {profit_color};">📈 Final Profit: ₪{comp_profit:,.0f}</p>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("""
            <div class="info-message">
                📭 No archived competitions yet.
            </div>
        """, unsafe_allow_html=True)

# --- MANAGE COMPETITIONS PAGE ---
elif track == "⚙️ Manage Competitions":
    st.markdown("""
        <div class="comp-banner-box" style="background: linear-gradient(135deg, #2d3436 0%, #636e72 100%);">
            <h1 class="overview-banner-text">⚙️ MANAGE COMPETITIONS</h1>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<p class="section-title">🏆 Active Competitions</p>', unsafe_allow_html=True)
    
    for comp_name, comp_info in active_competitions.items():
        with st.expander(f"⚽ {comp_name}", expanded=False):
            # Use white text for visibility
            st.markdown(f"""
                <div style="color: white; text-shadow: 1px 1px 2px rgba(0,0,0,0.5);">
                    <p><strong>📝 Description:</strong> {comp_info['description'] or 'N/A'}</p>
                    <p><strong>💵 Default Stake:</strong> ₪{comp_info['default_stake']}</p>
                    <p><strong>📅 Created:</strong> {comp_info['created_date']}</p>
                </div>
            """, unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                new_stake = st.number_input(
                    f"Update Default Stake",
                    min_value=1.0,
                    value=float(comp_info['default_stake']),
                    step=5.0,
                    key=f"stake_{comp_name}"
                )
                if st.button("💾 Save Stake", key=f"save_{comp_name}"):
                    with st.spinner('⚽'):
                        ws = get_competitions_worksheet()
                        if ws:
                            ws.update_cell(comp_info['row'], 3, new_stake)  # Column C = Default_Stake
                            connect_to_sheets.clear()
                            st.success("✅ Updated!")
                            st.rerun()
            
            with col2:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button(f"🔒 Close Competition", key=f"close_{comp_name}"):
                    with st.spinner('⚽'):
                        ws = get_competitions_worksheet()
                        if ws:
                            ws.update_cell(comp_info['row'], 8, "Closed")  # Column H = Status
                            ws.update_cell(comp_info['row'], 10, str(datetime.date.today()))  # Column J = Closed_Date
                            connect_to_sheets.clear()
                            st.success(f"✅ '{comp_name}' closed and moved to archive!")
                            st.rerun()

# --- COMPETITION PAGES ---
elif track.startswith("⚽ "):
    comp_name = track.replace("⚽ ", "")
    
    if comp_name not in active_competitions:
        st.error("Competition not found!")
        st.stop()
    
    comp_info = active_competitions[comp_name]
    
    # Competition Banner
    logo_html = f'<img src="{comp_info["logo"]}" alt="{comp_name}">' if comp_info["logo"] else ''
    st.markdown(f"""
        <div class="comp-banner-box" style="background: {comp_info['gradient']};">
            {logo_html}
            <h1 class="comp-banner-text" style="color: {comp_info['text_color']};">{comp_name.upper()}</h1>
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
    next_bet = next_stakes.get(comp_name, comp_info['default_stake'])
    st.markdown(f"""
        <div class="next-bet-display">
            <div class="next-bet-label">NEXT RECOMMENDED BET</div>
            <div class="next-bet-value">₪{next_bet:,.0f}</div>
        </div>
    """, unsafe_allow_html=True)
    
    # Add Match Form
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
        
        st.write("")
        result = st.radio("Match Result", ["Pending", "Draw (X)", "No Draw"], horizontal=True)
        
        st.write("")
        submitted = st.form_submit_button("✅ Add Match", use_container_width=True, type="primary")
        
        if submitted:
            if home_team and away_team:
                with st.spinner('⚽ Adding match...'):
                    ws = get_matches_worksheet()
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
            if row['Status'] == "Won":
                card_class = "match-card-won"
                profit_class = "match-profit-positive"
                profit_prefix = "+"
            elif row['Status'] == "Lost":
                card_class = "match-card-lost"
                profit_class = "match-profit-negative"
                profit_prefix = ""
            else:
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
            
            if row['Status'] == "Pending":
                col1, col2, col3 = st.columns([1, 1, 2])
                with col1:
                    if st.button("✅ WIN", key=f"win_{row['Row']}", use_container_width=True):
                        with st.spinner('⚽'):
                            ws = get_matches_worksheet()
                            if ws:
                                ws.update_cell(row['Row'], RESULT_COL, "Draw (X)")
                                connect_to_sheets.clear()
                                st.rerun()
                with col2:
                    if st.button("❌ LOSS", key=f"loss_{row['Row']}", use_container_width=True):
                        with st.spinner('⚽'):
                            ws = get_matches_worksheet()
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
        Elite Football Tracker v3.0 | Built with ❤️ using Streamlit
    </div>
""", unsafe_allow_html=True)