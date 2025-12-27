import streamlit as st
import pandas as pd
import plotly.express as px
import gspread
import datetime

# --- 1. CONFIGURATION ---
APP_LOGO_URL = "https://i.postimg.cc/8Cr6SypK/yzwb-ll-sm.png"
BG_IMAGE_URL = "https://i.postimg.cc/GmFZ4KS7/Gemini-Generated-Image-k1h11zk1h11zk1h1.png"
SIDEBAR_BG_IMAGE_URL = "https://i.postimg.cc/NfdK3hck/'yzwb-ll'-sm-(1).png"

st.set_page_config(
    page_title="GoalMetric Elite",
    layout="wide",
    page_icon=APP_LOGO_URL,
    initial_sidebar_state="expanded"
)

# --- 2. CSS STYLING (Final Typography & Arrow Fix) ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;600;900&family=Inter:wght@400;600&display=swap');
    
    /* CLEANUP */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    [data-testid="stDecoration"] {{display: none;}}
    
    /* Header & Tooltip Fix (Prevents 'keyb' artifact) */
    header[data-testid="stHeader"] {{
        background: transparent !important;
    }}
    .stTooltipIcon {{ display: none !important; }}

    /* OPEN ARROW (Outside) - WHITE */
    [data-testid="stSidebarCollapsedControl"] {{
        background-color: rgba(0, 0, 0, 0.5) !important;
        border-radius: 50% !important;
        color: #ffffff !important;
        width: 40px; height: 40px;
        display: flex; align-items: center; justify-content: center;
    }}
    [data-testid="stSidebarCollapsedControl"] svg {{ fill: white !important; }}

    /* CLOSE ARROW (Inside) - BLACK */
    [data-testid="stSidebar"] button[kind="header"] svg {{
        fill: #000000 !important;
    }}

    /* MAIN BACKGROUND */
    [data-testid="stAppViewContainer"] {{
        background-image: linear-gradient(rgba(0, 0, 0, 0.7), rgba(0, 0, 0, 0.7)), url("{BG_IMAGE_URL}");
        background-attachment: fixed; background-size: cover; background-position: center;
    }}

    /* SIDEBAR BLUR */
    [data-testid="stSidebar"] {{
        position: relative;
        background-color: rgba(255, 255, 255, 0.8) !important;
        border-right: 1px solid rgba(255,255,255,0.2);
    }}
    [data-testid="stSidebar"]::before {{
        content: ""; position: absolute; top: 0; left: 0; width: 100%; height: 100%;
        background-image: url("{SIDEBAR_BG_IMAGE_URL}");
        background-size: cover; background-position: center;
        filter: blur(5px); z-index: -1; transform: scale(1.05);
    }}

    /* SIDEBAR TEXT (BLACK) */
    [data-testid="stSidebar"] *, [data-testid="stSidebar"] [data-testid="stMetricValue"] {{
        color: #000000 !important; text-shadow: none !important;
    }}
    
    /* MAIN AREA TEXT (WHITE) */
    .main h1, .main h2, .main h3, .main h4, .main p, .main span {{
        color: #ffffff !important;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.8);
    }}
    
    /* TARGET SPECIFIC HEADERS FROM IMAGE (Performance & Log) */
    [data-testid="stHeader"] h2, .main .stMarkdown h2, .main .stMarkdown h3 {{
        color: #ffffff !important;
    }}
    
    /* CAPTION (Win Rate) FIX */
    [data-testid="stCaptionContainer"] p {{
        color: #ffffff !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
    }}

    /* INPUTS & CARDS */
    [data-testid="stSidebar"] input {{ color: black !important; background-color: white !important; }}
    [data-testid="stDataFrame"] {{ background-color: white !important; border-radius: 8px; }}
    [data-testid="stDataFrame"] * {{ color: black !important; }}
    [data-testid="stForm"] {{ background-color: rgba(255, 255, 255, 0.95); border-radius: 15px; padding: 25px; }}
    [data-testid="stForm"] * {{ color: black !important; }}

    .custom-metric-box {{
        background-color: rgba(255, 255, 255, 0.95);
        border-radius: 12px; padding: 20px; text-align: center;
    }}
    .metric-card-label {{ color: #555 !important; font-weight: 700; font-size: 13px; }}
    .metric-card-value {{ color: #1b4332 !important; font-weight: 900; font-size: 26px; }}

    @media only screen and (max-width: 768px) {{
        .banner-text {{ display: none !important; }}
        .banner-container {{ justify-content: center !important; }}
        .banner-img {{ height: 100px !important; }}
    }}
    </style>
""", unsafe_allow_html=True)

# --- 3. BACKEND LOGIC ---
def get_data_from_sheets():
    try:
        gc = gspread.service_account_from_dict(st.secrets["service_account"])
        sh = gc.open_by_url(st.secrets["sheet_url"])
        worksheet = sh.get_worksheet(0)
        data = worksheet.get_all_records()
        try:
            val = worksheet.cell(1, 10).value
            initial_bankroll = float(str(val).replace(',', '')) if val else 5000.0
        except: initial_bankroll = 5000.0
        return data, worksheet, initial_bankroll
    except Exception as e:
        st.error(f"Connection Error: {e}")
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

    for row in raw_data:
        try:
            comp = str(row.get('Competition', 'Brighton')).strip()
            if not comp: comp = 'Brighton'
            if comp not in next_bets:
                next_bets[comp] = 30.0 
                cycle_invest[comp] = 0.0

            try: odds = float(str(row.get('Odds', 1)).replace(',', '.'))
            except: odds = 1.0
            
            stake_val = row.get('Stake')
            if stake_val in [None, '', ' ']: exp = next_bets[comp]
            else: exp = float(str(stake_val).replace(',', ''))
            
            res = str(row.get('Result', '')).strip()
            cycle_invest[comp] += exp
            is_win = "Draw (X)" in res
            
            if is_win:
                inc = exp * odds
                net = inc - cycle_invest[comp]
                roi = f"{(net / cycle_invest[comp]) * 100:.1f}%" if cycle_invest[comp] > 0 else "0%"
                base_reset = float(br_base if "Brighton" in comp else (af_base if "Africa" in comp else 30.0))
                next_bets[comp] = base_reset
                cycle_invest[comp] = 0.0
                status = "✅ Won"
            else:
                inc = 0.0
                net = -exp
                roi = "N/A"
                next_bets[comp] = exp * 2.0
                status = "❌ Lost"
            
            processed.append({
                "Date": row.get('Date', ''), "Comp": comp, "Match": f"{row.get('Home Team','')} vs {row.get('Away Team','')}",
                "Odds": odds, "Expense": exp, "Income": inc, "Net Profit": net, "Status": status, "ROI": roi
            })
        except: continue
    return processed, next_bets

# --- 4. EXECUTION ---
raw_data, worksheet, saved_br = get_data_from_sheets()
processed, next_stakes = calculate_logic(raw_data, 30.0, 20.0)

if processed:
    df = pd.DataFrame(processed)
    current_bal = saved_br + (df['Income'].sum() - df['Expense'].sum())
else:
    df = pd.DataFrame(columns=["Comp", "Income", "Expense", "Net Profit", "Status", "Match"])
    current_bal = saved_br

# --- 5. UI LAYOUT ---
with st.sidebar:
    st.image(APP_LOGO_URL, width=120)
    st.markdown("## WALLET CONTROL")
    st.metric("Base Bankroll", f"₪{saved_br:,.0f}")
    amt = st.number_input("Amount", min_value=0.0, value=100.0, step=50.0, label_visibility="collapsed")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Deposit", use_container_width=True):
            if update_bankroll(worksheet, saved_br + amt): st.rerun()
    with col2:
        if st.button("Withdraw", use_container_width=True):
            if update_bankroll(worksheet, saved_br - amt): st.rerun()
    st.divider()
    track = st.selectbox("View", ["🏆 Overview", "Brighton", "Africa Cup of Nations"], label_visibility="collapsed")
    if st.button("🔄 Sync Cloud", use_container_width=True): st.rerun()

# --- CONTENT RENDERING ---

if track == "🏆 Overview":
    st.markdown("<h1 style='text-align: center;'>CENTRAL COMMAND</h1>", unsafe_allow_html=True)
    st.markdown(f"<h2 style='text-align: center;'>₪{current_bal:,.2f}</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #ccc;'>TOTAL BANKROLL</p>", unsafe_allow_html=True)

    if not df.empty:
        summary = df.groupby('Comp').agg({'Match': 'count', 'Expense': 'sum', 'Income': 'sum', 'Status': lambda x: (x == '✅ Won').sum()}).reset_index()
        summary.columns = ['Competition', 'Games', 'Expenses', 'Revenue', 'Wins']
        summary['Net Profit'] = summary['Revenue'] - summary['Expenses']
        summary['Win Rate'] = (summary['Wins'] / summary['Games'] * 100).apply(lambda x: f"{x:.1f}%")
        
        c1, c2, c3 = st.columns(3)
        total_p = summary['Net Profit'].sum()
        with c1: st.markdown(f'<div class="custom-metric-box"><div class="metric-card-label">ALL TIME PROFIT</div><div class="metric-card-value" style="color: {"#2d6a4f" if total_p >=0 else "#d32f2f"} !important;">₪{total_p:,.0f}</div></div>', unsafe_allow_html=True)
        with c2: st.markdown(f'<div class="custom-metric-box"><div class="metric-card-label">TOTAL GAMES</div><div class="metric-card-value">{summary["Games"].sum()}</div></div>', unsafe_allow_html=True)
        with c3: 
            rate = (summary['Wins'].sum() / summary['Games'].sum() * 100) if summary['Games'].sum() > 0 else 0
            st.markdown(f'<div class="custom-metric-box"><div class="metric-card-label">GLOBAL WIN RATE</div><div class="metric-card-value">{rate:.1f}%</div></div>', unsafe_allow_html=True)
        
        col_c, col_t = st.columns([1, 1])
        with col_c:
            st.subheader("Profit Distribution")
            fig = px.bar(summary, x='Competition', y='Net Profit', color='Net Profit', color_continuous_scale=['#d32f2f', '#2d6a4f'])
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0.1)', font=dict(color='white'), height=300)
            st.plotly_chart(fig, use_container_width=True)
        with col_t:
            st.subheader("Performance Breakdown")
            st.dataframe(summary[['Competition', 'Games', 'Wins', 'Win Rate', 'Net Profit']].style.format({"Net Profit": "₪{:,.0f}"}), use_container_width=True, hide_index=True)

else:
    # --- SPECIFIC TRACK VIEW ---
    logos = {"Brighton": "https://i.postimg.cc/x8kdQh5H/Brighton_Hove_Albion_logo.png", "Africa Cup of Nations": "https://i.postimg.cc/5yHtJTgz/2025_Africa_Cup_of_Nations_logo.png"}
    banner_bg = "linear-gradient(90deg, #4CABFF 0%, #E6F7FF 50%, #4CABFF 100%)" if track == "Brighton" else "linear-gradient(90deg, #CE1126 0%, #FCD116 50%, #007A33 100%)"
    text_c = "#004085" if track == "Brighton" else "#FFFFFF"

    st.markdown(f'<div class="banner-container" style="background: {banner_bg}; border-radius: 15px; padding: 20px; display: flex; align-items: center; margin-bottom: 30px;"><img class="banner-img" src="{logos[track]}" style="height: 70px; margin-right: 25px;"><h1 class="banner-text" style="color: {text_c} !important;">{track.upper()}</h1></div>', unsafe_allow_html=True)
    st.markdown(f"<h2 style='text-align: center;'>₪{current_bal:,.2f}</h2><p style='text-align: center; color: #ccc;'>LIVE BANKROLL</p>", unsafe_allow_html=True)

    f_df = df[df['Comp'] == track].copy() if not df.empty else pd.DataFrame()
    m_exp, m_inc = (f_df['Expense'].sum(), f_df['Income'].sum()) if not f_df.empty else (0.0, 0.0)
    m_net = m_inc - m_exp

    mc1, mc2, mc3 = st.columns(3)
    with mc1: st.markdown(f'<div class="custom-metric-box"><div class="metric-card-label">TOTAL EXPENSES</div><div class="metric-card-value">₪{m_exp:,.0f}</div></div>', unsafe_allow_html=True)
    with mc2: st.markdown(f'<div class="custom-metric-box"><div class="metric-card-label">TOTAL REVENUE</div><div class="metric-card-value">₪{m_inc:,.0f}</div></div>', unsafe_allow_html=True)
    with mc3: 
        c_n = "#2d6a4f" if m_net >= 0 else "#d32f2f"
        st.markdown(f'<div class="custom-metric-box"><div class="metric-card-label">NET PROFIT</div><div class="metric-card-value" style="color: {c_n} !important;">₪{m_net:,.0f}</div></div>', unsafe_allow_html=True)

    nxt = next_stakes.get(track, 30.0)
    st.markdown(f'<div style="text-align: center; margin: 30px 0;"><span style="font-size: 1.4rem;">Next Bet: </span><span style="font-size: 1.6rem; color: #4CAF50; font-weight: 900;">₪{nxt:,.0f}</span></div>', unsafe_allow_html=True)

    col_f, col_g = st.columns([1, 1])
    with col_f:
        with st.form("add_game"):
            st.subheader("Add Match")
            h = st.text_input("Home Team", value="Brighton" if track == "Brighton" else "")
            a = st.text_input("Away Team")
            o = st.number_input("Odds", value=3.2, step=0.1)
            s = st.number_input("Stake", value=float(nxt))
            r = st.radio("Result", ["Draw (X)", "No Draw"], horizontal=True)
            if st.form_submit_button("Submit Game", use_container_width=True):
                worksheet.append_row([str(datetime.date.today()), track, h, a, o, r, s, 0.0])
                st.rerun()

    with col_g:
        st.subheader("Performance")
        if not f_df.empty:
            f_df['Bal'] = saved_br + (f_df['Income'].cumsum() - f_df['Expense'].cumsum())
            fig = px.line(f_df, y='Bal', x=f_df.index)
            fig.update_traces(line_color='#00ff88', line_width=3)
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0.1)', font=dict(color='white'), height=250, margin=dict(l=0,r=0,t=0,b=0))
            st.plotly_chart(fig, use_container_width=True)
            wins = len(f_df[f_df['Status'] == "✅ Won"])
            st.caption(f"Win Rate: {(wins/len(f_df)*100):.1f}% ({wins} W / {len(f_df)-wins} L)")

    st.subheader("📜 Activity Log")
    if not f_df.empty:
        st.dataframe(f_df[['Date', 'Match', 'Odds', 'Expense', 'Net Profit', 'Status']].sort_index(ascending=False), use_container_width=True, hide_index=True)

with st.expander("🛠️ Admin"):
    if st.button("Undo Last"):
        worksheet.delete_rows(len(raw_data) + 1)
        st.rerun()