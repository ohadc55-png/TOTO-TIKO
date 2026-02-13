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
       ELITE FOOTBALL TRACKER - Premium Dark Financial Dashboard
       ============================================================ */

    /* --- 1. Font Import --- */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

    /* --- 2. Global Styles & CSS Custom Properties --- */
    :root {{
        --bg-surface: rgba(16, 16, 10, 0.82);
        --bg-card: rgba(22, 22, 14, 0.88);
        --bg-card-hover: rgba(28, 28, 18, 0.92);
        --bg-input: rgba(12, 12, 8, 0.7);
        --border-subtle: rgba(255, 255, 255, 0.08);
        --border-medium: rgba(255, 255, 255, 0.12);
        --border-strong: rgba(255, 255, 255, 0.18);
        --text-primary: #FFFFFF;
        --text-secondary: rgba(255, 255, 255, 0.75);
        --text-tertiary: rgba(255, 255, 255, 0.52);
        --text-muted: rgba(255, 255, 255, 0.38);
        --accent-primary: #F5A623;
        --accent-primary-glow: rgba(245, 166, 35, 0.25);
        --color-profit: #34D399;
        --color-profit-glow: rgba(52, 211, 153, 0.3);
        --color-loss: #F87171;
        --color-loss-glow: rgba(248, 113, 113, 0.2);
        --color-pending: #FBBF24;
        --color-pending-glow: rgba(251, 191, 36, 0.25);
        --radius-sm: 8px;
        --radius-md: 14px;
        --radius-lg: 18px;
        --blur-card: blur(20px);
        --shadow-card: 0 2px 12px rgba(0, 0, 0, 0.25), 0 0 1px rgba(255, 255, 255, 0.05);
        --shadow-card-hover: 0 4px 20px rgba(0, 0, 0, 0.35), 0 0 1px rgba(255, 255, 255, 0.08);
        --transition-fast: 0.18s ease;
        --transition-med: 0.3s ease;
    }}

    * {{
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
    }}

    /* --- 3. Main Background --- */
    [data-testid="stAppViewContainer"] {{
        background-image:
            linear-gradient(
                175deg,
                rgba(8, 8, 4, 0.88) 0%,
                rgba(12, 12, 6, 0.90) 30%,
                rgba(10, 10, 5, 0.93) 70%,
                rgba(6, 6, 3, 0.96) 100%
            ),
            url("{BG_IMAGE_URL}");
        background-attachment: fixed;
        background-size: cover;
        background-position: center;
    }}

    /* --- 4. Text Color Overrides for Main Area --- */
    [data-testid="stAppViewContainer"] [data-testid="stMain"] h1,
    [data-testid="stAppViewContainer"] [data-testid="stMain"] h2,
    [data-testid="stAppViewContainer"] [data-testid="stMain"] h3,
    [data-testid="stAppViewContainer"] [data-testid="stMain"] h4 {{
        color: var(--text-primary) !important;
        font-weight: 700;
    }}

    [data-testid="stAppViewContainer"] [data-testid="stMain"] p,
    [data-testid="stAppViewContainer"] [data-testid="stMain"] span,
    [data-testid="stAppViewContainer"] [data-testid="stMain"] label,
    [data-testid="stAppViewContainer"] [data-testid="stMain"] li,
    [data-testid="stAppViewContainer"] [data-testid="stMain"] div {{
        color: var(--text-secondary) !important;
    }}

    [data-testid="stAppViewContainer"] [data-testid="stMain"] strong {{
        color: var(--text-primary) !important;
    }}

    /* Streamlit markdown containers */
    [data-testid="stMarkdownContainer"] p {{
        color: var(--text-secondary) !important;
        line-height: 1.6;
    }}

    /* Streamlit metric overrides */
    [data-testid="stMetricValue"] {{
        color: var(--text-primary) !important;
        font-weight: 800 !important;
        font-variant-numeric: tabular-nums;
    }}

    [data-testid="stMetricLabel"] {{
        color: var(--text-tertiary) !important;
        font-size: 0.72rem !important;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        font-weight: 600 !important;
    }}

    /* --- 5. Sidebar Styles --- */
    [data-testid="stSidebar"] {{
        background: linear-gradient(
            180deg,
            rgba(10, 10, 6, 0.98) 0%,
            rgba(14, 14, 8, 0.98) 50%,
            rgba(10, 10, 6, 0.98) 100%
        ) !important;
        border-right: 1px solid var(--border-subtle) !important;
    }}

    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {{
        color: var(--text-primary) !important;
        font-weight: 700 !important;
        font-size: 0.95rem !important;
        letter-spacing: 0.5px;
    }}

    [data-testid="stSidebar"] h4 {{
        color: var(--text-secondary) !important;
        font-weight: 600 !important;
    }}

    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] .stMarkdown {{
        color: var(--text-secondary) !important;
    }}

    [data-testid="stSidebar"] [data-testid="stMetricValue"] {{
        color: var(--text-primary) !important;
        font-size: 1.4rem !important;
        font-weight: 800 !important;
    }}

    [data-testid="stSidebar"] [data-testid="stMetricLabel"] {{
        color: var(--text-muted) !important;
    }}

    /* Sidebar divider */
    [data-testid="stSidebar"] hr {{
        border-color: var(--border-subtle) !important;
        margin: 16px 0 !important;
    }}

    /* Sidebar buttons */
    [data-testid="stSidebar"] button {{
        background: var(--bg-card) !important;
        border: 1px solid var(--border-medium) !important;
        color: var(--text-secondary) !important;
        border-radius: var(--radius-sm) !important;
        font-weight: 600 !important;
        font-size: 0.82rem !important;
        transition: all var(--transition-fast) !important;
    }}

    [data-testid="stSidebar"] button:hover {{
        background: var(--bg-card-hover) !important;
        border-color: var(--accent-primary) !important;
        color: var(--accent-primary) !important;
    }}

    /* Sidebar selectbox */
    [data-testid="stSidebar"] [data-baseweb="select"] {{
        background: var(--bg-card) !important;
    }}

    [data-testid="stSidebar"] [data-baseweb="select"] div {{
        color: var(--text-primary) !important;
        background: transparent !important;
    }}

    /* Sidebar number input */
    [data-testid="stSidebar"] input {{
        background: var(--bg-input) !important;
        border: 1px solid var(--border-medium) !important;
        color: var(--text-primary) !important;
        border-radius: var(--radius-sm) !important;
    }}

    [data-testid="stSidebar"] input:focus {{
        border-color: var(--accent-primary) !important;
        box-shadow: 0 0 0 2px var(--accent-primary-glow) !important;
    }}

    /* --- 6. Form Styles --- */
    [data-testid="stForm"] {{
        background: var(--bg-card) !important;
        backdrop-filter: var(--blur-card);
        border: 1px solid var(--border-medium) !important;
        border-radius: var(--radius-md) !important;
        padding: 8px !important;
    }}

    [data-testid="stForm"] label {{
        color: var(--text-secondary) !important;
        font-weight: 600 !important;
        font-size: 0.78rem !important;
        text-transform: uppercase;
        letter-spacing: 1.2px;
    }}

    [data-testid="stForm"] input,
    [data-testid="stForm"] textarea {{
        background: var(--bg-input) !important;
        border: 1px solid var(--border-medium) !important;
        color: var(--text-primary) !important;
        border-radius: var(--radius-sm) !important;
        font-weight: 500 !important;
        transition: border-color var(--transition-fast), box-shadow var(--transition-fast);
    }}

    [data-testid="stForm"] input:focus,
    [data-testid="stForm"] textarea:focus {{
        border-color: var(--accent-primary) !important;
        box-shadow: 0 0 0 3px var(--accent-primary-glow) !important;
        outline: none !important;
    }}

    [data-testid="stForm"] input::placeholder,
    [data-testid="stForm"] textarea::placeholder {{
        color: var(--text-muted) !important;
    }}

    /* Radio buttons in form */
    [data-testid="stForm"] [data-testid="stMarkdownContainer"] {{
        color: var(--text-primary) !important;
    }}

    [data-testid="stForm"] [data-baseweb="radio"],
    [data-testid="stForm"] [data-baseweb="radio"] div {{
        color: var(--text-primary) !important;
    }}

    [data-testid="stForm"] .stRadio label,
    [data-testid="stForm"] .stRadio p {{
        color: var(--text-primary) !important;
        font-weight: 500 !important;
    }}

    /* Submit button */
    [data-testid="stForm"] button[kind="primaryFormSubmit"],
    [data-testid="stForm"] button[type="submit"] {{
        background: linear-gradient(135deg, var(--accent-primary) 0%, #E8941E 100%) !important;
        color: #0a0a05 !important;
        font-weight: 700 !important;
        border: none !important;
        border-radius: var(--radius-sm) !important;
        letter-spacing: 0.5px;
        transition: all var(--transition-fast) !important;
        box-shadow: 0 2px 10px var(--accent-primary-glow) !important;
    }}

    [data-testid="stForm"] button[kind="primaryFormSubmit"]:hover,
    [data-testid="stForm"] button[type="submit"]:hover {{
        box-shadow: 0 4px 20px var(--accent-primary-glow) !important;
        transform: translateY(-1px);
    }}

    /* Color picker in forms */
    [data-testid="stForm"] [data-testid="stColorPicker"] label {{
        color: var(--text-secondary) !important;
    }}

    /* Number input within form */
    [data-testid="stForm"] [data-baseweb="input"] {{
        background: var(--bg-input) !important;
    }}

    /* Select / dropdown in form */
    [data-testid="stForm"] [data-baseweb="select"] div {{
        color: var(--text-primary) !important;
    }}

    /* --- 7. Form Card Styles --- */
    .form-card {{
        background: var(--bg-card);
        backdrop-filter: var(--blur-card);
        border-radius: var(--radius-md);
        padding: 24px 28px;
        margin: 24px 0 8px 0;
        box-shadow: var(--shadow-card);
        border: 1px solid var(--border-medium);
    }}

    .form-card-title {{
        color: var(--text-primary) !important;
        font-size: 1.05rem;
        font-weight: 700;
        margin-bottom: 0;
        display: flex;
        align-items: center;
        gap: 12px;
        letter-spacing: 0.3px;
    }}

    /* --- 8. Match Card Styles --- */
    .match-card {{
        border-radius: var(--radius-md);
        padding: 18px 22px;
        margin-bottom: 10px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        background: var(--bg-card);
        backdrop-filter: var(--blur-card);
        border: 1px solid var(--border-subtle);
        box-shadow: var(--shadow-card);
        transition: all var(--transition-fast);
    }}

    .match-card:hover {{
        background: var(--bg-card-hover);
        border-color: var(--border-medium);
        box-shadow: var(--shadow-card-hover);
        transform: translateY(-1px);
    }}

    .match-card-won {{
        background: var(--bg-card);
        border: 1px solid var(--border-subtle);
        border-left: 4px solid var(--color-profit);
    }}

    .match-card-won:hover {{
        border-left-color: var(--color-profit);
    }}

    .match-card-lost {{
        background: var(--bg-card);
        border: 1px solid var(--border-subtle);
        border-left: 4px solid var(--color-loss);
    }}

    .match-card-lost:hover {{
        border-left-color: var(--color-loss);
    }}

    .match-card-pending {{
        background: var(--bg-card);
        border: 1px solid var(--border-subtle);
        border-left: 4px solid var(--color-pending);
    }}

    .match-card-pending:hover {{
        border-left-color: var(--color-pending);
    }}

    .match-card .match-info {{
        flex: 1;
    }}

    .match-card .match-name {{
        font-size: 0.98rem;
        font-weight: 700;
        color: var(--text-primary) !important;
        margin-bottom: 6px;
        letter-spacing: 0.2px;
    }}

    .match-card .match-details {{
        font-size: 0.78rem;
        color: var(--text-tertiary) !important;
        font-weight: 500;
        letter-spacing: 0.2px;
    }}

    .match-card .match-details strong {{
        color: var(--text-secondary) !important;
    }}

    .match-card .match-profit {{
        font-size: 1.15rem;
        font-weight: 800;
        font-variant-numeric: tabular-nums;
    }}

    /* --- 9. Match Profit Color Classes --- */
    [data-testid="stAppViewContainer"] .match-profit-positive {{
        color: var(--color-profit) !important;
        text-shadow: 0 0 12px var(--color-profit-glow);
    }}

    [data-testid="stAppViewContainer"] .match-profit-negative {{
        color: var(--color-loss) !important;
    }}

    [data-testid="stAppViewContainer"] .match-profit-neutral {{
        color: var(--color-pending) !important;
        text-shadow: 0 0 10px var(--color-pending-glow);
    }}

    /* --- 10. Competition Banner Styles --- */
    .comp-banner-box {{
        border-radius: var(--radius-lg);
        padding: 28px 36px;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-bottom: 32px;
        box-shadow: 0 4px 24px rgba(0, 0, 0, 0.3);
        border: 1px solid var(--border-subtle);
        backdrop-filter: var(--blur-card);
        position: relative;
        overflow: hidden;
    }}

    .comp-banner-box::before {{
        content: '';
        position: absolute;
        inset: 0;
        background: linear-gradient(135deg, rgba(8, 8, 4, 0.55) 0%, rgba(12, 12, 6, 0.65) 100%);
        z-index: 0;
        pointer-events: none;
    }}

    .comp-banner-box > * {{
        position: relative;
        z-index: 1;
    }}

    .comp-banner-box img {{
        height: 72px;
        margin-right: 28px;
        filter: drop-shadow(2px 2px 6px rgba(0, 0, 0, 0.4));
        transition: transform var(--transition-med);
    }}

    .comp-banner-box:hover img {{
        transform: scale(1.04);
    }}

    .comp-banner-box h1 {{
        margin: 0;
        font-weight: 800;
        font-size: 1.5rem;
        letter-spacing: 5px;
        text-transform: uppercase;
    }}

    /* --- 11. Banner Text Styles --- */
    .comp-banner-text {{
        margin: 0;
        font-weight: 800;
        font-size: 1.5rem;
        letter-spacing: 5px;
        text-transform: uppercase;
        text-shadow: 0 2px 8px rgba(0, 0, 0, 0.4);
    }}

    .overview-banner-text {{
        margin: 0;
        font-weight: 800;
        font-size: 1.6rem;
        letter-spacing: 6px;
        text-transform: uppercase;
        color: var(--text-primary);
        text-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
    }}

    /* --- 12. First Mobile Responsive Block --- */
    @media (max-width: 768px) {{
        .comp-banner-box {{
            padding: 18px;
            border-radius: var(--radius-md);
        }}

        .comp-banner-box img {{
            height: 48px;
            margin-right: 0;
        }}

        .comp-banner-box .comp-banner-text {{
            display: none !important;
        }}

        .comp-banner-box .overview-banner-text {{
            display: block !important;
            font-size: 1.1rem;
            letter-spacing: 4px;
        }}

        .overview-comp-header h3 {{
            font-size: 0.95rem;
        }}

        .overview-comp-header img {{
            height: 40px;
            margin-right: 10px;
        }}

        .overview-comp-profit {{
            font-size: 1.15rem;
        }}

        .overview-stats-row {{
            flex-wrap: wrap;
        }}

        .overview-stat-item {{
            flex: 1 1 33%;
            padding: 8px 4px;
        }}

        .stat-box {{
            min-width: 95px;
            padding: 14px 10px;
        }}

        .stat-box .stat-value {{
            font-size: 1rem;
        }}

        .match-card {{
            flex-direction: column;
            align-items: flex-start;
            gap: 10px;
            padding: 16px 18px;
        }}

        .match-card .match-profit {{
            align-self: flex-end;
        }}

        .balance-value {{
            font-size: 2rem !important;
        }}

        .next-bet-value {{
            font-size: 1.6rem !important;
        }}

        .stats-container {{
            gap: 10px;
        }}
    }}

    /* --- 13. Stats Container + Stat Boxes --- */
    .stats-container {{
        display: flex;
        gap: 16px;
        margin: 28px 0;
        flex-wrap: wrap;
    }}

    .stat-box {{
        flex: 1;
        min-width: 150px;
        border-radius: var(--radius-md);
        padding: 20px 22px;
        text-align: center;
        background: var(--bg-card);
        backdrop-filter: var(--blur-card);
        border: 1px solid var(--border-medium);
        box-shadow: var(--shadow-card);
        transition: all var(--transition-fast);
    }}

    .stat-box:hover {{
        border-color: var(--border-strong);
        box-shadow: var(--shadow-card-hover);
    }}

    .stat-box-total {{
        background: var(--bg-card);
        border: 1px solid var(--border-medium);
    }}

    .stat-box-income {{
        background: var(--bg-card);
        border: 1px solid var(--border-medium);
    }}

    .stat-box-profit {{
        background: var(--bg-card);
        border: 1px solid var(--border-medium);
    }}

    .stat-box .stat-label {{
        font-size: 0.68rem;
        color: var(--text-muted) !important;
        text-transform: uppercase;
        letter-spacing: 2.5px;
        margin-bottom: 10px;
        font-weight: 700;
    }}

    .stat-box .stat-value {{
        font-size: 1.35rem;
        font-weight: 800;
        color: var(--text-primary) !important;
        font-variant-numeric: tabular-nums;
    }}

    /* Staked = muted green (money out, not glowing) */
    [data-testid="stAppViewContainer"] [data-testid="stMain"] .stat-box-total .stat-value {{
        color: #6BCB77 !important;
    }}

    /* Won = bright glowing green */
    [data-testid="stAppViewContainer"] [data-testid="stMain"] .stat-box-income .stat-value {{
        color: var(--color-profit) !important;
        text-shadow: 0 0 14px var(--color-profit-glow);
    }}

    /* Net Profit - dynamic: green glow or red */
    [data-testid="stAppViewContainer"] [data-testid="stMain"] .stat-value-profit-pos {{
        color: var(--color-profit) !important;
        text-shadow: 0 0 18px var(--color-profit-glow);
    }}

    [data-testid="stAppViewContainer"] [data-testid="stMain"] .stat-value-profit-neg {{
        color: var(--color-loss) !important;
    }}

    /* --- 14. Overview Competition Cards --- */
    .overview-comp-card {{
        border-radius: var(--radius-md);
        padding: 22px 26px;
        margin-bottom: 18px;
        box-shadow: var(--shadow-card);
        border: 1px solid var(--border-medium);
        backdrop-filter: var(--blur-card);
        position: relative;
        overflow: hidden;
        transition: all var(--transition-fast);
    }}

    .overview-comp-card:hover {{
        box-shadow: var(--shadow-card-hover);
        border-color: var(--border-strong);
        transform: translateY(-2px);
    }}

    .overview-comp-card::before {{
        content: '';
        position: absolute;
        inset: 0;
        background: linear-gradient(135deg, rgba(8, 8, 4, 0.62) 0%, rgba(14, 14, 8, 0.72) 100%);
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
        margin-bottom: 18px;
        padding-bottom: 16px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    }}

    .overview-comp-header img {{
        height: 58px;
        margin-right: 20px;
        filter: drop-shadow(2px 2px 5px rgba(0, 0, 0, 0.4));
    }}

    .overview-comp-header h3 {{
        margin: 0;
        font-weight: 700;
        font-size: 1.15rem;
        letter-spacing: 1px;
        color: var(--text-primary) !important;
    }}

    /* --- 15. Overview Stats Row --- */
    .overview-comp-profit {{
        font-size: 1.5rem;
        font-weight: 800;
        text-align: right;
        font-variant-numeric: tabular-nums;
    }}

    [data-testid="stAppViewContainer"] .overview-profit-positive {{
        color: var(--color-profit) !important;
        text-shadow: 0 0 16px var(--color-profit-glow);
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
        padding: 10px 20px;
    }}

    .overview-stat-label {{
        font-size: 0.68rem;
        color: var(--text-muted) !important;
        margin-bottom: 6px;
        text-transform: uppercase;
        letter-spacing: 2.5px;
        font-weight: 700;
    }}

    .overview-stat-value {{
        font-size: 1.1rem;
        font-weight: 800;
        color: var(--text-primary) !important;
        font-variant-numeric: tabular-nums;
    }}

    [data-testid="stAppViewContainer"] [data-testid="stMain"] .overview-stat-value-staked {{
        color: #6BCB77 !important;
    }}

    [data-testid="stAppViewContainer"] [data-testid="stMain"] .overview-stat-value-green {{
        color: var(--color-profit) !important;
        text-shadow: 0 0 12px var(--color-profit-glow);
    }}

    /* --- 16. Next Bet Display --- */
    .next-bet-display {{
        text-align: center;
        margin: 28px 0;
        padding: 24px;
        background: var(--bg-card);
        backdrop-filter: var(--blur-card);
        border-radius: var(--radius-md);
        border: 1px solid var(--border-medium);
        box-shadow: var(--shadow-card);
        position: relative;
    }}

    .next-bet-display::after {{
        content: '';
        position: absolute;
        bottom: 0;
        left: 20%;
        right: 20%;
        height: 2px;
        background: linear-gradient(90deg, transparent, var(--accent-primary), transparent);
        border-radius: 1px;
        opacity: 0.6;
    }}

    .next-bet-label {{
        font-size: 0.68rem;
        color: var(--text-muted) !important;
        margin-bottom: 8px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 2.5px;
    }}

    .next-bet-value {{
        font-size: 2.2rem;
        font-weight: 900;
        color: var(--accent-primary) !important;
        text-shadow: 0 0 24px var(--accent-primary-glow);
        font-variant-numeric: tabular-nums;
    }}

    /* --- 17. Section Titles --- */
    .section-title {{
        color: var(--text-muted) !important;
        font-size: 0.7rem;
        font-weight: 700;
        margin: 30px 0 16px 0;
        text-transform: uppercase;
        letter-spacing: 3.5px;
        display: flex;
        align-items: center;
        gap: 10px;
    }}

    .section-title::after {{
        content: '';
        flex: 1;
        height: 1px;
        background: linear-gradient(90deg, var(--border-subtle), transparent);
    }}

    /* --- 18. Balance Display --- */
    .balance-container {{
        text-align: center;
        margin: 28px 0;
        padding: 24px;
    }}

    .balance-label {{
        color: var(--text-muted) !important;
        font-size: 0.72rem;
        margin-bottom: 8px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 3px;
    }}

    .balance-value {{
        font-size: 3rem;
        font-weight: 900;
        font-variant-numeric: tabular-nums;
        line-height: 1.1;
    }}

    [data-testid="stAppViewContainer"] .balance-positive {{
        color: var(--color-profit) !important;
        text-shadow: 0 0 20px var(--color-profit-glow);
    }}

    [data-testid="stAppViewContainer"] .balance-negative {{
        color: var(--color-loss) !important;
    }}

    /* --- 19. Info Messages --- */
    .info-message {{
        background: var(--bg-card);
        backdrop-filter: var(--blur-card);
        border-radius: var(--radius-md);
        padding: 28px;
        text-align: center;
        color: var(--text-secondary) !important;
        border: 1px solid var(--border-medium);
        box-shadow: var(--shadow-card);
        font-weight: 500;
    }}

    /* --- 20. Football Loading Animation (KEPT EXACTLY AS-IS) --- */
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

    /* --- 21. Loading Text + Pulse Animation (KEPT EXACTLY AS-IS) --- */
    .loading-text {{
        color: rgba(255,255,255,0.6);
        font-size: 1rem;
        font-weight: 500;
        animation: pulse 1.5s ease-in-out infinite;
    }}

    @keyframes pulse {{
        0%, 100% {{ opacity: 0.6; }}
        50% {{ opacity: 1; }}
    }}

    /* --- 22. Spinner Override (KEPT EXACTLY AS-IS) --- */
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

    /* --- 23. Overview Comp Name + Second Mobile Block --- */
    .overview-comp-name {{
        margin: 0;
        font-weight: 700;
        font-size: 1.15rem;
        letter-spacing: 1px;
        color: var(--text-primary) !important;
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

    /* --- 24. Expander Styles --- */
    [data-testid="stExpander"] {{
        background: var(--bg-card) !important;
        border: 1px solid var(--border-medium) !important;
        border-radius: var(--radius-md) !important;
        margin-bottom: 12px !important;
        box-shadow: var(--shadow-card) !important;
        overflow: hidden !important;
    }}

    [data-testid="stExpander"] summary {{
        color: var(--text-primary) !important;
        font-weight: 700 !important;
        padding: 14px 18px !important;
        transition: color var(--transition-fast) !important;
    }}

    [data-testid="stExpander"] summary:hover {{
        color: var(--accent-primary) !important;
    }}

    [data-testid="stExpander"] summary span {{
        color: inherit !important;
    }}

    [data-testid="stExpander"] [data-testid="stMarkdownContainer"] p {{
        color: var(--text-secondary) !important;
    }}

    [data-testid="stExpander"] [data-testid="stMarkdownContainer"] strong {{
        color: var(--text-primary) !important;
    }}

    [data-testid="stExpander"] label {{
        color: var(--text-secondary) !important;
    }}

    [data-testid="stExpander"] input {{
        background: var(--bg-input) !important;
        border: 1px solid var(--border-medium) !important;
        color: var(--text-primary) !important;
        border-radius: var(--radius-sm) !important;
    }}

    [data-testid="stExpander"] button {{
        background: var(--bg-card) !important;
        border: 1px solid var(--border-medium) !important;
        color: var(--text-secondary) !important;
        border-radius: var(--radius-sm) !important;
        font-weight: 600 !important;
        transition: all var(--transition-fast) !important;
    }}

    [data-testid="stExpander"] button:hover {{
        border-color: var(--accent-primary) !important;
        color: var(--accent-primary) !important;
    }}

    /* --- 25. Archive Card Styles --- */
    .archive-card {{
        background: var(--bg-card);
        backdrop-filter: var(--blur-card);
        border: 1px solid var(--border-medium);
        border-radius: var(--radius-md);
        padding: 22px 26px;
        margin-bottom: 14px;
        box-shadow: var(--shadow-card);
        transition: all var(--transition-fast);
    }}

    .archive-card:hover {{
        border-color: var(--border-strong);
        box-shadow: var(--shadow-card-hover);
    }}

    .archive-card h4 {{
        color: var(--text-primary) !important;
        margin: 0 0 12px 0;
        font-weight: 700;
    }}

    .archive-card p {{
        color: var(--text-secondary) !important;
        margin: 6px 0;
        font-weight: 500;
    }}

    .archive-card strong {{
        color: var(--text-primary) !important;
    }}

    .archive-card-header {{
        display: flex;
        align-items: center;
        margin-bottom: 10px;
    }}

    .archive-logo {{
        height: 40px;
        margin-right: 15px;
        filter: drop-shadow(1px 1px 4px rgba(0, 0, 0, 0.3));
    }}

    .archive-final-profit {{
        font-size: 1.2rem !important;
        font-weight: 700 !important;
        margin-top: 10px !important;
    }}

    [data-testid="stAppViewContainer"] .archive-profit-positive {{
        color: var(--color-profit) !important;
    }}

    [data-testid="stAppViewContainer"] .archive-profit-negative {{
        color: var(--color-loss) !important;
    }}

    /* --- 26. Settings Card Styles --- */
    .settings-card {{
        background: var(--bg-card);
        backdrop-filter: var(--blur-card);
        border-radius: var(--radius-md);
        padding: 28px;
        margin-bottom: 20px;
        box-shadow: var(--shadow-card);
        border: 1px solid var(--border-medium);
    }}

    .settings-card h3 {{
        color: var(--text-primary) !important;
        margin-bottom: 20px;
        font-weight: 700;
    }}

    .settings-card label {{
        color: var(--text-secondary) !important;
        font-weight: 600;
    }}

    .settings-card input {{
        background: var(--bg-input) !important;
        border: 1px solid var(--border-medium) !important;
        color: var(--text-primary) !important;
        border-radius: var(--radius-sm) !important;
    }}

    /* --- Global Button Polish --- */
    [data-testid="stMain"] button {{
        background: var(--bg-card) !important;
        border: 1px solid var(--border-medium) !important;
        color: var(--text-primary) !important;
        border-radius: var(--radius-sm) !important;
        font-weight: 600 !important;
        transition: all var(--transition-fast) !important;
        letter-spacing: 0.3px;
    }}

    [data-testid="stMain"] button p,
    [data-testid="stMain"] button span,
    [data-testid="stMain"] button div {{
        color: var(--text-primary) !important;
    }}

    [data-testid="stMain"] button:hover {{
        background: var(--bg-card-hover) !important;
        border-color: var(--accent-primary) !important;
        color: var(--accent-primary) !important;
        transform: translateY(-1px);
    }}

    [data-testid="stMain"] button:hover p,
    [data-testid="stMain"] button:hover span,
    [data-testid="stMain"] button:hover div {{
        color: var(--accent-primary) !important;
    }}

    /* Primary action buttons in main area */
    [data-testid="stMain"] button[kind="primary"],
    [data-testid="stMain"] button[kind="primaryFormSubmit"] {{
        background: linear-gradient(135deg, var(--accent-primary) 0%, #E8941E 100%) !important;
        color: #0a0a05 !important;
        border: none !important;
        font-weight: 700 !important;
        box-shadow: 0 2px 10px var(--accent-primary-glow) !important;
    }}

    [data-testid="stMain"] button[kind="primary"] p,
    [data-testid="stMain"] button[kind="primary"] span,
    [data-testid="stMain"] button[kind="primary"] div,
    [data-testid="stMain"] button[kind="primaryFormSubmit"] p,
    [data-testid="stMain"] button[kind="primaryFormSubmit"] span,
    [data-testid="stMain"] button[kind="primaryFormSubmit"] div {{
        color: #0a0a05 !important;
    }}

    [data-testid="stMain"] button[kind="primary"]:hover,
    [data-testid="stMain"] button[kind="primaryFormSubmit"]:hover {{
        box-shadow: 0 4px 20px var(--accent-primary-glow) !important;
        transform: translateY(-1px);
    }}

    [data-testid="stMain"] button[kind="primary"]:hover p,
    [data-testid="stMain"] button[kind="primary"]:hover span,
    [data-testid="stMain"] button[kind="primary"]:hover div,
    [data-testid="stMain"] button[kind="primaryFormSubmit"]:hover p,
    [data-testid="stMain"] button[kind="primaryFormSubmit"]:hover span,
    [data-testid="stMain"] button[kind="primaryFormSubmit"]:hover div {{
        color: #0a0a05 !important;
    }}

    /* --- Dropdown / Popover / Listbox (light background panels) --- */
    [data-baseweb="popover"],
    [data-baseweb="menu"],
    [role="listbox"] {{
        background: var(--bg-card) !important;
        border: 1px solid var(--border-medium) !important;
    }}

    [data-baseweb="popover"] li,
    [data-baseweb="menu"] li,
    [role="listbox"] li,
    [role="option"] {{
        color: var(--text-primary) !important;
        background: transparent !important;
    }}

    [data-baseweb="popover"] li:hover,
    [data-baseweb="menu"] li:hover,
    [role="option"]:hover {{
        background: var(--bg-card-hover) !important;
    }}

    [role="option"][aria-selected="true"] {{
        background: rgba(245, 166, 35, 0.15) !important;
        color: var(--accent-primary) !important;
    }}

    /* Main area inputs (outside forms too) */
    [data-testid="stMain"] input,
    [data-testid="stMain"] textarea {{
        background: var(--bg-input) !important;
        border: 1px solid var(--border-medium) !important;
        color: var(--text-primary) !important;
        border-radius: var(--radius-sm) !important;
    }}

    [data-testid="stMain"] input:focus,
    [data-testid="stMain"] textarea:focus {{
        border-color: var(--accent-primary) !important;
        box-shadow: 0 0 0 3px var(--accent-primary-glow) !important;
    }}

    /* Main area select/dropdown */
    [data-testid="stMain"] [data-baseweb="select"] {{
        background: var(--bg-card) !important;
    }}

    [data-testid="stMain"] [data-baseweb="select"] div {{
        color: var(--text-primary) !important;
        background: transparent !important;
    }}

    /* Radio buttons in main area */
    [data-testid="stMain"] [data-baseweb="radio"] div {{
        color: var(--text-primary) !important;
    }}

    /* Number input steppers */
    [data-testid="stMain"] [data-baseweb="input"] {{
        background: var(--bg-input) !important;
    }}

    [data-testid="stMain"] [data-baseweb="input"] div {{
        color: var(--text-primary) !important;
        background: transparent !important;
    }}

    /* Scrollbar styling */
    ::-webkit-scrollbar {{
        width: 6px;
        height: 6px;
    }}

    ::-webkit-scrollbar-track {{
        background: transparent;
    }}

    ::-webkit-scrollbar-thumb {{
        background: rgba(255, 255, 255, 0.12);
        border-radius: 3px;
    }}

    ::-webkit-scrollbar-thumb:hover {{
        background: rgba(255, 255, 255, 0.2);
    }}

    /* Success / Error / Warning message overrides */
    [data-testid="stAlert"] {{
        border-radius: var(--radius-sm) !important;
        font-weight: 500;
    }}

    /* Streamlit header/toolbar transparency */
    header[data-testid="stHeader"] {{
        background: transparent !important;
    }}

    /* Tab styling if used */
    .stTabs [data-baseweb="tab"] {{
        color: var(--text-tertiary) !important;
        font-weight: 600 !important;
    }}

    .stTabs [data-baseweb="tab"][aria-selected="true"] {{
        color: var(--accent-primary) !important;
    }}

    /* --- Manage Competition Details --- */
    .manage-comp-details {{
        color: var(--text-secondary) !important;
    }}

    .manage-comp-details p {{
        color: var(--text-secondary) !important;
        margin: 6px 0;
    }}

    .manage-comp-details strong {{
        color: var(--text-primary) !important;
    }}

    /* --- App Footer --- */
    .app-footer {{
        text-align: center;
        color: var(--text-muted) !important;
        font-size: 0.75rem;
        padding: 20px;
        letter-spacing: 1px;
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
        <div class="comp-banner-box" style="background: linear-gradient(135deg, rgba(10,10,5,0.85) 0%, rgba(20,20,10,0.85) 100%);">
            <h1 class="overview-banner-text">OVERVIEW</h1>
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
        <div class="comp-banner-box" style="background: linear-gradient(135deg, rgba(10,10,5,0.85) 0%, rgba(20,20,10,0.85) 100%);">
            <h1 class="overview-banner-text">➕ NEW COMPETITION</h1>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
        <div class="form-card">
            <div class="form-card-title">
                <span style="font-size: 1.5rem;">🏆</span>
                <span style="color: white !important;">Create New Competition</span>
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
        <div class="comp-banner-box" style="background: linear-gradient(135deg, rgba(10,10,5,0.85) 0%, rgba(20,20,10,0.85) 100%);">
            <h1 class="overview-banner-text">📁 ARCHIVE</h1>
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
        <div class="comp-banner-box" style="background: linear-gradient(135deg, rgba(10,10,5,0.85) 0%, rgba(20,20,10,0.85) 100%);">
            <h1 class="overview-banner-text">⚙️ MANAGE COMPETITIONS</h1>
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
            <h1 class="comp-banner-text" style="color: {comp_info['text_color']};">{comp_name.upper()}</h1>
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
                <span style="color: white !important;">Add New Match</span>
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
