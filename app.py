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
# 2. STYLING WITH WORKING ARROWS
# ============================================================================

def get_custom_css() -> str:
    """Returns custom CSS styling with Unicode arrow solution"""
    return f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;900&display=swap');
    
    /* ===== RESET ===== */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header[data-testid="stHeader"] {{ background: transparent !important; }}
    
    /* ===== WORKING ARROWS SOLUTION ===== */
    
    /* Open Sidebar Button - Main Screen */
    button[aria-label="Open sidebar"] {{
        background: linear-gradient(135deg, rgba(0,0,0,0.9), rgba(40,40,40,0.9)) !important;
        border: 3px solid rgba(255,255,255,0.95) !important;
        border-radius: 14px !important;
        width: 65px !important;
        height: 65px !important;
        margin: 20px 0 0 15px !important;
        box-shadow: 0 6px 25px rgba(0,0,0,0.8), inset 0 1px 3px rgba(255,255,255,0.2) !important;
        position: relative !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        cursor: pointer !important;
        overflow: visible !important;
    }}
    
    /* Hide original content completely */
    button[aria-label="Open sidebar"] svg,
    button[aria-label="Open sidebar"] > div,
    button[aria-label="Open sidebar"] > span {{
        opacity: 0 !important;
        width: 0 !important;
        height: 0 !important;
        position: absolute !important;
        pointer-events: none !important;
    }}
    
    /* Create white arrow with pseudo-element */
    button[aria-label="Open sidebar"]::after {{
        content: "➤" !important;
        position: absolute !important;
        top: 50% !important;
        left: 50% !important;
        transform: translate(-50%, -50%) !important;
        font-size: 32px !important;
        font-weight: 900 !important;
        color: #ffffff !important;
        text-shadow: 
            0 2px 8px rgba(0,0,0,0.9),
            0 0 20px rgba(255,255,255,0.3) !important;
        display: block !important;
        line-height: 1 !important;
        z-index: 10 !important;
    }}
    
    button[aria-label="Open sidebar"]:hover {{
        background: linear-gradient(135deg, rgba(255,255,255,0.15), rgba(255,255,255,0.05)) !important;
        border-color: #ffffff !important;
        transform: scale(1.12) translateY(-2px) !important;
        box-shadow: 0 10px 35px rgba(0,0,0,0.9), inset 0 1px 3px rgba(255,255,255,0.3) !important;
    }}
    
    button[aria-label="Open sidebar"]:hover::after {{
        transform: translate(-50%, -50%) scale(1.15) !important;
        text-shadow: 
            0 3px 12px rgba(0,0,0,1),
            0 0 30px rgba(255,255,255,0.5) !important;
    }}
    
    /* Close Sidebar Button - Inside Sidebar */
    button[aria-label="Collapse sidebar"] {{
        background: linear-gradient(135deg, rgba(255,255,255,0.98), rgba(245,245,245,0.98)) !important;
        border: 3px solid rgba(0,0,0,0.5) !important;
        border-radius: 14px !important;
        width: 65px !important;
        height: 65px !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.25), inset 0 1px 2px rgba(0,0,0,0.1) !important;
        position: relative !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        cursor: pointer !important;
        overflow: visible !important;
    }}
    
    /* Hide original content */
    button[aria-label="Collapse sidebar"] svg,
    button[aria-label="Collapse sidebar"] > div,
    button[aria-label="Collapse sidebar"] > span {{
        opacity: 0 !important;
        width: 0 !important;
        height: 0 !important;
        position: absolute !important;
        pointer-events: none !important;
    }}
    
    /* Create black arrow pointing left */
    button[aria-label="Collapse sidebar"]::after {{
        content: "◄" !important;
        position: absolute !important;
        top: 50% !important;
        left: 50% !important;
        transform: translate(-50%, -50%) !important;
        font-size: 36px !important;
        font-weight: 900 !important;
        color: #000000 !important;
        text-shadow: 
            0 1px 3px rgba(255,255,255,0.8),
            0 0 15px rgba(0,0,0,0.2) !important;
        display: block !important;
        line-height: 1 !important;
        z-index: 10 !important;
    }}
    
    button[aria-label="Collapse sidebar"]:hover {{
        background: linear-gradient(135deg, #ffffff, #f8f8f8) !important;
        border-color: rgba(0,0,0,0.7) !important;
        transform: scale(1.12) translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(0,0,0,0.35), inset 0 1px 2px rgba(0,0,0,0.15) !important;
    }}
    
    button[aria-label="Collapse sidebar"]:hover::after {{
        transform: translate(-50%, -50%) scale(1.15) !important;
        color: #000000 !important;
        text-shadow: 
            0 2px 5px rgba(255,255,255,0.9),
            0 0 20px rgba(0,0,0,0.3) !important;
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

    /* ===== SIDEBAR (BLACK TEXT) ===== */
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
    
    /* All sidebar text in BLACK */
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
# 3. BACKEND LOGIC
# ============================================================================

@st.cache_data(ttl=300)
def connect_db() -> Tuple[List[Dict], Optional[object], float]:
    try:
        gc = gspread.service_account_from_dict(st.secrets["service_account"])
        sh = gc.open_by_url(st.secrets["sheet_url"])
        ws = sh.get_worksheet(0)
        data = ws.get_all_records()
        
        try:
            bankroll_value = ws.cell(BANKROLL_ROW, BANKROLL_COL).value
            base_br = float(str(bankroll_value).replace(',', '')) if bankroll_value else DEFAULT_BANKROLL
        except:
            base_br = DEFAULT_BANKROLL
        
        return data, ws, base_br
    except Exception as e:
        st.error(f"שגיאה בחיבור: {e}")
        return [], None, DEFAULT_BANKROLL


def process_logic(raw: List[Dict]) -> pd.DataFrame:
    if not raw:
        return pd.DataFrame()
    
    rows = []
    cycle_tracker = {}
    
    for r in raw:
        try:
            comp = str(r.get('Competition', 'Brighton')).strip() or 'Brighton'
            if comp not in cycle_tracker:
                cycle_tracker[comp] = 0.0
            
            odds = float(str(r.get('Odds', 1)).replace(',', '.'))
            stake = float(str(r.get('Stake', 0)).replace(',', '')) if r.get('Stake') else 0.0
            result = str(r.get('Result', '')).strip()
            is_win = "Draw (X)" in result
            
            gross_win = stake * odds if is_win else 0.0
            cycle_tracker[comp] += stake
            
            if is_win:
                net_cycle_profit = gross_win - cycle_tracker[comp]
                cycle_tracker[comp] = 0.0
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
        except:
            continue
    
    return pd.DataFrame(rows)


def validate_match_input(home: str, away: str, odds: float, stake: float) -> None:
    if not home or not away:
        raise ValueError("חובה למלא שם שתי הקבוצות")
    if odds < 1.01:
        raise ValueError("Odds חייב להיות לפחות 1.01")
    if stake <= 0:
        raise ValueError("Stake חייב להיות מספר חיובי")


def update_bankroll(worksheet: object, current_br: float, amount: float, operation: str) -> bool:
    try:
        new_bankroll = current_br + amount if operation == "deposit" else current_br - amount
        
        if new_bankroll < 0:
            st.error("לא ניתן למשוך סכום גדול מהבנקרול הקיים")
            return False
        
        worksheet.update_cell(BANKROLL_ROW, BANKROLL_COL, new_bankroll)
        st.success(f"✅ {'הפקדה' if operation == 'deposit' else 'משיכה'} של ₪{amount:,.0f} בוצעה בהצלחה!")
        return True
    except Exception as e:
        st.error(f"שגיאה: {e}")
        return False


# ============================================================================
# 4. UI COMPONENTS
# ============================================================================

def render_metric_box(label: str, value: str, color: Optional[str] = None) -> str:
    color_style = f"color:{color} !important" if color else ""
    return f'<div class="metric-box"><div class="m-lbl">{label}</div><div class="m-val" style="{color_style}">{value}</div></div>'


def display_live_bankroll(value: float) -> None:
    st.markdown(f"""
        <div style="text-align: center; margin-bottom: 40px;">
            <div style="font-size: 3.5rem; font-weight: 300; color: #fff; text-shadow: 0 0 25px rgba(255,255,255,0.5);">₪{value:,.2f}</div>
            <div style="font-size: 0.9rem; font-weight: 700; color: #fff; letter-spacing: 3px; text-transform: uppercase;">LIVE BANKROLL</div>
        </div>
    """, unsafe_allow_html=True)


def render_competition_header(competition: str) -> None:
    logo = COMPETITION_LOGOS.get(competition, "")
    gradient = COMPETITION_GRADIENTS.get(competition, "linear-gradient(90deg, #4CABFF, #E6F7FF)")
    text_color = "#004085" if competition == "Brighton" else "white"
    
    st.markdown(f'''
        <div style="background:{gradient}; border-radius:15px; padding:25px; display:flex; align-items:center; margin-bottom:20px; box-shadow: 0 0 20px rgba(0,0,0,0.5);">
            <img src="{logo}" style="height:80px; margin-right:30px;">
            <h1 style="color:{text_color} !important; margin:0; text-shadow:none !important;">{competition.upper()}</h1>
        </div>
    ''', unsafe_allow_html=True)


def render_activity_log(df: pd.DataFrame) -> None:
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
        
        st.markdown(f"""
            <div class="banner-container {banner_class}">
                <div style="flex: 2;">
                    <span style="font-size: 1.2rem; font-weight: 900;">{row['Match']}</span><br>
                    <span style="font-size: 0.85rem; opacity: 0.8;">{row['Date']} | Odds: {row['Odds']}</span><br>
                    <span style="font-size: 0.8rem; font-weight: bold; opacity: 0.9;">Stake: ₪{row['Stake']:,.0f}</span>
                </div>
                <div style="flex: 1; text-align: right;">
                    <span style="font-size: 0.8rem; font-weight: bold; opacity: 0.8;">{label}</span><br>
                    <span style="font-size: 1.4rem; font-weight: 900; color: {cycle_col} !important;">{cycle_val}</span>
                </div>
            </div>
        """, unsafe_allow_html=True)


# ============================================================================
# 5. MAIN APP
# ============================================================================

if 'last_refresh' not in st.session_state:
    st.session_state['last_refresh'] = datetime.datetime.now()

with st.spinner('טוען נתונים...'):
    raw_data, worksheet, base_br = connect_db()
    df = process_logic(raw_data)

live_br_val = base_br + (df['Gross'].sum() - df['Stake'].sum()) if not df.empty else base_br

# SIDEBAR
with st.sidebar:
    st.image(APP_LOGO, width=120)
    st.markdown("### 💰 WALLET CONTROL")
    st.metric("Base Bankroll", f"₪{base_br:,.0f}")
    
    amount = st.number_input("Amount", min_value=0.0, value=100.0, step=50.0)
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
        st.rerun()
    
    st.divider()
    st.caption(f"🕐 Last refresh: {st.session_state['last_refresh'].strftime('%H:%M:%S')}")

# MAIN CONTENT
if view == "🏆 Overview":
    st.markdown("<h1 style='text-align: center; letter-spacing: 5px;'>CENTRAL COMMAND</h1>", unsafe_allow_html=True)
    display_live_bankroll(live_br_val)

    if not df.empty:
        summary = df.groupby('Comp').agg({
            'Match': 'count', 'Stake': 'sum', 'Gross': 'sum',
            'Status': lambda x: (x == '✅ Won').sum()
        }).reset_index()
        summary['Profit'] = summary['Gross'] - summary['Stake']
        
        total_profit = summary['Profit'].sum()
        col1, col2, col3 = st.columns(3)
        profit_color = "#00ff88" if total_profit >= 0 else "#ff4b4b"
        
        col1.markdown(render_metric_box("Total Profit", f"₪{total_profit:,.0f}", profit_color), unsafe_allow_html=True)
        col2.markdown(render_metric_box("Total Volume", f"{summary['Match'].sum()}", None), unsafe_allow_html=True)
        win_rate = (summary['Status'].sum() / summary['Match'].sum() * 100) if summary['Match'].sum() > 0 else 0
        col3.markdown(render_metric_box("Win Rate", f"{win_rate:.1f}%", None), unsafe_allow_html=True)

        st.markdown("<br><h3>📊 Performance Breakdown</h3>", unsafe_allow_html=True)
        
        for _, row in summary.iterrows():
            profit = row['Profit']
            profit_text = f"+₪{profit:,.0f}" if profit >= 0 else f"-₪{abs(profit):,.0f}"
            profit_style = "#2d6a4f" if profit >= 0 else "#d32f2f"
            wr = (row['Status'] / row['Match'] * 100) if row['Match'] > 0 else 0
            
            st.markdown(f"""
                <div class="track-overview-banner">
                    <div style="flex: 1.5;"><span style="font-size: 1.4rem; font-weight: 900;">{row['Comp']}</span></div>
                    <div style="flex: 1; text-align: center;">
                        <span style="font-size: 0.8rem; font-weight: bold; color: #555 !important;">GAMES</span><br>
                        <span style="font-size: 1.2rem; font-weight: 800;">{row['Match']}</span>
                    </div>
                    <div style="flex: 1; text-align: center;">
                        <span style="font-size: 0.8rem; font-weight: bold; color: #555 !important;">WINS</span><br>
                        <span style="font-size: 1.2rem; font-weight: 800;">{row['Status']} ({wr:.1f}%)</span>
                    </div>
                    <div style="flex: 1.2; text-align: right;">
                        <span style="font-size: 0.8rem; font-weight: bold; color: #555 !important;">NET PROFIT</span><br>
                        <span style="font-size: 1.5rem; font-weight: 900; color: {profit_style} !important;">{profit_text}</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)
        
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
    # Competition View
    render_competition_header(view)
    display_live_bankroll(live_br_val)

    filtered_df = df[df['Comp'] == view].copy() if not df.empty else pd.DataFrame()
    total_net = filtered_df['Gross'].sum() - filtered_df['Stake'].sum() if not filtered_df.empty else 0.0

    mc1, mc2, mc3 = st.columns(3)
    mc1.markdown(render_metric_box("Invested", f"₪{filtered_df['Stake'].sum():,.0f}"), unsafe_allow_html=True)
    mc2.markdown(render_metric_box("Gross Rev", f"₪{filtered_df['Gross'].sum():,.0f}"), unsafe_allow_html=True)
    
    net_color = "#00ff88" if total_net >= 0 else "#ff4b4b"
    mc3.markdown(render_metric_box("Net Profit", f"₪{total_net:,.0f}", net_color), unsafe_allow_html=True)

    st.markdown("<br><h2>⚡ Performance Strategy</h2>", unsafe_allow_html=True)
    form_col, chart_col = st.columns([1, 1.2])
    
    with form_col:
        with st.form("add_match"):
            st.markdown("### ⚽ New Entry")
            home_team = st.text_input("Home Team", value="Brighton" if view == "Brighton" else "")
            away_team = st.text_input("Away Team")
            odds = st.number_input("Odds", value=3.2, min_value=1.01, step=0.1)
            stake = st.number_input("Stake", value=30.0, min_value=0.0, step=10.0)
            result = st.radio("Outcome", ["Draw (X)", "No Draw"], horizontal=True)
            
            if st.form_submit_button("✅ SUBMIT ENTRY", use_container_width=True):
                try:
                    validate_match_input(home_team, away_team, odds, stake)
                    
                    if worksheet:
                        worksheet.append_row([
                            str(datetime.date.today()),
                            view,
                            home_team,
                            away_team,
                            odds,
                            result,
                            stake,
                            0.0
                        ])
                        st.success("✅ Entry added successfully!")
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error("❌ No connection to database")
                        
                except ValueError as e:
                    st.error(f"❌ {str(e)}")
                except Exception as e:
                    st.error(f"❌ Error adding entry: {e}")
    
    with chart_col:
        if not filtered_df.empty:
            filtered_df['Equity'] = base_br + (filtered_df['Gross'].cumsum() - filtered_df['Stake'].cumsum())
            
            fig_line = px.line(filtered_df, y='Equity', x=filtered_df.index, 
                              title="Equity Curve")
            fig_line.update_traces(line_color='#00ff88', line_width=4)
            fig_line.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0.1)',
                font=dict(color='white'),
                height=400,
                showlegend=False
            )
            st.plotly_chart(fig_line, use_container_width=True)
        else:
            st.info("📊 No data to display yet")

    render_activity_log(filtered_df)