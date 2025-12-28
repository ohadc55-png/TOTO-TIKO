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

# --- 2. ADVANCED CSS (FIXES ARROWS, HEADERS & BANNERS) ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;700;900&display=swap');
    
    /* 1. Global Reset */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    [data-testid="stDecoration"] {{display: none;}}
    header[data-testid="stHeader"] {{ background: transparent !important; }}
    
    /* 2. Arrow & Tooltip Fix */
    [data-testid="stSidebarCollapsedControl"] {{
        background-color: rgba(0, 0, 0, 0.6) !important;
        border-radius: 50% !important;
        width: 45px !important; height: 45px !important;
        display: flex !important; align-items: center !important; justify-content: center !important;
        margin: 10px !important;
    }}
    [data-testid="stSidebarCollapsedControl"] svg {{ fill: white !important; }}
    [data-testid="stTooltipContent"], .stTooltipIcon {{ display: none !important; }}
    
    [data-testid="stSidebar"] button[kind="header"] svg {{ fill: #000000 !important; }}

    /* 3. Backgrounds */
    [data-testid="stAppViewContainer"] {{
        background-image: linear-gradient(rgba(0, 0, 0, 0.7), rgba(0, 0, 0, 0.7)), url("{BG_IMAGE}");
        background-attachment: fixed; background-size: cover; background-position: center;
    }}
    [data-testid="stSidebar"] {{
        background-color: rgba(255, 255, 255, 0.85) !important;
        border-right: 1px solid rgba(255,255,255,0.2);
    }}
    [data-testid="stSidebar"]::before {{
        content: ""; position: absolute; top: 0; left: 0; width: 100%; height: 100%;
        background-image: url("{SIDEBAR_BG}"); background-size: cover;
        filter: blur(4px); z-index: -1;
    }}

    /* 4. Typography & Visibility */
    .main h1, .main h2, .main h3, .main p, .main span, .main label {{
        color: #ffffff !important;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.8);
        font-family: 'Montserrat', sans-serif;
    }}
    [data-testid="stSidebar"] * {{ color: #000000 !important; text-shadow: none !important; }}
    [data-testid="stCaptionContainer"] {{ color: #ffffff !important; font-weight: 700 !important; font-size: 1.1rem !important; }}

    /* 5. Component Styling */
    .custom-metric-card {{
        background-color: rgba(255, 255, 255, 0.95);
        border-radius: 15px; padding: 20px; text-align: center;
        box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    }}
    .c-label {{ color: #555 !important; font-weight: 700; font-size: 12px; text-transform: uppercase; }}
    .c-value {{ color: #1b4332 !important; font-weight: 900; font-size: 26px; }}

    [data-testid="stForm"] {{ background-color: rgba(255, 255, 255, 0.95); border-radius: 15px; padding: 20px; }}
    [data-testid="stForm"] * {{ color: black !important; }}

    /* 6. Activity Log Banners (50% Opacity) */
    .log-banner {{
        padding: 15px 25px;
        border-radius: 12px;
        margin-bottom: 12px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.4);
        border-left: 8px solid;
    }}
    .banner-win {{
        background-color: rgba(46, 204, 113, 0.5) !important; /* 50% Green */
        border-color: #27ae60;
    }}
    .banner-loss {{
        background-color: rgba(231, 76, 60, 0.5) !important; /* 50% Red */
        border-color: #c0392b;
    }}
    .banner-text-main {{ font-size: 1.1rem; font-weight: 800; color: white !important; }}
    .banner-text-sub {{ font-size: 0.85rem; opacity: 0.9; color: white !important; }}
    .banner-profit {{ font-size: 1.4rem; font-weight: 900; color: white !important; }}

    @media only screen and (max-width: 768 {{
        .banner-text {{ display: none !important; }}
    }}
    </style>
""", unsafe_allow_html=True)

# --- 3. DATA & LOGIC ENGINE (BACKEND) ---

def get_connection():
    try:
        gc = gspread.service_account_from_dict(st.secrets["service_account"])
        sh = gc.open_by_url(st.secrets["sheet_url"])
        ws = sh.get_worksheet(0)
        data = ws.get_all_records()
        try:
            br_cell = ws.cell(1, 10).value
            base_br = float(str(br_cell).replace(',', '')) if br_cell else 5000.0
        except: base_br = 5000.0
        return data, ws, base_br
    except Exception as e:
        st.error(f"Sync Error: {e}")
        return [], None, 5000.0

def process_data(raw_data):
    """Processes raw sheets data with Martingale Cycle Logic."""
    if not raw_data: return pd.DataFrame()
    processed = []
    
    # Dictionary to track cumulative stake per competition until a win
    cycle_trackers = {}
    
    for row in raw_data:
        try:
            comp = str(row.get('Competition', 'Brighton')).strip() or 'Brighton'
            if comp not in cycle_trackers:
                cycle_trackers[comp] = 0.0
                
            odds = float(str(row.get('Odds', 1)).replace(',', '.'))
            stake = float(str(row.get('Stake', 0)).replace(',', '')) if row.get('Stake') else 0.0
            res = str(row.get('Result', '')).strip()
            
            is_win = "Draw (X)" in res
            income = stake * odds if is_win else 0.0
            
            # Update cycle tracker
            cycle_trackers[comp] += stake
            
            if is_win:
                # Cycle profit = Total revenue from this bet minus all stakes in this cycle
                cycle_profit = income - cycle_trackers[comp]
                cycle_trackers[comp] = 0.0  # Reset cycle
            else:
                # Still in cycle, current profit for this specific step is a loss
                cycle_profit = -stake
            
            processed.append({
                "Date": row.get('Date', ''),
                "Comp": comp,
                "Match": f"{row.get('Home Team','')} vs {row.get('Away Team','')}",
                "Odds": odds,
                "Expense": stake,
                "Income": income,
                "Cycle_Profit": cycle_profit,
                "Status": "✅ Won" if is_win else "❌ Lost"
            })
        except: continue
    return pd.DataFrame(processed)

# --- 4. EXECUTION FLOW ---
raw_rows, sheet_ws, initial_bankroll = get_connection()
df = process_data(raw_rows)

if not df.empty:
    net_change = df['Income'].sum() - df['Expense'].sum()
    live_bankroll = initial_bankroll + net_change
else:
    live_bankroll = initial_bankroll

# --- 5. UI COMPONENTS ---

# SIDEBAR
with st.sidebar:
    st.image(APP_LOGO, width=120)
    st.markdown("### WALLET CONTROL")
    st.metric("Base Bankroll", f"₪{initial_bankroll:,.0f}")
    amt = st.number_input("Transaction", min_value=0.0, value=100.0, step=50.0, label_visibility="collapsed")
    c1, c2 = st.columns(2)
    if c1.button("Deposit", use_container_width=True):
        sheet_ws.update_cell(1, 10, initial_bankroll + amt)
        st.rerun()
    if c2.button("Withdraw", use_container_width=True):
        sheet_ws.update_cell(1, 10, initial_bankroll - amt)
        st.rerun()
    st.divider()
    view = st.selectbox("Navigation", ["🏆 Overview", "Brighton", "Africa Cup of Nations"], label_visibility="collapsed")
    if st.button("🔄 Sync Systems", use_container_width=True): st.rerun()

# MAIN VIEW SWITCHER
if view == "🏆 Overview":
    st.markdown("<h1 style='text-align: center;'>CENTRAL COMMAND</h1>", unsafe_allow_html=True)
    st.markdown(f"<h2 style='text-align: center; font-size: 3rem;'>₪{live_bankroll:,.2f}</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; opacity: 0.7;'>AGGREGATED GLOBAL POSITION</p>", unsafe_allow_html=True)

    if not df.empty:
        summary = df.groupby('Comp').agg({
            'Match': 'count',
            'Expense': 'sum',
            'Income': 'sum',
            'Status': lambda x: (x == '✅ Won').sum()
        }).reset_index()
        
        summary['Net Profit'] = summary['Income'] - summary['Expense']
        summary['Win Rate'] = (summary['Status'] / summary['Match'] * 100).map("{:.1f}%".format)
        
        total_p = summary['Net Profit'].sum()
        p_color = "#2ecc71" if total_p >= 0 else "#e74c3c"

        col1, col2, col3 = st.columns(3)
        with col1: st.markdown(f'<div class="custom-metric-card"><div class="c-label">Total Profit</div><div class="c-value" style="color:{p_color}!important">₪{total_p:,.0f}</div></div>', unsafe_allow_html=True)
        with col2: st.markdown(f'<div class="custom-metric-card"><div class="c-label">Total Games</div><div class="c-value">{summary["Match"].sum()}</div></div>', unsafe_allow_html=True)
        with col3: 
            avg_rate = (summary['Status'].sum() / summary['Match'].sum() * 100)
            st.markdown(f'<div class="custom-metric-card"><div class="c-label">Global Health</div><div class="c-value">{avg_rate:.1f}%</div></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        ch, tb = st.columns([1, 1.2])
        with ch:
            st.subheader("Distribution")
            fig = px.bar(summary, x='Comp', y='Net Profit', color='Net Profit', color_continuous_scale=['#e74c3c', '#2ecc71'])
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0.1)', font=dict(color='white'), height=350, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        with tb:
            st.subheader("Track Performance")
            # In Overview we keep the dataframe for clean summary
            st.dataframe(summary[['Comp', 'Match', 'Status', 'Win Rate', 'Net Profit']].rename(columns={'Comp': 'Competition', 'Status': 'Wins'}), use_container_width=True, hide_index=True)
    else:
        st.info("No data found in cloud storage.")

else:
    # SPECIFIC TRACK VIEW
    logos = {"Brighton": "https://i.postimg.cc/x8kdQh5H/Brighton_Hove_Albion_logo.png", "Africa Cup of Nations": "https://i.postimg.cc/5yHtJTgz/2025_Africa_Cup_of_Nations_logo.png"}
    grad = "linear-gradient(90deg, #4CABFF, #E6F7FF)" if view == "Brighton" else "linear-gradient(90deg, #CE1126, #FCD116, #007A33)"
    
    st.markdown(f'<div class="banner-container" style="background:{grad}; border-radius:15px; padding:25px; display:flex; align-items:center; margin-bottom:40px;"><img src="{logos[view]}" style="height:80px; margin-right:30px;"><h1 style="color:{"#004085" if view=="Brighton" else "white"} !important; margin:0;">{view.upper()}</h1></div>', unsafe_allow_html=True)
    
    st.markdown(f"<h2 style='text-align: center;'>₪{live_bankroll:,.2f}</h2><p style='text-align: center; opacity: 0.7;'>LIVE BANKROLL</p>", unsafe_allow_html=True)

    f_df = df[df['Comp'] == view].copy() if not df.empty else pd.DataFrame()
    t_net = f_df['Income'].sum() - f_df['Expense'].sum() if not f_df.empty else 0.0

    mc1, mc2, mc3 = st.columns(3)
    with mc1: st.markdown(f'<div class="custom-metric-card"><div class="c-label">Total Invested</div><div class="c-value">₪{f_df["Expense"].sum() if not f_df.empty else 0:,.0f}</div></div>', unsafe_allow_html=True)
    with mc2: st.markdown(f'<div class="custom-metric-card"><div class="c-label">Total Revenue</div><div class="c-value">₪{f_df["Income"].sum() if not f_df.empty else 0:,.0f}</div></div>', unsafe_allow_html=True)
    with mc3: 
        nc_col = "#2ecc71" if t_net >= 0 else "#e74c3c"
        st.markdown(f'<div class="custom-metric-card"><div class="c-label">Net Profit</div><div class="c-value" style="color:{nc_col}!important">₪{t_net:,.0f}</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    col_f, col_g = st.columns([1, 1.2])
    
    with col_f:
        with st.form("new_entry"):
            st.subheader("Add Match")
            h = st.text_input("Home", value="Brighton" if view == "Brighton" else "")
            a = st.text_input("Away")
            o = st.number_input("Odds", value=3.2, step=0.1)
            s = st.number_input("Stake", value=30.0)
            r = st.radio("Outcome", ["Draw (X)", "No Draw"], horizontal=True)
            if st.form_submit_button("SUBMIT GAME", use_container_width=True):
                sheet_ws.append_row([str(datetime.date.today()), view, h, a, o, r, s, 0.0])
                st.rerun()

    with col_g:
        st.subheader("Performance")
        if not f_df.empty:
            f_df['Equity'] = initial_bankroll + (f_df['Income'].cumsum() - f_df['Expense'].cumsum())
            fig_l = px.line(f_df, y='Equity', x=f_df.index)
            fig_l.update_traces(line_color='#00ff88', line_width=4)
            fig_l.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0.1)', font=dict(color='white'), height=280, margin=dict(l=0,r=0,t=0,b=0))
            st.plotly_chart(fig_l, use_container_width=True)
            wins = len(f_df[f_df['Status'] == "✅ Won"])
            st.caption(f"Success Rate: {(wins/len(f_df)*100):.1f}% ({wins} W / {len(f_df)-wins} L)")

    st.markdown("### 📜 Activity Log")
    if not f_df.empty:
        # Loop through rows to create Banners
        for index, row in f_df.sort_index(ascending=False).iterrows():
            is_win = "✅ Won" in row['Status']
            bg_class = "banner-win" if is_win else "banner-loss"
            
            st.markdown(f"""
                <div class="log-banner {bg_class}">
                    <div style="flex: 2;">
                        <div class="banner-text-main">{row['Match']}</div>
                        <div class="banner-text-sub">{row['Date']} | Odds: {row['Odds']:.2f}</div>
                    </div>
                    <div style="flex: 1.5; text-align: center;">
                        <div class="banner-text-sub">Stake: ₪{row['Expense']:,.0f}</div>
                        <div class="banner-text-sub">Gross: ₪{row['Income']:,.0f}</div>
                    </div>
                    <div style="flex: 1.5; text-align: right;">
                        <div class="banner-text-sub">{"Cycle Profit" if is_win else "Step Loss"}</div>
                        <div class="banner-profit">₪{row['Cycle_Profit']:,.0f}</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

with st.expander("🛠️ Admin Console"):
    if st.button("Undo Last Entry"):
        sheet_ws.delete_rows(len(raw_rows) + 1)
        st.rerun()