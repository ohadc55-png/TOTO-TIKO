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
    /* ============================================================
       ELITE FOOTBALL TRACKER - Light Analytical Sports Dashboard
       ============================================================ */

    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

    /* --- CSS Custom Properties --- */
    :root {{
        --bg-page: #F0F2F5;
        --bg-card: #FFFFFF;
        --bg-card-hover: #F8F9FA;
        --bg-sidebar: #1B2A4A;
        --bg-sidebar-hover: #243558;
        --bg-input: #F5F6F8;
        --bg-banner: #1B2A4A;

        --border-light: #E2E5EA;
        --border-medium: #D0D4DA;

        --text-dark: #1A1D23;
        --text-body: #3D4250;
        --text-muted: #8C92A0;
        --text-on-dark: #FFFFFF;
        --text-on-dark-muted: rgba(255,255,255,0.65);

        --accent: #2563EB;
        --accent-light: #DBEAFE;
        --accent-dark: #1E40AF;

        --color-staked: #6B7280;
        --color-won: #059669;
        --color-won-bg: #ECFDF5;
        --color-profit: #16A34A;
        --color-profit-bg: #F0FDF4;
        --color-loss: #DC2626;
        --color-loss-bg: #FEF2F2;
        --color-pending: #D97706;
        --color-pending-bg: #FFFBEB;
        --color-next-bet: #7C3AED;
        --color-next-bet-bg: #F5F3FF;

        --radius-sm: 8px;
        --radius-md: 12px;
        --radius-lg: 16px;

        --shadow-sm: 0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04);
        --shadow-md: 0 4px 12px rgba(0,0,0,0.08), 0 1px 3px rgba(0,0,0,0.04);
        --shadow-lg: 0 8px 24px rgba(0,0,0,0.1), 0 2px 6px rgba(0,0,0,0.04);

        --transition-fast: 0.15s ease;
    }}


    * {{
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        -webkit-font-smoothing: antialiased;
    }}

    /* --- Background --- */
    [data-testid="stAppViewContainer"] {{
        background-image:
            linear-gradient(
                175deg,
                rgba(240, 242, 245, 0.75) 0%,
                rgba(235, 238, 243, 0.70) 40%,
                rgba(230, 234, 240, 0.72) 100%
            ),
            url("{BG_IMAGE_URL}");
        background-attachment: fixed;
        background-size: cover;
        background-position: center;
    }}

    /* --- Global text colors (light theme) --- */
    [data-testid="stAppViewContainer"] [data-testid="stMain"] h1,
    [data-testid="stAppViewContainer"] [data-testid="stMain"] h2,
    [data-testid="stAppViewContainer"] [data-testid="stMain"] h3,
    [data-testid="stAppViewContainer"] [data-testid="stMain"] h4 {{
        color: var(--text-dark) !important;
        font-weight: 700;
    }}

    [data-testid="stAppViewContainer"] [data-testid="stMain"] p,
    [data-testid="stAppViewContainer"] [data-testid="stMain"] span,
    [data-testid="stAppViewContainer"] [data-testid="stMain"] label,
    [data-testid="stAppViewContainer"] [data-testid="stMain"] li,
    [data-testid="stAppViewContainer"] [data-testid="stMain"] div {{
        color: var(--text-body) !important;
    }}

    [data-testid="stAppViewContainer"] [data-testid="stMain"] strong {{
        color: var(--text-dark) !important;
    }}

    [data-testid="stMarkdownContainer"] p {{
        color: var(--text-body) !important;
        line-height: 1.6;
    }}

    [data-testid="stMetricValue"] {{
        color: var(--text-dark) !important;
        font-weight: 800 !important;
        font-variant-numeric: tabular-nums;
    }}

    [data-testid="stMetricLabel"] {{
        color: var(--text-muted) !important;
        font-size: 0.72rem !important;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        font-weight: 600 !important;
    }}

    /* Streamlit header transparency */
    header[data-testid="stHeader"] {{
        background: transparent !important;
    }}

    /* --- Sidebar (dark navy) --- */
    [data-testid="stSidebar"] {{
        background: linear-gradient(180deg, #1B2A4A 0%, #162240 100%) !important;
        border-right: 1px solid rgba(255,255,255,0.08) !important;
    }}

    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {{
        color: var(--text-on-dark) !important;
        font-weight: 700 !important;
        font-size: 0.95rem !important;
    }}

    [data-testid="stSidebar"] h4 {{
        color: var(--text-on-dark-muted) !important;
        font-weight: 600 !important;
    }}

    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] .stMarkdown {{
        color: var(--text-on-dark-muted) !important;
    }}

    [data-testid="stSidebar"] [data-testid="stMetricValue"] {{
        color: var(--text-on-dark) !important;
        font-size: 1.4rem !important;
        font-weight: 800 !important;
    }}

    [data-testid="stSidebar"] [data-testid="stMetricLabel"] {{
        color: var(--text-on-dark-muted) !important;
    }}

    [data-testid="stSidebar"] hr {{
        border-color: rgba(255,255,255,0.1) !important;
        margin: 16px 0 !important;
    }}

    [data-testid="stSidebar"] button {{
        background: rgba(255,255,255,0.08) !important;
        border: 1px solid rgba(255,255,255,0.15) !important;
        color: var(--text-on-dark) !important;
        border-radius: var(--radius-sm) !important;
        font-weight: 600 !important;
        font-size: 0.82rem !important;
        transition: all var(--transition-fast) !important;
    }}

    [data-testid="stSidebar"] button:hover {{
        background: rgba(255,255,255,0.15) !important;
        border-color: rgba(255,255,255,0.25) !important;
    }}

    [data-testid="stSidebar"] button p,
    [data-testid="stSidebar"] button span,
    [data-testid="stSidebar"] button div {{
        color: var(--text-on-dark) !important;
    }}

    [data-testid="stSidebar"] [data-baseweb="select"] {{
        background: rgba(255,255,255,0.08) !important;
    }}

    [data-testid="stSidebar"] [data-baseweb="select"] div {{
        color: var(--text-on-dark) !important;
        background: transparent !important;
    }}

    [data-testid="stSidebar"] input {{
        background: rgba(255,255,255,0.08) !important;
        border: 1px solid rgba(255,255,255,0.15) !important;
        color: var(--text-on-dark) !important;
        border-radius: var(--radius-sm) !important;
    }}

    [data-testid="stSidebar"] input:focus {{
        border-color: var(--accent) !important;
        box-shadow: 0 0 0 2px rgba(37,99,235,0.3) !important;
    }}

    /* --- Forms --- */
    [data-testid="stForm"] {{
        background: var(--bg-card) !important;
        border: 1px solid var(--border-light) !important;
        border-radius: var(--radius-md) !important;
        padding: 8px !important;
        box-shadow: var(--shadow-sm) !important;
    }}

    [data-testid="stForm"] label {{
        color: var(--text-body) !important;
        font-weight: 600 !important;
        font-size: 0.8rem !important;
        text-transform: uppercase;
        letter-spacing: 0.8px;
    }}

    [data-testid="stForm"] input,
    [data-testid="stForm"] textarea {{
        background: var(--bg-input) !important;
        border: 1px solid var(--border-light) !important;
        color: var(--text-dark) !important;
        border-radius: var(--radius-sm) !important;
        font-weight: 500 !important;
    }}

    [data-testid="stForm"] input:focus,
    [data-testid="stForm"] textarea:focus {{
        border-color: var(--accent) !important;
        box-shadow: 0 0 0 3px rgba(37,99,235,0.15) !important;
        outline: none !important;
    }}

    [data-testid="stForm"] input::placeholder,
    [data-testid="stForm"] textarea::placeholder {{
        color: var(--text-muted) !important;
    }}

    [data-testid="stForm"] [data-testid="stMarkdownContainer"] {{
        color: var(--text-dark) !important;
    }}

    [data-testid="stForm"] [data-baseweb="radio"] div {{
        color: var(--text-dark) !important;
    }}

    [data-testid="stForm"] .stRadio label,
    [data-testid="stForm"] .stRadio p {{
        color: var(--text-dark) !important;
        font-weight: 500 !important;
    }}

    /* Submit button */
    [data-testid="stForm"] button[kind="primaryFormSubmit"],
    [data-testid="stForm"] button[type="submit"] {{
        background: var(--accent) !important;
        color: #FFFFFF !important;
        font-weight: 700 !important;
        border: none !important;
        border-radius: var(--radius-sm) !important;
        box-shadow: 0 2px 8px rgba(37,99,235,0.25) !important;
        transition: all var(--transition-fast) !important;
    }}

    [data-testid="stForm"] button[kind="primaryFormSubmit"]:hover,
    [data-testid="stForm"] button[type="submit"]:hover {{
        background: var(--accent-dark) !important;
        box-shadow: 0 4px 16px rgba(37,99,235,0.3) !important;
        transform: translateY(-1px);
    }}

    [data-testid="stForm"] button[kind="primaryFormSubmit"] p,
    [data-testid="stForm"] button[kind="primaryFormSubmit"] span,
    [data-testid="stForm"] button[kind="primaryFormSubmit"] div {{
        color: #FFFFFF !important;
    }}

    [data-testid="stForm"] [data-baseweb="select"] div {{
        color: var(--text-dark) !important;
    }}

    [data-testid="stForm"] [data-baseweb="input"] {{
        background: var(--bg-input) !important;
    }}

    /* --- Form Card --- */
    .form-card {{
        background: var(--bg-card);
        border-radius: var(--radius-md);
        padding: 20px 24px;
        margin: 20px 0 8px 0;
        box-shadow: var(--shadow-sm);
        border: 1px solid var(--border-light);
    }}

    .form-card-title {{
        color: var(--text-dark) !important;
        font-size: 1.05rem;
        font-weight: 700;
        margin-bottom: 0;
        display: flex;
        align-items: center;
        gap: 10px;
    }}

    .form-card-title span {{
        color: var(--text-dark) !important;
    }}

    /* --- Match Cards --- */
    .match-card {{
        border-radius: var(--radius-md);
        padding: 16px 20px;
        margin-bottom: 8px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        background: var(--bg-card);
        border: 1px solid var(--border-light);
        box-shadow: var(--shadow-sm);
        transition: all var(--transition-fast);
    }}

    .match-card:hover {{
        box-shadow: var(--shadow-md);
        transform: translateY(-1px);
    }}

    .match-card-won {{
        border: 1.5px solid #34D399;
        border-left: 4px solid #059669;
        background: #ECFDF5;
    }}

    .match-card-lost {{
        border: 1.5px solid #FCA5A5;
        border-left: 4px solid #DC2626;
        background: #FFF1F2;
    }}

    .match-card-pending {{
        border: 1.5px solid #FCD34D;
        border-left: 4px solid #D97706;
        background: #FFFBEB;
    }}

    .match-card .match-info {{
        flex: 1;
    }}

    .match-card .match-name {{
        font-size: 0.95rem;
        font-weight: 700;
        color: var(--text-dark) !important;
        margin-bottom: 4px;
    }}

    .match-card .match-details {{
        font-size: 0.78rem;
        color: var(--text-muted) !important;
        font-weight: 500;
    }}

    .match-card .match-details strong {{
        color: var(--text-body) !important;
    }}

    .match-card .match-profit {{
        font-size: 1.1rem;
        font-weight: 800;
        font-variant-numeric: tabular-nums;
    }}

    /* Match profit colors */
    [data-testid="stAppViewContainer"] .match-profit-positive {{
        color: var(--color-profit) !important;
    }}

    [data-testid="stAppViewContainer"] .match-profit-negative {{
        color: var(--color-loss) !important;
    }}

    [data-testid="stAppViewContainer"] .match-profit-neutral {{
        color: var(--color-pending) !important;
    }}

    /* --- Page Banner --- */
    .comp-banner-box {{
        border-radius: var(--radius-lg);
        padding: 28px 36px;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-bottom: 28px;
        box-shadow: var(--shadow-md);
        position: relative;
        overflow: hidden;
    }}

    .comp-banner-box::before {{
        content: '';
        position: absolute;
        inset: 0;
        background: linear-gradient(135deg, rgba(27,42,74,0.7) 0%, rgba(22,34,64,0.8) 100%);
        z-index: 0;
        pointer-events: none;
    }}

    .comp-banner-box > * {{
        position: relative;
        z-index: 1;
    }}

    .comp-banner-box img {{
        height: 68px;
        margin-right: 24px;
        filter: drop-shadow(2px 2px 6px rgba(0,0,0,0.3));
        transition: transform 0.3s ease;
    }}

    .comp-banner-box:hover img {{
        transform: scale(1.04);
    }}

    [data-testid="stAppViewContainer"] [data-testid="stMain"] [data-testid="stMarkdownContainer"] .banner-title {{
        margin: 0;
        font-weight: 800;
        font-size: 1.6rem;
        letter-spacing: 6px;
        text-transform: uppercase;
        color: #FFFFFF !important;
        text-shadow: 0 2px 10px rgba(0,0,0,0.3);
    }}

    .comp-banner-box .banner-title {{
        color: #FFFFFF !important;
    }}

    /* --- Stats Container --- */
    .stats-container {{
        display: flex;
        gap: 14px;
        margin: 24px 0;
        flex-wrap: wrap;
    }}

    .stat-box {{
        flex: 1;
        min-width: 140px;
        border-radius: var(--radius-md);
        padding: 18px 20px;
        text-align: center;
        background: var(--bg-card);
        border: 1px solid var(--border-light);
        box-shadow: var(--shadow-sm);
        transition: all var(--transition-fast);
    }}

    .stat-box:hover {{
        box-shadow: var(--shadow-md);
    }}

    .stat-box .stat-label {{
        font-size: 0.68rem;
        color: var(--text-muted) !important;
        text-transform: uppercase;
        letter-spacing: 2px;
        margin-bottom: 8px;
        font-weight: 700;
    }}

    .stat-box .stat-value {{
        font-size: 1.3rem;
        font-weight: 800;
        color: var(--text-dark) !important;
        font-variant-numeric: tabular-nums;
    }}

    /* Staked = gray (neutral, money out) */
    [data-testid="stAppViewContainer"] .stat-box-total .stat-value {{
        color: var(--color-staked) !important;
    }}

    /* Won = green */
    [data-testid="stAppViewContainer"] .stat-box-income {{
        border-bottom: 3px solid var(--color-won);
    }}

    [data-testid="stAppViewContainer"] .stat-box-income .stat-value {{
        color: var(--color-won) !important;
    }}

    /* Net Profit dynamic */
    [data-testid="stAppViewContainer"] .stat-value-profit-pos {{
        color: var(--color-profit) !important;
    }}

    [data-testid="stAppViewContainer"] .stat-value-profit-neg {{
        color: var(--color-loss) !important;
    }}

    [data-testid="stAppViewContainer"] .stat-box-profit-up {{
        border-bottom: 3px solid var(--color-profit);
    }}

    [data-testid="stAppViewContainer"] .stat-box-profit-down {{
        border-bottom: 3px solid var(--color-loss);
    }}

    /* --- Overview Competition Cards --- */
    .overview-comp-card {{
        border-radius: var(--radius-md);
        padding: 20px 24px;
        margin-bottom: 14px;
        box-shadow: var(--shadow-sm);
        border: 1px solid var(--border-light);
        position: relative;
        overflow: hidden;
        transition: all var(--transition-fast);
    }}

    .overview-comp-card:hover {{
        box-shadow: var(--shadow-md);
        transform: translateY(-2px);
    }}

    .overview-comp-card::before {{
        content: '';
        position: absolute;
        inset: 0;
        background: linear-gradient(135deg, rgba(255,255,255,0.75) 0%, rgba(255,255,255,0.85) 100%);
        z-index: 0;
        pointer-events: none;
    }}

    .overview-comp-card > * {{
        position: relative;
        z-index: 1;
    }}

    .overview-comp-header {{
        display: flex;
        align-items: center;
        margin-bottom: 14px;
        padding-bottom: 12px;
        border-bottom: 1px solid var(--border-light);
    }}

    .overview-comp-header img {{
        height: 50px;
        margin-right: 16px;
        filter: drop-shadow(1px 1px 3px rgba(0,0,0,0.15));
    }}

    .overview-comp-header h3 {{
        margin: 0;
        font-weight: 700;
        font-size: 1.1rem;
        color: var(--text-dark) !important;
    }}

    .overview-comp-name {{
        margin: 0;
        font-weight: 700;
        font-size: 1.1rem;
        color: var(--text-dark) !important;
    }}

    .overview-comp-profit {{
        font-size: 1.4rem;
        font-weight: 800;
        text-align: right;
        font-variant-numeric: tabular-nums;
    }}

    [data-testid="stAppViewContainer"] .overview-profit-positive {{
        color: var(--color-profit) !important;
    }}

    [data-testid="stAppViewContainer"] .overview-profit-negative {{
        color: var(--color-loss) !important;
    }}

    .overview-stats-row {{
        display: flex;
        justify-content: space-around;
        text-align: center;
    }}

    .overview-stat-item {{
        padding: 8px 16px;
    }}

    .overview-stat-label {{
        font-size: 0.68rem;
        color: var(--text-muted) !important;
        margin-bottom: 4px;
        text-transform: uppercase;
        letter-spacing: 2px;
        font-weight: 700;
    }}

    .overview-stat-value {{
        font-size: 1.05rem;
        font-weight: 800;
        color: var(--text-dark) !important;
        font-variant-numeric: tabular-nums;
    }}

    [data-testid="stAppViewContainer"] .overview-stat-value-staked {{
        color: var(--color-staked) !important;
    }}

    [data-testid="stAppViewContainer"] .overview-stat-value-green {{
        color: var(--color-won) !important;
    }}

    /* --- Next Bet Display --- */
    .next-bet-display {{
        text-align: center;
        margin: 24px 0;
        padding: 22px;
        background: var(--color-next-bet-bg);
        border-radius: var(--radius-md);
        border: 1px solid #E9D5FF;
        box-shadow: var(--shadow-sm);
    }}

    .next-bet-label {{
        font-size: 0.68rem;
        color: var(--text-muted) !important;
        margin-bottom: 6px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 2.5px;
    }}

    .next-bet-value {{
        font-size: 2.2rem;
        font-weight: 900;
        color: var(--color-next-bet) !important;
        font-variant-numeric: tabular-nums;
    }}

    /* --- Section Titles --- */
    .section-title {{
        color: var(--text-muted) !important;
        font-size: 0.72rem;
        font-weight: 700;
        margin: 28px 0 14px 0;
        text-transform: uppercase;
        letter-spacing: 3px;
        display: flex;
        align-items: center;
        gap: 10px;
    }}

    .section-title::after {{
        content: '';
        flex: 1;
        height: 1px;
        background: linear-gradient(90deg, var(--border-light), transparent);
    }}

    /* --- Balance Display --- */
    .balance-container {{
        text-align: center;
        margin: 24px 0;
        padding: 20px;
    }}

    .balance-label {{
        color: var(--text-muted) !important;
        font-size: 0.72rem;
        margin-bottom: 6px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 3px;
    }}

    .balance-value {{
        font-size: 2.8rem;
        font-weight: 900;
        font-variant-numeric: tabular-nums;
        line-height: 1.1;
    }}

    [data-testid="stAppViewContainer"] .balance-positive {{
        color: var(--color-profit) !important;
    }}

    [data-testid="stAppViewContainer"] .balance-negative {{
        color: var(--color-loss) !important;
    }}

    /* --- Info Messages --- */
    .info-message {{
        background: var(--bg-card);
        border-radius: var(--radius-md);
        padding: 28px;
        text-align: center;
        color: var(--text-muted) !important;
        border: 1px solid var(--border-light);
        box-shadow: var(--shadow-sm);
        font-weight: 500;
    }}

    /* --- Football Loading Animation --- */
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
        color: var(--text-muted);
        font-size: 1rem;
        font-weight: 500;
        animation: pulse 1.5s ease-in-out infinite;
    }}

    @keyframes pulse {{
        0%, 100% {{ opacity: 0.6; }}
        50% {{ opacity: 1; }}
    }}

    /* --- Spinner Override --- */
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

    /* --- Expander Styles --- */
    [data-testid="stExpander"] {{
        background: var(--bg-card) !important;
        border: 1px solid var(--border-light) !important;
        border-radius: var(--radius-md) !important;
        margin-bottom: 10px !important;
        box-shadow: var(--shadow-sm) !important;
        overflow: hidden !important;
    }}

    [data-testid="stExpander"] summary {{
        color: var(--text-dark) !important;
        font-weight: 700 !important;
        padding: 14px 18px !important;
    }}

    [data-testid="stExpander"] summary:hover {{
        color: var(--accent) !important;
    }}

    [data-testid="stExpander"] summary span {{
        color: inherit !important;
    }}

    [data-testid="stExpander"] [data-testid="stMarkdownContainer"] p {{
        color: var(--text-body) !important;
    }}

    [data-testid="stExpander"] [data-testid="stMarkdownContainer"] strong {{
        color: var(--text-dark) !important;
    }}

    [data-testid="stExpander"] label {{
        color: var(--text-body) !important;
    }}

    [data-testid="stExpander"] input {{
        background: var(--bg-input) !important;
        border: 1px solid var(--border-light) !important;
        color: var(--text-dark) !important;
        border-radius: var(--radius-sm) !important;
    }}

    [data-testid="stExpander"] button {{
        background: var(--bg-card) !important;
        border: 1px solid var(--border-medium) !important;
        color: var(--text-body) !important;
        border-radius: var(--radius-sm) !important;
        font-weight: 600 !important;
        transition: all var(--transition-fast) !important;
    }}

    [data-testid="stExpander"] button:hover {{
        border-color: var(--accent) !important;
        color: var(--accent) !important;
    }}

    [data-testid="stExpander"] button p,
    [data-testid="stExpander"] button span {{
        color: inherit !important;
    }}

    /* --- Archive Card --- */
    .archive-card {{
        background: var(--bg-card);
        border: 1px solid var(--border-light);
        border-radius: var(--radius-md);
        padding: 20px 24px;
        margin-bottom: 12px;
        box-shadow: var(--shadow-sm);
        transition: all var(--transition-fast);
    }}

    .archive-card:hover {{
        box-shadow: var(--shadow-md);
    }}

    .archive-card h4 {{
        color: var(--text-dark) !important;
        margin: 0 0 10px 0;
        font-weight: 700;
    }}

    .archive-card p {{
        color: var(--text-body) !important;
        margin: 5px 0;
        font-weight: 500;
    }}

    .archive-card strong {{
        color: var(--text-dark) !important;
    }}

    .archive-card-header {{
        display: flex;
        align-items: center;
        margin-bottom: 10px;
    }}

    .archive-logo {{
        height: 40px;
        margin-right: 15px;
    }}

    .archive-final-profit {{
        font-size: 1.15rem !important;
        font-weight: 700 !important;
        margin-top: 8px !important;
    }}

    [data-testid="stAppViewContainer"] .archive-profit-positive {{
        color: var(--color-profit) !important;
    }}

    [data-testid="stAppViewContainer"] .archive-profit-negative {{
        color: var(--color-loss) !important;
    }}

    /* --- Settings Card --- */
    .settings-card {{
        background: var(--bg-card);
        border-radius: var(--radius-md);
        padding: 24px;
        margin-bottom: 16px;
        box-shadow: var(--shadow-sm);
        border: 1px solid var(--border-light);
    }}

    .settings-card h3 {{
        color: var(--text-dark) !important;
    }}

    .settings-card label {{
        color: var(--text-body) !important;
    }}

    .settings-card input {{
        background: var(--bg-input) !important;
        border: 1px solid var(--border-light) !important;
        color: var(--text-dark) !important;
        border-radius: var(--radius-sm) !important;
    }}

    /* --- Manage Competition Details --- */
    .manage-comp-details {{
        color: var(--text-body) !important;
    }}

    .manage-comp-details p {{
        color: var(--text-body) !important;
        margin: 5px 0;
    }}

    .manage-comp-details strong {{
        color: var(--text-dark) !important;
    }}

    /* --- Global Button Polish --- */
    [data-testid="stMain"] button {{
        background: var(--bg-card) !important;
        border: 1px solid var(--border-medium) !important;
        color: var(--text-body) !important;
        border-radius: var(--radius-sm) !important;
        font-weight: 600 !important;
        transition: all var(--transition-fast) !important;
    }}

    [data-testid="stMain"] button p,
    [data-testid="stMain"] button span,
    [data-testid="stMain"] button div {{
        color: var(--text-body) !important;
    }}

    [data-testid="stMain"] button:hover {{
        border-color: var(--accent) !important;
        color: var(--accent) !important;
        box-shadow: var(--shadow-sm) !important;
    }}

    [data-testid="stMain"] button:hover p,
    [data-testid="stMain"] button:hover span,
    [data-testid="stMain"] button:hover div {{
        color: var(--accent) !important;
    }}

    /* Primary buttons */
    [data-testid="stMain"] button[kind="primary"],
    [data-testid="stMain"] button[kind="primaryFormSubmit"] {{
        background: var(--accent) !important;
        color: #FFFFFF !important;
        border: none !important;
        font-weight: 700 !important;
        box-shadow: 0 2px 8px rgba(37,99,235,0.25) !important;
    }}

    [data-testid="stMain"] button[kind="primary"] p,
    [data-testid="stMain"] button[kind="primary"] span,
    [data-testid="stMain"] button[kind="primary"] div,
    [data-testid="stMain"] button[kind="primaryFormSubmit"] p,
    [data-testid="stMain"] button[kind="primaryFormSubmit"] span,
    [data-testid="stMain"] button[kind="primaryFormSubmit"] div {{
        color: #FFFFFF !important;
    }}

    [data-testid="stMain"] button[kind="primary"]:hover,
    [data-testid="stMain"] button[kind="primaryFormSubmit"]:hover {{
        background: var(--accent-dark) !important;
        box-shadow: 0 4px 16px rgba(37,99,235,0.3) !important;
        transform: translateY(-1px);
    }}

    /* --- Dropdown / Popover --- */
    [data-baseweb="popover"],
    [data-baseweb="menu"],
    [role="listbox"] {{
        background: var(--bg-card) !important;
        border: 1px solid var(--border-light) !important;
    }}

    [data-baseweb="popover"] li,
    [data-baseweb="menu"] li,
    [role="listbox"] li,
    [role="option"] {{
        color: var(--text-dark) !important;
        background: transparent !important;
    }}

    [data-baseweb="popover"] li:hover,
    [data-baseweb="menu"] li:hover,
    [role="option"]:hover {{
        background: var(--bg-input) !important;
    }}

    [role="option"][aria-selected="true"] {{
        background: var(--accent-light) !important;
        color: var(--accent-dark) !important;
    }}

    /* Main area inputs */
    [data-testid="stMain"] input,
    [data-testid="stMain"] textarea {{
        background: var(--bg-input) !important;
        border: 1px solid var(--border-light) !important;
        color: var(--text-dark) !important;
        border-radius: var(--radius-sm) !important;
    }}

    [data-testid="stMain"] input:focus,
    [data-testid="stMain"] textarea:focus {{
        border-color: var(--accent) !important;
        box-shadow: 0 0 0 3px rgba(37,99,235,0.15) !important;
    }}

    [data-testid="stMain"] [data-baseweb="select"] {{
        background: var(--bg-card) !important;
    }}

    [data-testid="stMain"] [data-baseweb="select"] div {{
        color: var(--text-dark) !important;
        background: transparent !important;
    }}

    [data-testid="stMain"] [data-baseweb="radio"] div {{
        color: var(--text-dark) !important;
    }}

    [data-testid="stMain"] [data-baseweb="input"] {{
        background: var(--bg-input) !important;
    }}

    [data-testid="stMain"] [data-baseweb="input"] div {{
        color: var(--text-dark) !important;
        background: transparent !important;
    }}

    /* --- Scrollbar --- */
    ::-webkit-scrollbar {{
        width: 6px;
        height: 6px;
    }}

    ::-webkit-scrollbar-track {{
        background: transparent;
    }}

    ::-webkit-scrollbar-thumb {{
        background: rgba(0,0,0,0.12);
        border-radius: 3px;
    }}

    ::-webkit-scrollbar-thumb:hover {{
        background: rgba(0,0,0,0.2);
    }}

    /* Alert overrides */
    [data-testid="stAlert"] {{
        border-radius: var(--radius-sm) !important;
    }}

    /* Tabs */
    .stTabs [data-baseweb="tab"] {{
        color: var(--text-muted) !important;
        font-weight: 600 !important;
    }}

    .stTabs [data-baseweb="tab"][aria-selected="true"] {{
        color: var(--accent) !important;
    }}

    /* --- Footer --- */
    .app-footer {{
        text-align: center;
        color: var(--text-muted) !important;
        font-size: 0.75rem;
        padding: 20px;
        letter-spacing: 1px;
    }}

    /* --- Mobile Responsive --- */
    @media (max-width: 768px) {{
        .comp-banner-box {{
            padding: 18px;
            border-radius: var(--radius-md);
        }}

        .comp-banner-box img {{
            height: 44px;
            margin-right: 0;
        }}

        .comp-banner-box .banner-title {{
            font-size: 1.1rem;
            letter-spacing: 4px;
        }}

        .overview-comp-name {{
            display: none !important;
        }}

        .overview-comp-header {{
            justify-content: space-between;
        }}

        .overview-comp-header img {{
            margin-right: 0;
        }}

        .overview-stats-row {{
            flex-wrap: wrap;
        }}

        .overview-stat-item {{
            flex: 1 1 33%;
            padding: 6px 4px;
        }}

        .stat-box {{
            min-width: 90px;
            padding: 14px 10px;
        }}

        .stat-box .stat-value {{
            font-size: 1rem;
        }}

        .match-card {{
            flex-direction: column;
            align-items: flex-start;
            gap: 8px;
            padding: 14px 16px;
        }}

        .match-card .match-profit {{
            align-self: flex-end;
        }}

        .balance-value {{
            font-size: 2rem !important;
        }}

        .next-bet-value {{
            font-size: 1.5rem !important;
        }}

        .stats-container {{
            gap: 8px;
        }}
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
    
    # Use session_state with the selectbox key directly
    # Initialize only if not exists or if current value is invalid
    if 'nav_selection' not in st.session_state:
        st.session_state.nav_selection = "📊 Overview"
    
    # Validate that current selection still exists in options
    if st.session_state.nav_selection not in nav_options:
        st.session_state.nav_selection = "📊 Overview"
    
    # Create selectbox with session state
    track = st.selectbox(
        "Select View", 
        nav_options, 
        index=nav_options.index(st.session_state.nav_selection),
        key="nav_selection",
        label_visibility="collapsed"
    )
    
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
        <div class="comp-banner-box" style="background: linear-gradient(135deg, #1B2A4A 0%, #162240 100%);">
            <div class="banner-title">OVERVIEW</div>
        </div>
    """, unsafe_allow_html=True)
    
    balance_class = "balance-positive" if current_bal >= initial_bankroll else "balance-negative"
    st.markdown(f"""
        <div class="balance-container">
            <p class="balance-label">TOTAL BALANCE</p>
            <h1 class="balance-value {balance_class}">₪{current_bal:,.2f}</h1>
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
                            <div class="overview-stat-value overview-stat-value-staked">₪{stats['total_staked']:,.0f}</div>
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
        <div class="comp-banner-box" style="background: linear-gradient(135deg, #1B2A4A 0%, #162240 100%);">
            <div class="banner-title">➕ NEW COMPETITION</div>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
        <div class="form-card">
            <div class="form-card-title">
                <span style="font-size: 1.5rem;">🏆</span>
                <span class="form-card-title-text">Create New Competition</span>
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
        <div class="comp-banner-box" style="background: linear-gradient(135deg, #1B2A4A 0%, #162240 100%);">
            <div class="banner-title">📁 ARCHIVE</div>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<p class="section-title">📜 Closed Competitions</p>', unsafe_allow_html=True)
    
    if archived_competitions:
        for comp_name, comp_info in archived_competitions.items():
            comp_df = df[df['Comp'] == comp_name]
            comp_profit = comp_df['Profit'].sum() if not comp_df.empty else 0
            stats = competition_stats.get(comp_name, {"total_staked": 0, "total_income": 0, "net_profit": 0})
            
            profit_class = "archive-profit-positive" if comp_profit >= 0 else "archive-profit-negative"
            logo_html = f'<img src="{comp_info["logo"]}" class="archive-logo">' if comp_info["logo"] else ''

            st.markdown(f"""
                <div class="archive-card">
                    <div class="archive-card-header">
                        {logo_html}
                        <h4>{comp_name}</h4>
                    </div>
                    <p>📅 Closed: {comp_info['closed_date'] or 'N/A'}</p>
                    <p>💰 Total Staked: ₪{stats['total_staked']:,.0f}</p>
                    <p>🏆 Total Won: ₪{stats['total_income']:,.0f}</p>
                    <p class="archive-final-profit {profit_class}">📈 Final Profit: ₪{comp_profit:,.0f}</p>
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
        <div class="comp-banner-box" style="background: linear-gradient(135deg, #1B2A4A 0%, #162240 100%);">
            <div class="banner-title">⚙️ MANAGE COMPETITIONS</div>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<p class="section-title">🏆 Active Competitions</p>', unsafe_allow_html=True)
    
    for comp_name, comp_info in active_competitions.items():
        with st.expander(f"⚽ {comp_name}", expanded=False):
            st.markdown(f"""
                <div class="manage-comp-details">
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
            <div class="banner-title">{comp_name.upper()}</div>
        </div>
    """, unsafe_allow_html=True)
    
    # Current Balance
    balance_class = "balance-positive" if current_bal >= initial_bankroll else "balance-negative"
    st.markdown(f"""
        <div class="balance-container">
            <p class="balance-label">CURRENT BALANCE</p>
            <h1 class="balance-value {balance_class}">₪{current_bal:,.2f}</h1>
        </div>
    """, unsafe_allow_html=True)
    
    # Filter data for this competition
    comp_df = df[df['Comp'] == comp_name].copy() if not df.empty else pd.DataFrame()
    stats = competition_stats.get(comp_name, {"total_staked": 0, "total_income": 0, "net_profit": 0})
    
    # Statistics Boxes
    profit_val_class = "stat-value-profit-pos" if stats['net_profit'] >= 0 else "stat-value-profit-neg"
    profit_box_class = "stat-box-profit-up" if stats['net_profit'] >= 0 else "stat-box-profit-down"
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
            <div class="stat-box {profit_box_class}">
                <div class="stat-label">📈 Net Profit</div>
                <div class="stat-value {profit_val_class}">₪{stats['net_profit']:,.0f}</div>
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
                <span class="form-card-title-text">Add New Match</span>
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
                        try:
                            ws.append_row(new_row)
                            connect_to_sheets.clear()
                            st.success(f"✅ Added: {home_team} vs {away_team}")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error saving to sheet: {str(e)}")
                    else:
                        st.error("❌ Could not connect to worksheet!")
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
    <div class="app-footer">
        Elite Football Tracker v3.0 | Built with Streamlit
    </div>
""", unsafe_allow_html=True)
