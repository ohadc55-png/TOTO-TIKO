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

# --- 2. CSS STYLING (HIGH CONTRAST & VISIBILITY) ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;900&display=swap');
    
    /* 1. GLOBAL RESET */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header[data-testid="stHeader"] {{ background: transparent !important; }}
    
    /* 2. ARROW CONTROLS (Icon Only) */
    button[aria-label="Open sidebar"] {{
        background-color: rgba(0, 0, 0, 0.8) !important;
        border: 1px solid rgba(255,255,255,0.3);
        border-radius: 12px;
        width: 45px; height: 45px;
        margin-top: 20px;
        color: transparent !important; /* Hide text */
        font-size: 0px !important;
    }}
    button[aria-label="Open sidebar"] svg {{ fill: white !important; width: 24px; height: 24px; }}
    
    button[aria-label="Collapse sidebar"] {{ font-size: 0px !important; color: transparent !important; }}
    button[aria-label="Collapse sidebar"] svg {{ fill: black !important; width: 24px; height: 24px; }}
    .stTooltipIcon {{ display: none !important; }}

    /* 3. MAIN AREA TEXT (WHITE WITH SHADOW) */
    .main h1, .main h2, .main h3, .main p, .main span, .main label, 
    .main div[data-testid="stMarkdownContainer"] p {{
        color: #ffffff !important;
        text-shadow: 0px 2px 4px rgba(0,0,0,0.9);
        font-family: 'Montserrat', sans-serif;
    }}
    /* Metrics */
    [data-testid="stMetricValue"] {{ color: #ffffff !important; text-shadow: 0px 2px 5px rgba(0,0,0,1); }}
    [data-testid="stMetricLabel"] {{ color: #dddddd !important; }}

    /* 4. FORM / ADD MATCH BANNER */
    [data-testid="stForm"] {{
        background: rgba(255, 255, 255, 0.15);
        backdrop-filter: blur(15px);
        border: 1px solid rgba(255,255,255,0.3);
        border-radius: 16px;
        padding: 25px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.5);
    }}
    /* Form Labels */
    [data-testid="stForm"] label p {{
        color: #ffffff !important;
        font-weight: 700 !important;
    }}

    /* 5. INPUT FIELDS (WHITE BG, BLACK TEXT) */
    .stTextInput input, .stNumberInput input {{
        background-color: #ffffff !important;
        color: #000000 !important;
        border: 2px solid #ddd !important;
        font-weight: bold;
        border-radius: 8px;
    }}
    /* Dropdown/Radio */
    div[data-baseweb="select"] > div {{ background-color: #ffffff !important; color: black !important; }}
    div[data-baseweb="radio"] label p {{ color: white !important; font-weight: bold; }}

    /* 6. SIDEBAR (LIGHT THEME) */
    [data-testid="stSidebar"] {{ background-color: rgba(255, 255, 255, 0.95); }}
    [data-testid="stSidebar"]::before {{
        content: ""; position: absolute; top: 0; left: 0; width: 100%; height: 100%;
        background-image: url("{SIDEBAR_BG}"); background-size: cover;
        filter: blur(5px); z-index: -1;
    }}
    [data-testid="stSidebar"] * {{ color: #000000 !important; text-shadow: none !important; }}
    [data-testid="stSidebar"] input {{ border: 1px solid #999 !important; }}

    /* 7. CUSTOM BANNERS */
    .banner-container {{
        background: rgba(255, 255, 255, 0.95);
        border-radius: 12px;
        padding: 15px 20px;
        margin-bottom: 15px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.5);
        border-left: 12px solid #333;
    }}
    /* Force text inside banners to be black */
    .banner-container span, .banner-container div {{
        color: #000000 !important;
        text-shadow: none !important;
    }}
    
    .status-win {{ border-left-color: #2d6a4f; background: linear-gradient(90deg, #e6fffa, #ffffff); }}
    .status-loss {{ border-left-color: #d32f2f; background: linear-gradient(90deg, #fff5f5, #ffffff); }}

    /* 8. METRIC BOXES */
    .metric-box {{
        background-color: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(5px);
        border: 1px solid rgba(255,255,255,0.2);
        border-radius: 15px;
        padding: 20px;
        text-align: center;
    }}
    .m-lbl {{ font-size: 0.8rem; font-weight: bold; color: #ddd !important; text-transform: uppercase; }}
    .m-val {{ font-size: 1.8rem; font-weight: 900; color: white !important; }}

    /* BACKGROUND */
    [data-testid="stAppViewContainer"] {{
        background-image: linear-gradient(rgba(0, 0, 0, 0.75), rgba(0, 0, 0, 0.75)), url("{BG_IMAGE}");
        background-attachment: fixed; background-size: cover; background-position: center;
    }}
    /* Hide Default Table */
    [data-testid="stDataFrame"] {{ display: none; }} 
    </style>
""", unsafe_allow_html=True)

# --- 3. BACKEND LOGIC (CYCLE ENGINE) ---
def connect_db():
    try:
        gc = gspread.service_account_from_dict(st.secrets["service_account"])
        sh = gc.open_by_url(st.secrets["sheet_url"])
        ws = sh.get_worksheet(0)
        data = ws.get_all_records()
        try: br = float(str(ws.cell(1, 10).value).replace(',', '')) if ws.cell(1, 10).value else 5000.0
        except: br = 5000.0
        return data, ws, br
    except Exception as e:
        st.error(f"Error: {e}"); return [], None, 5000.0

def process_logic(raw):
    if not raw: return pd.DataFrame()
    rows = []
    
    # Track accumulated loss per competition
    cycle_tracker = {} 

    for r in raw:
        try:
            comp = str(r.get('Competition', 'Brighton')).strip() or 'Brighton'
            if comp not in cycle_tracker: cycle_tracker[comp] = 0.0
            
            odds = float(str(r.get('Odds', 1)).replace(',', '.'))
            stake = float(str(r.get('Stake', 0)).replace(',', '')) if r.get('Stake') else 0.0
            res = str(r.get('Result', '')).strip()
            win = "Draw (X)" in res
            
            gross_win = stake * odds if win else 0.0
            
            # --- LOGIC: Accumulate stake to current cycle ---
            cycle_tracker[comp] += stake 
            
            if win:
                # Net Profit for Cycle = Gross Win - Total Invested in this cycle
                net_cycle_profit = gross_win - cycle_tracker[comp]
                cycle_tracker[comp] = 0.0 # Reset cycle
            else:
                # Visual profit for this specific bet is just the lost stake
                net_cycle_profit = -stake 
            
            rows.append({
                "Date": r.get('Date', ''), "Comp": comp,
                "Match": f"{r.get('Home Team','')} vs {r.get('Away Team','')}",
                "Odds": odds, "Stake": stake, "Gross": gross_win,
                "Cycle_Net": net_cycle_profit, "Status": "✅ Won" if win else "❌ Lost"
            })
        except: continue
    return pd.DataFrame(rows)

raw_data, worksheet, base_br = connect_db()
df = process_logic(raw_data)
# Live Bankroll = Initial + (Total Income - Total Expenses)
live_br_val = base_br + (df['Gross'].sum() - df['Stake'].sum()) if not df.empty else base_br

# --- 4. SIDEBAR ---
with st.sidebar:
    st.image(APP_LOGO, width=120)
    st.markdown("### WALLET CONTROL")
    st.metric("Base Bankroll", f"₪{base_br:,.0f}")
    amt = st.number_input("Amount", min_value=0.0, value=100.0, step=50.0)
    c1, c2 = st.columns(2)
    if c1.button("Deposit", use_container_width=True): worksheet.update_cell(1, 10, base_br + amt); st.rerun()
    if c2.button("Withdraw", use_container_width=True): worksheet.update_cell(1, 10, base_br - amt); st.rerun()
    st.divider()
    view = st.selectbox("Navigation", ["🏆 Overview", "Brighton", "Africa Cup of Nations"])
    if st.button("🔄 Sync Cloud", use_container_width=True): st.rerun()

# --- 5. RENDER FUNCTIONS ---
def display_live_br(val):
    st.markdown(f"""
        <div style="text-align: center; margin-bottom: 40px;">
            <div style="font-size: 3.5rem; font-weight: 300; color: #fff; text-shadow: 0 0 25px rgba(255,255,255,0.5);">₪{val:,.2f}</div>
            <div style="font-size: 0.9rem; font-weight: 700; color: #fff; letter-spacing: 3px; text-transform: uppercase;">LIVE BANKROLL</div>
        </div>
    """, unsafe_allow_html=True)

# --- 6. MAIN VIEW LOGIC ---

if view == "🏆 Overview":
    st.markdown("<h1 style='text-align: center; letter-spacing: 5px;'>CENTRAL COMMAND</h1>", unsafe_allow_html=True)
    display_live_br(live_br_val)

    if not df.empty:
        # Aggregate logic
        summary = df.groupby('Comp').agg({
            'Match': 'count', 
            'Stake': 'sum', 
            'Gross': 'sum', 
            'Status': lambda x: (x == '✅ Won').sum()
        }).reset_index()
        summary['Profit'] = summary['Gross'] - summary['Stake']
        
        # Metrics
        total_profit = summary['Profit'].sum()
        col1, col2, col3 = st.columns(3)
        pc = "#00ff88" if total_profit >= 0 else "#ff4b4b"
        
        col1.markdown(f'<div class="metric-box"><div class="m-lbl">Total Profit</div><div class="m-val" style="color:{pc}!important">₪{total_profit:,.0f}</div></div>', unsafe_allow_html=True)
        col2.markdown(f'<div class="metric-box"><div class="m-lbl">Total Volume</div><div class="m-val">{summary["Match"].sum()}</div></div>', unsafe_allow_html=True)
        rate = (summary['Status'].sum()/summary['Match'].sum()*100) if summary['Match'].sum() > 0 else 0
        col3.markdown(f'<div class="metric-box"><div class="m-lbl">Win Rate</div><div class="m-val">{rate:.1f}%</div></div>', unsafe_allow_html=True)

        st.markdown("<br><h3>Performance Breakdown</h3>", unsafe_allow_html=True)
        
        # --- TRACK BANNERS (OVERVIEW) ---
        for _, row in summary.iterrows():
            prof = row['Profit']
            # Prepare strings separately to avoid f-string syntax errors
            p_text = f"+₪{prof:,.0f}" if prof >= 0 else f"-₪{abs(prof):,.0f}"
            p_style = "#2d6a4f" if prof >= 0 else "#d32f2f"
            border_style = "status-win" if prof >= 0 else "status-loss"
            wr = (row['Status'] / row['Match'] * 100) if row['Match'] > 0 else 0
            
            st.markdown(f"""
                <div class="banner-container {border_style}">
                    <div style="flex: 1.5;">
                        <span style="font-size: 1.4rem; font-weight: 900;">{row['Comp']}</span>
                    </div>
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
                        <span style="font-size: 1.5rem; font-weight: 900; color: {p_style} !important;">{p_text}</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
        st.markdown("<h3>Distribution</h3>", unsafe_allow_html=True)
        fig = px.bar(summary, x='Comp', y='Profit', color='Profit', color_continuous_scale=['#ff4b4b', '#00ff88'])
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0.1)', font=dict(color='white'), height=300, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

else:
    # TRACK VIEW
    logos = {"Brighton": "https://i.postimg.cc/x8kdQh5H/Brighton_Hove_Albion_logo.png", "Africa Cup of Nations": "https://i.postimg.cc/5yHtJTgz/2025_Africa_Cup_of_Nations_logo.png"}
    grad = "linear-gradient(90deg, #4CABFF, #E6F7FF)" if view == "Brighton" else "linear-gradient(90deg, #CE1126, #FCD116, #007A33)"
    
    st.markdown(f'<div style="background:{grad}; border-radius:15px; padding:25px; display:flex; align-items:center; margin-bottom:20px; box-shadow: 0 0 20px rgba(0,0,0,0.5);"><img src="{logos[view]}" style="height:80px; margin-right:30px;"><h1 style="color:{"#004085" if view=="Brighton" else "white"} !important; margin:0; text-shadow:none !important;">{view.upper()}</h1></div>', unsafe_allow_html=True)
    display_live_br(live_br_val)

    f_df = df[df['Comp'] == view].copy() if not df.empty else pd.DataFrame()
    t_net = f_df['Gross'].sum() - f_df['Stake'].sum() if not f_df.empty else 0.0

    mc1, mc2, mc3 = st.columns(3)
    mc1.markdown(f'<div class="metric-box"><div class="m-lbl">Invested</div><div class="m-val">₪{f_df["Stake"].sum():,.0f}</div></div>', unsafe_allow_html=True)
    mc2.markdown(f'<div class="metric-box"><div class="m-lbl">Gross Rev</div><div class="m-val">₪{f_df["Gross"].sum():,.0f}</div></div>', unsafe_allow_html=True)
    nc = "#00ff88" if t_net >= 0 else "#ff4b4b"
    mc3.markdown(f'<div class="metric-box"><div class="m-lbl">Net Profit</div><div class="m-val" style="color:{nc} !important">₪{t_net:,.0f}</div></div>', unsafe_allow_html=True)

    st.markdown("<br><h2>Performance Strategy</h2>", unsafe_allow_html=True)
    cf, cg = st.columns([1, 1.2])
    
    # --- ADD MATCH BANNER FORM ---
    with cf:
        with st.form("add_match"):
            st.markdown("### ⚽ New Entry")
            h = st.text_input("Home Team", value="Brighton" if view == "Brighton" else "")
            a = st.text_input("Away Team")
            o = st.number_input("Odds", 3.2)
            s = st.number_input("Stake", 30.0)
            r = st.radio("Outcome", ["Draw (X)", "No Draw"], horizontal=True)
            if st.form_submit_button("SUBMIT ENTRY"):
                worksheet.append_row([str(datetime.date.today()), view, h, a, o, r, s, 0.0]); st.rerun()
    
    # Chart
    with cg:
        if not f_df.empty:
            f_df['Equity'] = base_br + (f_df['Gross'].cumsum() - f_df['Stake'].cumsum())
            fig_l = px.line(f_df, y='Equity', x=f_df.index)
            fig_l.update_traces(line_color='#00ff88', line_width=4)
            fig_l.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0.1)', font=dict(color='white'), height=400)
            st.plotly_chart(fig_l, use_container_width=True)

    # --- ACTIVITY LOG BANNERS ---
    st.markdown("### 📜 Activity Log")
    if not f_df.empty:
        for _, row in f_df.sort_index(ascending=False).iterrows():
            is_win = "Won" in row['Status']
            b_class = "status-win" if is_win else "status-loss"
            
            # Prepare values outside f-string to ensure syntax safety
            cycle_val = f"+₪{row['Cycle_Net']:,.0f}" if is_win else f"-₪{abs(row['Cycle_Net']):,.0f}"
            cycle_col = "#2d6a4f" if is_win else "#d32f2f"
            lbl = "CYCLE PROFIT" if is_win else "LOSS"
            
            st.markdown(f"""
                <div class="banner-container {b_class}">
                    <div style="flex: 2;">
                        <span style="font-size: 1.2rem; font-weight: 900;">{row['Match']}</span><br>
                        <span style="font-size: 0.85rem; opacity: 0.7;">{row['Date']} | Odds: {row['Odds']}</span>
                    </div>
                    <div style="flex: 1; text-align: right;">
                        <span style="font-size: 0.8rem; font-weight: bold; color: #555 !important;">{lbl}</span><br>
                        <span style="font-size: 1.4rem; font-weight: 900; color: {cycle_col} !important;">{cycle_val}</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)