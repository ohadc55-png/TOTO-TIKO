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

# --- 2. THE ULTIMATE MOBILE & UX CSS ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;700;900&display=swap');
    
    /* Global Reset */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    [data-testid="stDecoration"] {{display: none;}}
    header[data-testid="stHeader"] {{ background: transparent !important; }}
    
    /* Arrow Fix */
    [data-testid="stSidebarCollapsedControl"] {{
        background-color: rgba(0, 0, 0, 0.6) !important;
        border-radius: 50% !important;
        width: 45px !important; height: 45px !important;
        display: flex !important; align-items: center !important; justify-content: center !important;
        margin: 10px !important;
    }}
    [data-testid="stSidebarCollapsedControl"] svg {{ fill: white !important; }}
    
    /* Global Backgrounds */
    [data-testid="stAppViewContainer"] {{
        background-image: linear-gradient(rgba(0, 0, 0, 0.75), rgba(0, 0, 0, 0.75)), url("{BG_IMAGE}");
        background-attachment: fixed; background-size: cover; background-position: center;
    }}
    [data-testid="stSidebar"] {{ background-color: rgba(255, 255, 255, 0.9) !important; }}
    [data-testid="stSidebar"]::before {{
        content: ""; position: absolute; top: 0; left: 0; width: 100%; height: 100%;
        background-image: url("{SIDEBAR_BG}"); background-size: cover;
        filter: blur(4px); z-index: -1;
    }}

    /* Typography */
    .main h1, .main h2, .main h3, .main p, .main span, .main label {{
        color: #ffffff !important;
        text-shadow: 2px 2px 5px rgba(0,0,0,0.9);
        font-family: 'Montserrat', sans-serif;
    }}
    [data-testid="stSidebar"] * {{ color: #000000 !important; text-shadow: none !important; }}

    /* Custom Metric Cards */
    .custom-metric-card {{
        background-color: rgba(255, 255, 255, 0.98);
        border-radius: 12px; padding: 15px; text-align: center;
        box-shadow: 0 10px 25px rgba(0,0,0,0.5);
        margin-bottom: 10px;
    }}
    .c-label {{ color: #555 !important; font-weight: 700; font-size: 11px; text-transform: uppercase; text-shadow: none !important; }}
    .c-value {{ color: #1b4332 !important; font-weight: 900; font-size: 24px; text-shadow: none !important; }}

    /* Activity Log Banners (50% Opacity) */
    .log-banner {{
        padding: 15px 20px; border-radius: 10px; margin-bottom: 10px;
        display: flex; justify-content: space-between; align-items: center;
        box-shadow: 0 5px 15px rgba(0,0,0,0.3); border-left: 8px solid;
    }}
    .banner-win {{ background-color: rgba(46, 204, 113, 0.5) !important; border-color: #27ae60; }}
    .banner-loss {{ background-color: rgba(231, 76, 60, 0.5) !important; border-color: #c0392b; }}
    .banner-text-main {{ font-size: 1rem; font-weight: 800; color: white !important; }}
    .banner-text-sub {{ font-size: 0.8rem; opacity: 0.95; color: white !important; }}
    .banner-profit {{ font-size: 1.3rem; font-weight: 900; color: white !important; }}

    /* Competition Banner Base Styling */
    .comp-banner-wrapper {{
        border-radius: 15px; padding: 25px; 
        display: flex; align-items: center; justify-content: center;
        margin-bottom: 30px; box-shadow: 0 8px 30px rgba(0,0,0,0.4);
    }}
    .comp-logo {{ height: 90px; transition: all 0.3s ease; }}
    .comp-text {{ 
        font-size: 2.5rem; font-weight: 900; margin-left: 25px; 
        color: white; text-transform: uppercase; letter-spacing: 2px;
    }}

    /* --- MOBILE-ONLY CSS ENGINE --- */
    @media only screen and (max-width: 768px) {{
        /* 1. FORCE REMOVE TEXT IN BANNER */
        .comp-text {{ 
            display: none !important; 
            visibility: hidden !important;
            width: 0 !important;
            height: 0 !important;
        }}
        .comp-banner-wrapper {{
            padding: 15px !important;
            min-height: 100px !important;
        }}
        .comp-logo {{
            height: 70px !important;
            margin: 0 auto !important;
        }}
        
        /* 2. Scale Main Typography */
        h1 {{ font-size: 1.4rem !important; text-align: center !important; }}
        .live-br-text {{ font-size: 2.2rem !important; text-align: center !important; }}
        
        /* 3. Stack Metric Columns */
        [data-testid="column"] {{
            width: 100% !important;
            flex: 1 1 100% !important;
            margin-bottom: 12px !important;
        }}
        
        /* 4. Re-align Log Banners */
        .log-banner {{
            flex-direction: column !important;
            text-align: center !important;
            gap: 10px;
        }}
        .log-banner > div {{ width: 100% !important; }}
    }}
    </style>
""", unsafe_allow_html=True)

# --- 3. BACKEND LOGIC ---

def get_connection():
    try:
        gc = gspread.service_account_from_dict(st.secrets["service_account"])
        sh = gc.open_by_url(st.secrets["sheet_url"])
        ws = sh.get_worksheet(0)
        data = ws.get_all_records()
        try:
            br_val = ws.cell(1, 10).value
            base_br = float(str(br_val).replace(',', '')) if br_val else 5000.0
        except: base_br = 5000.0
        return data, ws, base_br
    except Exception as e:
        st.error(f"Sync Error: {e}"); return [], None, 5000.0

def process_data(raw_data):
    if not raw_data: return pd.DataFrame()
    processed = []
    cycle_trackers = {}
    
    for row in raw_data:
        try:
            comp = str(row.get('Competition', 'Brighton')).strip() or 'Brighton'
            if comp not in cycle_trackers: cycle_trackers[comp] = 0.0
            odds = float(str(row.get('Odds', 1)).replace(',', '.'))
            stake = float(str(row.get('Stake', 0)).replace(',', '')) if row.get('Stake') else 0.0
            win = "Draw (X)" in str(row.get('Result', ''))
            income = stake * odds if win else 0.0
            
            cycle_trackers[comp] += stake
            if win:
                cycle_profit = income - cycle_trackers[comp]
                cycle_trackers[comp] = 0.0
            else:
                cycle_profit = -stake
                
            processed.append({
                "Date": row.get('Date', ''), "Comp": comp,
                "Match": f"{row.get('Home Team','')} vs {row.get('Away Team','')}",
                "Odds": odds, "Expense": stake, "Income": income,
                "Cycle_Profit": cycle_profit, "Status": "✅ Won" if win else "❌ Lost"
            })
        except: continue
    return pd.DataFrame(processed)

# --- 4. EXECUTION ---
raw_rows, sheet_ws, initial_br = get_connection()
df = process_data(raw_rows)
live_br = initial_br + (df['Income'].sum() - df['Expense'].sum()) if not df.empty else initial_br

# --- 5. SIDEBAR ---
with st.sidebar:
    st.image(APP_LOGO, width=110)
    st.markdown("### WALLET CONTROL")
    st.metric("Base Bankroll", f"₪{initial_br:,.0f}")
    amt = st.number_input("Transaction", min_value=0.0, value=100.0, step=50.0, label_visibility="collapsed")
    c1, c2 = st.columns(2)
    if c1.button("Deposit", use_container_width=True): sheet_ws.update_cell(1, 10, initial_br + amt); st.rerun()
    if c2.button("Withdraw", use_container_width=True): sheet_ws.update_cell(1, 10, initial_br - amt); st.rerun()
    st.divider()
    view = st.selectbox("Navigation", ["🏆 Overview", "Brighton", "Africa Cup of Nations"], label_visibility="collapsed")
    if st.button("🔄 Sync Systems", use_container_width=True): st.rerun()

# --- 6. MAIN VIEWS ---

if view == "🏆 Overview":
    st.markdown("<h1 style='text-align: center; letter-spacing: 3px;'>CENTRAL COMMAND</h1>", unsafe_allow_html=True)
    st.markdown(f"<div class='live-br-text' style='text-align: center; font-size: 3.5rem; font-weight: 900;'>₪{live_br:,.2f}</div>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; opacity: 0.6;'>LIVE GLOBAL BANKROLL</p>", unsafe_allow_html=True)

    if not df.empty:
        summary = df.groupby('Comp').agg({'Match': 'count', 'Expense': 'sum', 'Income': 'sum', 'Status': lambda x: (x == '✅ Won').sum()}).reset_index()
        summary['Net Profit'] = summary['Income'] - summary['Expense']
        col1, col2, col3 = st.columns(3)
        p_col = "#2ecc71" if summary['Net Profit'].sum() >= 0 else "#e74c3c"
        with col1: st.markdown(f'<div class="custom-metric-card"><div class="c-label">Total Profit</div><div class="c-value" style="color:{p_col}!important">₪{summary["Net Profit"].sum():,.0f}</div></div>', unsafe_allow_html=True)
        with col2: st.markdown(f'<div class="custom-metric-card"><div class="c-label">Total Games</div><div class="c-value">{summary["Match"].sum()}</div></div>', unsafe_allow_html=True)
        with col3: 
            rate = (summary['Status'].sum() / summary['Match'].sum() * 100) if summary['Match'].sum() > 0 else 0
            st.markdown(f'<div class="custom-metric-card"><div class="c-label">Success Rate</div><div class="c-value">{rate:.1f}%</div></div>', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        st.dataframe(summary[['Comp', 'Match', 'Status', 'Net Profit']].rename(columns={'Comp': 'Track', 'Status': 'Wins'}), use_container_width=True, hide_index=True)

else:
    # SPECIFIC TRACK VIEW
    logos = {"Brighton": "https://i.postimg.cc/x8kdQh5H/Brighton_Hove_Albion_logo.png", "Africa Cup of Nations": "https://i.postimg.cc/5yHtJTgz/2025_Africa_Cup_of_Nations_logo.png"}
    grad = "linear-gradient(90deg, #4CABFF, #E6F7FF)" if view == "Brighton" else "linear-gradient(90deg, #CE1126, #FCD116, #007A33)"
    t_color = "#004085" if view == "Brighton" else "white"

    # THE RE-ENGINEERED UX BANNER
    st.markdown(f"""
        <div class="comp-banner-wrapper" style="background: {grad};">
            <img src="{logos[view]}" class="comp-logo">
            <div class="comp-text" style="color: {t_color} !important;">{view}</div>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"<div class='live-br-text' style='text-align: center; font-size: 3rem; font-weight: 800;'>₪{live_br:,.2f}</div>", unsafe_allow_html=True)
    
    f_df = df[df['Comp'] == view].copy() if not df.empty else pd.DataFrame()
    t_net = f_df['Income'].sum() - f_df['Expense'].sum() if not f_df.empty else 0.0

    mc1, mc2, mc3 = st.columns(3)
    with mc1: st.markdown(f'<div class="custom-metric-card"><div class="c-label">Expenses</div><div class="c-value">₪{f_df["Expense"].sum():,.0f}</div></div>', unsafe_allow_html=True)
    with mc2: st.markdown(f'<div class="custom-metric-card"><div class="c-label">Revenue</div><div class="c-value">₪{f_df["Income"].sum():,.0f}</div></div>', unsafe_allow_html=True)
    with mc3: 
        n_c = "#2ecc71" if t_net >= 0 else "#e74c3c"
        st.markdown(f'<div class="custom-metric-card"><div class="c-label">Profit</div><div class="c-value" style="color:{n_c}!important">₪{t_net:,.0f}</div></div>', unsafe_allow_html=True)

    col_f, col_g = st.columns([1, 1.2])
    with col_f:
        with st.form("new_entry"):
            st.markdown("<h3 style='color:black!important;text-shadow:none!important;'>Add Match</h3>", unsafe_allow_html=True)
            h, a = st.text_input("Home", value="Brighton" if view == "Brighton" else ""), st.text_input("Away")
            o, s = st.number_input("Odds", value=3.2, step=0.1), st.number_input("Stake", value=30.0)
            r = st.radio("Outcome", ["Draw (X)", "No Draw"], horizontal=True)
            if st.form_submit_button("SUBMIT GAME", use_container_width=True):
                sheet_ws.append_row([str(datetime.date.today()), view, h, a, o, r, s, 0.0]); st.rerun()

    with col_g:
        if not f_df.empty:
            f_df['Equity'] = initial_br + (f_df['Income'].cumsum() - f_df['Expense'].cumsum())
            fig_l = px.line(f_df, y='Equity', x=f_df.index)
            fig_l.update_traces(line_color='#00ff88', line_width=4)
            fig_l.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0.1)', font=dict(color='white'), height=240, margin=dict(l=0,r=0,t=10,b=0))
            st.plotly_chart(fig_l, use_container_width=True)

    st.markdown("<h3 style='margin-top:20px;'>📜 Activity Log</h3>", unsafe_allow_html=True)
    if not f_df.empty:
        for _, row in f_df.sort_index(ascending=False).iterrows():
            is_win = "✅ Won" in row['Status']
            bg_c = "banner-win" if is_win else "banner-loss"
            st.markdown(f"""
                <div class="log-banner {bg_c}">
                    <div>
                        <div class="banner-text-main">{row['Match']}</div>
                        <div class="banner-text-sub">{row['Date']} | Odds: {row['Odds']:.2f}</div>
                    </div>
                    <div style="text-align: center;">
                        <div class="banner-text-sub">Stake: ₪{row['Expense']:,.0f} | Gross: ₪{row['Income']:,.0f}</div>
                    </div>
                    <div style="text-align: right;">
                        <div class="banner-text-sub">{"Cycle Profit" if is_win else "Step Loss"}</div>
                        <div class="banner-profit">₪{row['Cycle_Profit']:,.0f}</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)