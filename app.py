import streamlit as st
import pandas as pd
import plotly.express as px
import gspread
import datetime
from typing import Tuple, List, Dict, Optional

# ============================================================================
# 1. CONFIGURATION & CONSTANTS
# ============================================================================

APP_LOGO = "https://i.postimg.cc/8Cr6SypK/yzwb-ll-sm.png"
BG_IMAGE = "https://i.postimg.cc/GmFZ4KS7/Gemini-Generated-Image-k1h11zk1h11zk1h1.png"
SIDEBAR_BG = "https://i.postimg.cc/NfdK3hck/'yzwb-ll'-sm-(1).png"
ARROW_OPEN_URL = "https://i.postimg.cc/vHQy61dy/Gemini-Generated-Image-dl91ekdl91ekdl91.png"
ARROW_CLOSE_URL = "https://i.postimg.cc/hvVG4Nxz/Gemini-Generated-Image-2tueuy2tueuy2tue.png"

# Google Sheets Constants
BANKROLL_ROW = 1
BANKROLL_COL = 10
DEFAULT_BANKROLL = 5000.0

# Competition Logos
COMPETITION_LOGOS = {
    "Brighton": "https://i.postimg.cc/x8kdQh5H/Brighton_Hove_Albion_logo.png",
    "Africa Cup of Nations": "https://i.postimg.cc/5yHtJTgz/2025_Africa_Cup_of_Nations_logo.png"
}

COMPETITION_GRADIENTS = {
    "Brighton": "linear-gradient(90deg, #4CABFF, #E6F7FF)",
    "Africa Cup of Nations": "linear-gradient(90deg, #CE1126, #FCD116, #007A33)"
}

st.set_page_config(
    page_title="GoalMetric Elite Dashboard",
    layout="wide",
    page_icon=APP_LOGO,
    initial_sidebar_state="expanded"
)

# ============================================================================
# 2. STYLING
# ============================================================================

def get_custom_css() -> str:
    """Returns custom CSS styling for the application"""
    return f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;900&display=swap');
    
    /* ===== RESET ===== */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header[data-testid="stHeader"] {{ background: transparent !important; }}
    
    /* ===== CUSTOM ARROWS (תיקון: חצים במקום טקסט) ===== */
    
    /* Open Sidebar Arrow - WHITE COLOR */
    button[aria-label="Open sidebar"] {{
        background-color: rgba(255, 255, 255, 0.15) !important;
        border: 2px solid rgba(255, 255, 255, 0.8) !important;
        border-radius: 12px !important;
        width: 50px !important; 
        height: 50px !important;
        margin-top: 20px !important;
        margin-left: 10px !important;
        position: relative !important;
        transition: all 0.3s ease !important;
    }}
    
    button[aria-label="Open sidebar"]::before {{
        content: "→" !important;
        position: absolute !important;
        top: 50% !important;
        left: 50% !important;
        transform: translate(-50%, -50%) !important;
        font-size: 28px !important;
        font-weight: bold !important;
        color: #ffffff !important;
        text-shadow: 0px 2px 4px rgba(0,0,0,0.5) !important;
    }}
    
    button[aria-label="Open sidebar"]:hover {{
        background-color: rgba(255, 255, 255, 0.25) !important;
        border-color: rgba(255, 255, 255, 1) !important;
        transform: scale(1.05) !important;
    }}
    
    button[aria-label="Open sidebar"] svg {{
        display: none !important;
    }}
    
    /* Close Sidebar Arrow - BLACK COLOR */
    button[aria-label="Collapse sidebar"] {{
        background-color: rgba(0, 0, 0, 0.08) !important;
        border: 2px solid rgba(0, 0, 0, 0.3) !important;
        border-radius: 12px !important;
        width: 50px !important;
        height: 50px !important;
        position: relative !important;
        transition: all 0.3s ease !important;
    }}
    
    button[aria-label="Collapse sidebar"]::before {{
        content: "←" !important;
        position: absolute !important;
        top: 50% !important;
        left: 50% !important;
        transform: translate(-50%, -50%) !important;
        font-size: 28px !important;
        font-weight: bold !important;
        color: #000000 !important;
        text-shadow: none !important;
    }}
    
    button[aria-label="Collapse sidebar"]:hover {{
        background-color: rgba(0, 0, 0, 0.15) !important;
        border-color: rgba(0, 0, 0, 0.5) !important;
        transform: scale(1.05) !important;
    }}
    
    button[aria-label="Collapse sidebar"] svg {{
        display: none !important;
    }}
    
    .stTooltipIcon {{ display: none !important; }}

    /* ===== MAIN AREA TEXT (WHITE) ===== */
    [data-testid="stAppViewContainer"] h1, 
    [data-testid="stAppViewContainer"] h2, 
    [data-testid="stAppViewContainer"] h3, 
    [data-testid="stAppViewContainer"] p, 
    [data-testid="stAppViewContainer"] span, 
    [data-testid="stAppViewContainer"] label,
    [data-testid="stAppViewContainer"] div[data-testid="stMarkdownContainer"] p {{
        color: #ffffff !important;
        text-shadow: 0px 2px 4px rgba(0,0,0,0.8);
        font-family: 'Montserrat', sans-serif;
    }}
    [data-testid="stMetricValue"] {{ 
        color: #ffffff !important; 
        text-shadow: 0px 2px 5px rgba(0,0,0,1); 
    }}
    [data-testid="stMetricLabel"] {{ 
        color: #dddddd !important; 
    }}

    /* ===== FORM ===== */
    [data-testid="stForm"] {{
        background: linear-gradient(180deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.05) 100%);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.2);
        border-radius: 16px;
        padding: 25px;
    }}
    [data-testid="stForm"] label p {{ 
        color: #ffffff !important; 
        font-weight: 600; 
    }}

    /* ===== INPUT FIELDS ===== */
    input {{ 
        background-color: #ffffff !important; 
        color: #000000 !important; 
        font-weight: bold; 
        border-radius: 5px; 
    }}
    div[data-baseweb="select"] > div {{ 
        background-color: #ffffff !important; 
        color: #000000 !important; 
    }}
    div[data-baseweb="select"] span {{ 
        color: #000000 !important; 
    }}

    /* ===== SIDEBAR (תיקון: טקסט שחור ברור) ===== */
    [data-testid="stSidebar"] {{ 
        background-color: rgba(255, 255, 255, 0.98) !important;
    }}
    
    [data-testid="stSidebar"]::before {{
        content: ""; 
        position: absolute; 
        top: 0; 
        left: 0; 
        width: 100%; 
        height: 100%;
        background-image: url("{SIDEBAR_BG}"); 
        background-size: cover;
        filter: blur(5px); 
        opacity: 0.3;
        z-index: -1;
    }}
    
    /* תיקון קריטי: כל הטקסט בסיידבר יהיה שחור */
    [data-testid="stSidebar"] *,
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] p, 
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] div,
    [data-testid="stSidebar"] .stMarkdown,
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"],
    [data-testid="stSidebar"] [data-testid="stMetricLabel"],
    [data-testid="stSidebar"] [data-testid="stMetricValue"] {{
        color: #000000 !important;
        text-shadow: none !important;
        font-weight: 600 !important;
    }}
    
    [data-testid="stSidebar"] input {{
        border: 1px solid #ccc !important;
        color: #000000 !important;
    }}
    
    /* כפתורים בסיידבר */
    [data-testid="stSidebar"] button {{
        color: #000000 !important;
        font-weight: 700 !important;
    }}

    /* ===== BANNERS (50% OPACITY) ===== */
    .banner-container {{
        border-radius: 12px;
        padding: 15px 20px;
        margin-bottom: 15px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 4px 10px rgba(0,0,0,0.3);
        backdrop-filter: blur(5px);
    }}
    
    .status-win {{ 
        background: rgba(46, 204, 113, 0.5) !important;
        border-left: 10px solid #27ae60; 
        border: 1px solid rgba(46, 204, 113, 0.6);
    }}
    
    .status-loss {{ 
        background: rgba(231, 76, 60, 0.5) !important;
        border-left: 10px solid #c0392b; 
        border: 1px solid rgba(231, 76, 60, 0.6);
    }}

    .banner-container span, .banner-container div {{
        color: #ffffff !important;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.8) !important;
    }}
    
    /* Overview Light Banners */
    .track-overview-banner {{
        background: linear-gradient(90deg, #ffffff, #f0f0f0);
        border-radius: 12px;
        padding: 15px 20px;
        margin-bottom: 15px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-left: 10px solid #333;
        box-shadow: 0 4px 15px rgba(0,0,0,0.5);
    }}
    .track-overview-banner span, .track-overview-banner div {{
        color: #000000 !important;
        text-shadow: none !important;
    }}

    /* ===== METRIC BOXES ===== */
    .metric-box {{
        background-color: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(5px);
        border: 1px solid rgba(255,255,255,0.2);
        border-radius: 15px;
        padding: 20px;
        text-align: center;
    }}
    .m-lbl {{ 
        font-size: 0.8rem; 
        font-weight: bold; 
        color: #ddd !important; 
        text-transform: uppercase; 
    }}
    .m-val {{ 
        font-size: 1.8rem; 
        font-weight: 900; 
        color: white !important; 
    }}

    /* ===== BACKGROUND ===== */
    [data-testid="stAppViewContainer"] {{
        background-image: linear-gradient(rgba(0, 0, 0, 0.7), rgba(0, 0, 0, 0.7)), url("{BG_IMAGE}");
        background-attachment: fixed; 
        background-size: cover; 
        background-position: center;
    }}
    
    [data-testid="stDataFrame"] {{ 
        display: none; 
    }}
    </style>
    """

st.markdown(get_custom_css(), unsafe_allow_html=True)

# ============================================================================
# 3. BACKEND LOGIC WITH ERROR HANDLING & CACHING
# ============================================================================

@st.cache_data(ttl=300)  # Cache for 5 minutes
def connect_db() -> Tuple[List[Dict], Optional[object], float]:
    """
    Connect to Google Sheets and retrieve data
    Returns: (data, worksheet_object, base_bankroll)
    """
    try:
        gc = gspread.service_account_from_dict(st.secrets["service_account"])
        sh = gc.open_by_url(st.secrets["sheet_url"])
        ws = sh.get_worksheet(0)
        data = ws.get_all_records()
        
        # Get bankroll with proper error handling
        try:
            bankroll_value = ws.cell(BANKROLL_ROW, BANKROLL_COL).value
            base_br = float(str(bankroll_value).replace(',', '')) if bankroll_value else DEFAULT_BANKROLL
        except (ValueError, AttributeError) as e:
            st.warning(f"לא ניתן לקרוא bankroll, משתמש בערך ברירת מחדל: ₪{DEFAULT_BANKROLL:,.0f}")
            base_br = DEFAULT_BANKROLL
        
        return data, ws, base_br
        
    except gspread.exceptions.APIError as e:
        st.error(f"שגיאת API של Google Sheets: {e}")
        return [], None, DEFAULT_BANKROLL
    except Exception as e:
        st.error(f"שגיאה בחיבור למסד הנתונים: {e}")
        return [], None, DEFAULT_BANKROLL


def process_logic(raw: List[Dict]) -> pd.DataFrame:
    """
    Process raw data from Google Sheets into structured DataFrame
    Maintains cycle tracking logic for profit/loss calculation
    """
    if not raw:
        return pd.DataFrame()
    
    rows = []
    cycle_tracker = {}  # Tracks accumulated stakes per competition
    
    for r in raw:
        try:
            # Get competition name
            comp = str(r.get('Competition', 'Brighton')).strip() or 'Brighton'
            if comp not in cycle_tracker:
                cycle_tracker[comp] = 0.0
            
            # Parse odds and stake
            odds_str = str(r.get('Odds', 1)).replace(',', '.')
            odds = float(odds_str)
            
            stake_str = str(r.get('Stake', 0)).replace(',', '')
            stake = float(stake_str) if r.get('Stake') else 0.0
            
            # Determine win/loss
            result = str(r.get('Result', '')).strip()
            is_win = "Draw (X)" in result
            
            # Calculate gross winnings
            gross_win = stake * odds if is_win else 0.0
            
            # Update cycle tracker
            cycle_tracker[comp] += stake
            
            # Calculate net cycle profit
            if is_win:
                net_cycle_profit = gross_win - cycle_tracker[comp]
                cycle_tracker[comp] = 0.0  # Reset cycle after win
            else:
                net_cycle_profit = -stake
            
            rows.append({
                "Date": r.get('Date', ''),
                "Comp": comp,
                "Match": f"{r.get('Home Team', '')} vs {r.get('Away Team', '')}",
                "Odds": odds,
                "Stake": stake,
                "Gross": gross_win,
                "Cycle_Net": net_cycle_profit,
                "Status": "✅ Won" if is_win else "❌ Lost"
            })
            
        except ValueError as e:
            st.warning(f"שגיאה בעיבוד שורה (תאריך: {r.get('Date', 'לא ידוע')}): {e}")
            continue
        except Exception as e:
            st.error(f"שגיאה לא צפויה בעיבוד נתונים: {e}")
            continue
    
    return pd.DataFrame(rows)


def validate_match_input(home: str, away: str, odds: float, stake: float) -> None:
    """Validate user input before adding to database"""
    if not home or not away:
        raise ValueError("חובה למלא שם שתי הקבוצות")
    if odds < 1.01:
        raise ValueError("Odds חייב להיות לפחות 1.01")
    if stake <= 0:
        raise ValueError("Stake חייב להיות מספר חיובי")


def update_bankroll(worksheet: object, current_br: float, amount: float, operation: str) -> bool:
    """
    Update bankroll in Google Sheets
    Returns True if successful, False otherwise
    """
    try:
        new_bankroll = current_br + amount if operation == "deposit" else current_br - amount
        
        if new_bankroll < 0:
            st.error("לא ניתן למשוך סכום גדול מהבנקרול הקיים")
            return False
        
        worksheet.update_cell(BANKROLL_ROW, BANKROLL_COL, new_bankroll)
        st.success(f"✅ {'הפקדה' if operation == 'deposit' else 'משיכה'} של ₪{amount:,.0f} בוצעה בהצלחה!")
        return True
        
    except Exception as e:
        st.error(f"שגיאה בעדכון הבנקרול: {e}")
        return False


# ============================================================================
# 4. UI COMPONENT FUNCTIONS
# ============================================================================

def render_metric_box(label: str, value: str, color: Optional[str] = None) -> str:
    """Create HTML for metric display box"""
    color_style = f"color:{color} !important" if color else ""
    return f'''
    <div class="metric-box">
        <div class="m-lbl">{label}</div>
        <div class="m-val" style="{color_style}">{value}</div>
    </div>
    '''


def display_live_bankroll(value: float) -> None:
    """Display prominent live bankroll value"""
    st.markdown(f"""
        <div style="text-align: center; margin-bottom: 40px;">
            <div style="font-size: 3.5rem; font-weight: 300; color: #fff; text-shadow: 0 0 25px rgba(255,255,255,0.5);">
                ₪{value:,.2f}
            </div>
            <div style="font-size: 0.9rem; font-weight: 700; color: #fff; letter-spacing: 3px; text-transform: uppercase;">
                LIVE BANKROLL
            </div>
        </div>
    """, unsafe_allow_html=True)


def render_competition_header(competition: str) -> None:
    """Render competition-specific header with logo"""
    logo = COMPETITION_LOGOS.get(competition, "")
    gradient = COMPETITION_GRADIENTS.get(competition, "linear-gradient(90deg, #4CABFF, #E6F7FF)")
    text_color = "#004085" if competition == "Brighton" else "white"
    
    st.markdown(f'''
        <div style="
            background:{gradient}; 
            border-radius:15px; 
            padding:25px; 
            display:flex; 
            align-items:center; 
            margin-bottom:20px; 
            box-shadow: 0 0 20px rgba(0,0,0,0.5);">
            <img src="{logo}" style="height:80px; margin-right:30px;">
            <h1 style="color:{text_color} !important; margin:0; text-shadow:none !important;">
                {competition.upper()}
            </h1>
        </div>
    ''', unsafe_allow_html=True)


def render_activity_log(df: pd.DataFrame) -> None:
    """Render activity log with banners"""
    st.markdown("### 📜 Activity Log")
    
    if df.empty:
        st.info("אין פעילות להצגה")
        return
    
    for _, row in df.sort_index(ascending=False).iterrows():
        is_win = "Won" in row['Status']
        banner_class = "status-win" if is_win else "status-loss"
        
        cycle_val = f"+₪{row['Cycle_Net']:,.0f}" if is_win else f"-₪{abs(row['Cycle_Net']):,.0f}"
        cycle_col = "#2ecc71" if is_win else "#e74c3c"
        label = "CYCLE PROFIT" if is_win else "LOSS"
        stake_display = f"Stake: ₪{row['Stake']:,.0f}"
        
        st.markdown(f"""
            <div class="banner-container {banner_class}">
                <div style="flex: 2;">
                    <span style="font-size: 1.2rem; font-weight: 900;">{row['Match']}</span><br>
                    <span style="font-size: 0.85rem; opacity: 0.8;">{row['Date']} | Odds: {row['Odds']}</span><br>
                    <span style="font-size: 0.8rem; font-weight: bold; opacity: 0.9;">{stake_display}</span>
                </div>
                <div style="flex: 1; text-align: right;">
                    <span style="font-size: 0.8rem; font-weight: bold; opacity: 0.8;">{label}</span><br>
                    <span style="font-size: 1.4rem; font-weight: 900; color: {cycle_col} !important;">{cycle_val}</span>
                </div>
            </div>
        """, unsafe_allow_html=True)


# ============================================================================
# 5. MAIN APPLICATION LOGIC
# ============================================================================

# Initialize session state for confirmation dialogs
if 'confirm_withdraw' not in st.session_state:
    st.session_state['confirm_withdraw'] = False
if 'last_refresh' not in st.session_state:
    st.session_state['last_refresh'] = datetime.datetime.now()

# Load data with spinner
with st.spinner('טוען נתונים מהשרת...'):
    raw_data, worksheet, base_br = connect_db()
    df = process_logic(raw_data)

# Calculate live bankroll
live_br_val = base_br + (df['Gross'].sum() - df['Stake'].sum()) if not df.empty else base_br

# ============================================================================
# 6. SIDEBAR
# ============================================================================

with st.sidebar:
    st.image(APP_LOGO, width=120)
    
    st.markdown("### 💰 WALLET CONTROL")
    st.metric("Base Bankroll", f"₪{base_br:,.0f}")
    
    amount = st.number_input("Amount", min_value=0.0, value=100.0, step=50.0, key="amount_input")
    
    col1, col2 = st.columns(2)
    
    if col1.button("💵 Deposit", use_container_width=True):
        if worksheet and update_bankroll(worksheet, base_br, amount, "deposit"):
            st.cache_data.clear()
            st.rerun()
    
    if col2.button("💸 Withdraw", use_container_width=True):
        if worksheet and update_bankroll(worksheet, base_br, amount, "withdraw"):
            st.cache_data.clear()
            st.rerun()
    
    st.divider()
    
    view = st.selectbox("🧭 Navigation", ["🏆 Overview", "Brighton", "Africa Cup of Nations"])
    
    if st.button("🔄 Sync Cloud", use_container_width=True):
        st.cache_data.clear()
        st.session_state['last_refresh'] = datetime.datetime.now()
        st.rerun()
    
    st.divider()
    st.caption(f"🕐 Last refresh: {st.session_state['last_refresh'].strftime('%H:%M:%S')}")

# ============================================================================
# 7. MAIN CONTENT AREA
# ============================================================================

if view == "🏆 Overview":
    st.markdown("<h1 style='text-align: center; letter-spacing: 5px;'>CENTRAL COMMAND</h1>", unsafe_allow_html=True)
    display_live_bankroll(live_br_val)

    if not df.empty:
        # Calculate summary statistics
        summary = df.groupby('Comp').agg({
            'Match': 'count',
            'Stake': 'sum',
            'Gross': 'sum',
            'Status': lambda x: (x == '✅ Won').sum()
        }).reset_index()
        summary['Profit'] = summary['Gross'] - summary['Stake']
        
        # Display top-level metrics
        total_profit = summary['Profit'].sum()
        col1, col2, col3 = st.columns(3)
        
        profit_color = "#00ff88" if total_profit >= 0 else "#ff4b4b"
        
        col1.markdown(render_metric_box("Total Profit", f"₪{total_profit:,.0f}", profit_color), unsafe_allow_html=True)
        col2.markdown(render_metric_box("Total Volume", f"{summary['Match'].sum()}", None), unsafe_allow_html=True)
        
        win_rate = (summary['Status'].sum() / summary['Match'].sum() * 100) if summary['Match'].sum() > 0 else 0
        col3.markdown(render_metric_box("Win Rate", f"{win_rate:.1f}%", None), unsafe_allow_html=True)

        st.markdown("<br><h3>📊 Performance Breakdown</h3>", unsafe_allow_html=True)
        
        # Display competition breakdowns
        for _, row in summary.iterrows():
            profit = row['Profit']
            profit_text = f"+₪{profit:,.0f}" if profit >= 0 else f"-₪{abs(profit):,.0f}"
            profit_style = "#2d6a4f" if profit >= 0 else "#d32f2f"
            win_rate_comp = (row['Status'] / row['Match'] * 100) if row['Match'] > 0 else 0
            
            st.markdown(f"""
                <div class="track-overview-banner">
                    <div style="flex: 1.5;">
                        <span style="font-size: 1.4rem; font-weight: 900;">{row['Comp']}</span>
                    </div>
                    <div style="flex: 1; text-align: center;">
                        <span style="font-size: 0.8rem; font-weight: bold; color: #555 !important;">GAMES</span><br>
                        <span style="font-size: 1.2rem; font-weight: 800;">{row['Match']}</span>
                    </div>
                    <div style="flex: 1; text-align: center;">
                        <span style="font-size: 0.8rem; font-weight: bold; color: #555 !important;">WINS</span><br>
                        <span style="font-size: 1.2rem; font-weight: 800;">{row['Status']} ({win_rate_comp:.1f}%)</span>
                    </div>
                    <div style="flex: 1.2; text-align: right;">
                        <span style="font-size: 0.8rem; font-weight: bold; color: #555 !important;">NET PROFIT</span><br>
                        <span style="font-size: 1.5rem; font-weight: 900; color: {profit_style} !important;">{profit_text}</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)
        
        # Profit distribution chart
        st.markdown("<h3>📈 Distribution</h3>", unsafe_allow_html=True)
        fig = px.bar(summary, x='Comp', y='Profit', color='Profit', 
                     color_continuous_scale=['#ff4b4b', '#00ff88'])
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0.1)',
            font=dict(color='white'),
            height=300,
            showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("אין נתונים להצגה. הוסף משחקים כדי להתחיל!")

else:
    # Competition-specific view
    render_competition_header(view)
    display_live_bankroll(live_br_val)

    filtered_df = df[df['Comp'] == view].copy() if not df.empty else pd.DataFrame()
    total_net = filtered_df['Gross'].sum() - filtered_df['Stake'].sum() if not filtered_df.empty else 0.0

    # Display metrics
    mc1, mc2, mc3 = st.columns(3)
    mc1.markdown(render_metric_box("Invested", f"₪{filtered_df['Stake'].sum():,.0f}"), unsafe_allow_html=True)
    mc2.markdown(render_metric_box("Gross Rev", f"₪{filtered_df['Gross'].sum():,.0f}"), unsafe_allow_html=True)
    
    net_color = "#