import streamlit as st
import pandas as pd
import plotly.express as px
import gspread
import datetime

# --- 1. SETUP & CONFIGURATION ---
APP_LOGO = "https://i.postimg.cc/8Cr6SypK/yzwb-ll-sm.png"
BG_IMAGE = "https://i.postimg.cc/GmFZ4KS7/Gemini-Generated-Image-k1h11zk1h11zk1h1.png"
SIDEBAR_IMAGE = "https://i.postimg.cc/NfdK3hck/'yzwb-ll'-sm-(1).png"

st.set_page_config(
    page_title="GoalMetric Elite Dashboard",
    layout="wide",
    page_icon=APP_LOGO,
    initial_sidebar_state="expanded"
)

# --- 2. PROFESSIONAL UI STYLING (CSS) ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;700;900&display=swap');
    
    /* Global Cleanup */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    [data-testid="stDecoration"] {{display: none;}}
    header[data-testid="stHeader"] {{background: transparent !important;}}
    
    /* Fix: Arrows & Tooltip Artifacts ('keyb') */
    button[title="Collapse sidebar"] {{ color: black !important; }}
    [data-testid="stSidebarCollapsedControl"] {{
        background-color: rgba(0, 0, 0, 0.6) !important;
        border-radius: 50% !important;
        width: 45px !important; height: 45px !important;
        display: flex !important; align-items: center !important; justify-content: center !important;
        margin: 10px !important;
    }}
    [data-testid="stSidebarCollapsedControl"] svg {{ fill: white !important; width: 25px !important; }}
    .stTooltipIcon {{ display: none !important; }}

    /* Main Container & Background */
    [data-testid="stAppViewContainer"] {{
        background-image: linear-gradient(rgba(0, 0, 0, 0.75), rgba(0, 0, 0, 0.75)), url("{BG_IMAGE}");
        background-attachment: fixed; background-size: cover;
    }}

    /* Sidebar Fixes */
    [data-testid="stSidebar"] {{
        background-color: rgba(255, 255, 255, 0.85) !important;
        border-right: 1px solid rgba(255,255,255,0.2);
    }}
    [data-testid="stSidebar"]::before {{
        content: ""; position: absolute; top: 0; left: 0; width: 100%; height: 100%;
        background-image: url("{SIDEBAR_IMAGE}"); background-size: cover;
        filter: blur(4px); z-index: -1;
    }}
    [data-testid="stSidebar"] * {{ color: #000000 !important; font-family: 'Montserrat', sans-serif; }}

    /* Main Content Typography */
    .main h1, .main h2, .main h3, .main p, .main span, .main label {{
        color: #ffffff !important; text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
    }}
    
    /* Metrics & Components */
    .custom-card {{
        background-color: rgba(255, 255, 255, 0.95);
        border-radius: 15px; padding: 20px; text-align: center;
        box-shadow: 0 8px 32px rgba(0,0,0,0.3);
    }}
    .metric-label {{ color: #444 !important; font-weight: 700; font-size: 12px; text-transform: uppercase; }}
    .metric-value {{ color: #1b4332 !important; font-weight: 900; font-size: 28px; }}

    /* Tables & Forms */
    [data-testid="stDataFrame"] {{ background-color: white !important; border-radius: 10px; }}
    [data-testid="stDataFrame"] * {{ color: black !important; text-shadow: none !important; }}
    [data-testid="stForm"] {{ background-color: rgba(255, 255, 255, 0.9); border-radius: 15px; }}
    [data-testid="stForm"] * {{ color: black !important; text-shadow: none !important; }}

    </style>
""", unsafe_allow_html=True)

# --- 3. BACKEND CORE LOGIC ---

def fetch_and_validate_data():
    """Brings data from Sheets and performs a structural audit."""
    try:
        gc = gspread.service_account_from_dict(st.secrets["service_account"])
        sh = gc.open_by_url(st.secrets["sheet_url"])
        ws = sh.get_worksheet(0)
        raw_rows = ws.get_all_records()
        
        # Base Bankroll Audit
        try:
            br_val = ws.cell(1, 10).value
            base_br = float(str(br_val).replace(',', '')) if br_val else 5000.0
        except: base_br = 5000.0
        
        return raw_rows, ws, base_br
    except Exception as e:
        st.error(f"Backend Connection Error: {e}")
        return [], None, 5000.0

def process_engine(raw_data, br_start, af_start):
    """Refactored calculation engine for cycle betting logic."""
    processed = []
    # Dynamic track management
    registry = {
        "Brighton": {"base": float(br_start), "invested": 0.0},
        "Africa Cup of Nations": {"base": float(af_start), "invested": 0.0}
    }

    for row in raw_data:
        comp = str(row.get('Competition', 'Brighton')).strip() or 'Brighton'
        if comp not in registry: 
            registry[comp] = {"base": 30.0, "invested": 0.0}
        
        try: odds = float(str(row.get('Odds', 1)).replace(',', '.'))
        except: odds = 1.0
        
        # Cycle investment logic
        try:
            stake = row.get('Stake')
            # If stake is empty, use current recovery bet, else use manual entry
            if stake in [None, '', ' ']:
                # Dynamic recovery logic could go here, for now using current cycle step
                current_stake = 30.0 # Placeholder
            else:
                current_stake = float(str(stake).replace(',', ''))
        except: current_stake = 30.0

        res = str(row.get('Result', '')).strip()
        registry[comp]['invested'] += current_stake
        is_win = "Draw (X)" in res
        
        if is_win:
            income = current_stake * odds
            net_cycle = income - registry[comp]['invested']
            # Reset Cycle
            registry[comp]['invested'] = 0.0
            status = "✅ Won"
        else:
            income = 0.0
            net_cycle = -current_stake
            status = "❌ Lost"
            
        processed.append({
            "Date": row.get('Date', ''), "Comp": comp, 
            "Match": f"{row.get('Home Team','')} vs {row.get('Away Team','')}",
            "Odds": odds, "Expense": current_stake, "Income": income, 
            "Net": net_cycle, "Status": status
        })
    return processed

# --- 4. EXECUTION FLOW ---
raw_data, sheet_conn, base_bankroll = fetch_and_validate_data()
processed_data = process_engine(raw_data, 30.0, 20.0)

if processed_data:
    df = pd.DataFrame(processed_data)
    # Global Bankroll Calculation (Revenue - Expense)
    live_profit = df['Income'].sum() - df['Expense'].sum()
    current_wallet = base_bankroll + live_profit
else:
    df = pd.DataFrame(columns=["Comp", "Expense", "Income", "Status", "Match"])
    current_wallet = base_bankroll

# --- 5. UI COMPONENTS ---

# SIDEBAR NAV
with st.sidebar:
    st.image(APP_LOGO, width=120)
    st.markdown("### WALLET")
    st.metric("Base Bankroll", f"₪{base_bankroll:,.0f}")
    amt = st.number_input("Transaction Amount", min_value=0.0, value=100.0, step=50.0, label_visibility="collapsed")
    c1, c2 = st.columns(2)
    if c1.button("Deposit", use_container_width=True):
        sheet_conn.update_cell(1, 10, base_bankroll + amt)
        st.rerun()
    if c2.button("Withdraw", use_container_width=True):
        sheet_conn.update_cell(1, 10, base_bankroll - amt)
        st.rerun()
    st.divider()
    view = st.selectbox("Navigation", ["🏆 Overview", "Brighton", "Africa Cup of Nations"], label_visibility="collapsed")
    if st.button("🔄 Sync Systems", use_container_width=True): st.rerun()

# MAIN RENDERING
if view == "🏆 Overview":
    st.markdown("<h1 style='text-align: center; letter-spacing: 5px;'>COMMAND CENTER</h1>", unsafe_allow_html=True)
    st.markdown(f"<h2 style='text-align: center; font-size: 3.5rem;'>₪{current_wallet:,.2f}</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; opacity: 0.7;'>AGGREGATED GLOBAL POSITION</p>", unsafe_allow_html=True)

    if not df.empty:
        # PURE AGGREGATION LOGIC (NO ROW SUMS FOR PROFIT)
        summary = df.groupby('Comp').agg({
            'Match': 'count',
            'Expense': 'sum',
            'Income': 'sum',
            'Status': lambda x: (x == '✅ Won').sum()
        }).reset_index()
        
        summary.columns = ['Competition', 'Games', 'Total_Out', 'Total_In', 'Wins']
        summary['Actual_Profit'] = summary['Total_In'] - summary['Total_Out']
        summary['Win_Rate'] = (summary['Wins'] / summary['Games'] * 100).map("{:.1f}%".format)

        total_p = summary['Actual_Profit'].sum()
        col1, col2, col3 = st.columns(3)
        p_color = "#2d6a4f" if total_p >= 0 else "#d32f2f"
        
        col1.markdown(f'<div class="custom-card"><div class="metric-label">All-Time Net</div><div class="metric-value" style="color:{p_color} !important">₪{total_p:,.0f}</div></div>', unsafe_allow_html=True)
        col2.markdown(f'<div class="custom-card"><div class="metric-label">Total Volume</div><div class="metric-value">{summary["Games"].sum()}</div></div>', unsafe_allow_html=True)
        col3.markdown(f'<div class="custom-card"><div class="metric-label">System Health</div><div class="metric-value">{(summary["Wins"].sum()/summary["Games"].sum()*100):.1f}%</div></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        ch, tb = st.columns([1, 1.2])
        with ch:
            fig = px.bar(summary, x='Competition', y='Actual_Profit', color='Actual_Profit', color_continuous_scale=['#d32f2f', '#2d6a4f'])
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0.1)', font=dict(color='white'), height=350, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        with tb:
            st.dataframe(summary[['Competition', 'Games', 'Wins', 'Win_Rate', 'Actual_Profit']].rename(columns={'Actual_Profit': 'Net Profit'}), use_container_width=True, hide_index=True)

else:
    # TRACK VIEW
    logos = {"Brighton": "https://i.postimg.cc/x8kdQh5H/Brighton_Hove_Albion_logo.png", "Africa Cup of Nations": "https://i.postimg.cc/5yHtJTgz/2025_Africa_Cup_of_Nations_logo.png"}
    grad = "linear-gradient(90deg, #4CABFF, #E6F7FF)" if view == "Brighton" else "linear-gradient(90deg, #CE1126, #FCD116, #007A33)"
    
    st.markdown(f'<div style="background:{grad}; border-radius:15px; padding:25px; display:flex; align-items:center; margin-bottom:40px;"><img src="{logos[view]}" style="height:80px; margin-right:30px;"><h1 style="color:{"#004085" if view=="Brighton" else "white"} !important; margin:0;">{view.upper()}</h1></div>', unsafe_allow_html=True)
    
    f_df = df[df['Comp'] == view].copy() if not df.empty else pd.DataFrame()
    t_exp = f_df['Expense'].sum()
    t_inc = f_df['Income'].sum()
    t_net = t_inc - t_exp

    mc1, mc2, mc3 = st.columns(3)
    mc1.markdown(f'<div class="custom-card"><div class="metric-label">Expenditure</div><div class="metric-value">₪{t_exp:,.0f}</div></div>', unsafe_allow_html=True)
    mc2.markdown(f'<div class="custom-card"><div class="metric-label">Revenue</div><div class="metric-value">₪{t_inc:,.0f}</div></div>', unsafe_allow_html=True)
    n_color = "#2d6a4f" if t_net >= 0 else "#d32f2f"
    mc3.markdown(f'<div class="custom-card"><div class="metric-label">Net Return</div><div class="metric-value" style="color:{n_color} !important">₪{t_net:,.0f}</div></div>', unsafe_allow_html=True)

    st.markdown(f"<h2 style='text-align:center; margin-top:30px;'>Performance Analysis</h2>", unsafe_allow_html=True)
    
    c_form, c_chart = st.columns([1, 1.2])
    with c_form:
        with st.form("entry"):
            st.subheader("Register New Match")
            h = st.text_input("Home", value="Brighton" if view == "Brighton" else "")
            a = st.text_input("Away")
            o = st.number_input("Odds", value=3.2, step=0.1)
            s = st.number_input("Stake", value=30.0)
            r = st.radio("Outcome", ["Draw (X)", "No Draw"], horizontal=True)
            if st.form_submit_button("COMMIT TO CLOUD", use_container_width=True):
                sheet_conn.append_row([str(datetime.date.today()), view, h, a, o, r, s, 0.0])
                st.rerun()

    with c_chart:
        if not f_df.empty:
            f_df['Equity'] = base_bankroll + (f_df['Income'].cumsum() - f_df['Expense'].cumsum())
            fig_track = px.line(f_df, y='Equity', x=f_df.index, labels={'Equity': 'Bankroll', 'index': 'Game #'})
            fig_track.update_traces(line_color='#00ff88', line_width=4)
            fig_track.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0.1)', font=dict(color='white'), height=300)
            st.plotly_chart(fig_track, use_container_width=True)
            wins = len(f_df[f_df['Status'] == "✅ Won"])
            st.caption(f"Success Rate: {(wins/len(f_df)*100):.1f}% | Total Games: {len(f_df)}")

    st.markdown("### 📜 ACTIVE ACTIVITY LOG")
    if not f_df.empty:
        st.dataframe(f_df[['Date', 'Match', 'Odds', 'Expense', 'Net', 'Status']].sort_index(ascending=False), use_container_width=True, hide_index=True)

with st.expander("🛠️ SYSTEM CONTROL PANEL"):
    st.write("Current Backend Status: **ACTIVE**")
    if st.button("Rollback Last Entry"):
        sheet_conn.delete_rows(len(raw_data) + 1)
        st.rerun()