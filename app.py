import streamlit as st
import pandas as pd
import plotly.express as px
import gspread
import datetime

# --- 1. CONFIGURATION ---
APP_LOGO = "https://i.postimg.cc/8Cr6SypK/yzwb-ll-sm.png"
BG_IMAGE = "https://i.postimg.cc/GmFZ4KS7/Gemini-Generated-Image-k1h11zk1h11zk1h1.png"
SIDEBAR_BG = "https://i.postimg.cc/NfdK3hck/'yzwb-ll'-sm-(1).png"

# --- CUSTOM ARROW IMAGES (YOUR UPLOADS) ---
# Arrow for Main Screen (Dark Background -> Needs Light Arrow)
ARROW_OPEN_URL = "https://i.postimg.cc/vHQy61dy/Gemini-Generated-Image-dl91ekdl91ekdl91.png"

# Arrow for Sidebar (White Background -> Needs Dark Arrow)
ARROW_CLOSE_URL = "https://i.postimg.cc/hvVG4Nxz/Gemini-Generated-Image-2tueuy2tueuy2tue.png"

st.set_page_config(
    page_title="GoalMetric Elite Dashboard",
    layout="wide",
    page_icon=APP_LOGO,
    initial_sidebar_state="expanded"
)

# --- 2. CSS STYLING (CUSTOM IMAGES IMPLEMENTED) ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;900&display=swap');
    
    /* 1. RESET */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header[data-testid="stHeader"] {{ background: transparent !important; }}
    
    /* 2. ARROW CONTROLS - CUSTOM IMAGES */
    
    /* A. OPEN BUTTON (Floating on Stadium) */
    button[aria-label="Open sidebar"] {{
        background-color: rgba(0, 0, 0, 0.6) !important; /* Semi-transparent bubble */
        border: 1px solid rgba(255,255,255,0.3) !important;
        border-radius: 12px !important;
        width: 50px !important; height: 50px !important; /* Slightly larger for your image */
        margin-top: 20px !important;
        
        /* IMAGE MAGIC */
        background-image: url('{ARROW_OPEN_URL}') !important;
        background-size: 30px 30px !important; /* Adjust icon size */
        background-repeat: no-repeat !important;
        background-position: center !important;
        
        /* Hide original text/icon */
        color: transparent !important;
        font-size: 0px !important;
    }}
    button[aria-label="Open sidebar"] svg {{ display: none !important; }}
    
    /* B. CLOSE BUTTON (Inside White Sidebar) */
    button[aria-label="Collapse sidebar"] {{
        background-color: transparent !important;
        border: none !important;
        width: 50px !important; height: 50px !important;
        
        /* IMAGE MAGIC */
        background-image: url('{ARROW_CLOSE_URL}') !important;
        background-size: 30px 30px !important;
        background-repeat: no-repeat !important;
        background-position: center !important;
        
        /* Hide original text/icon */
        color: transparent !important;
        font-size: 0px !important;
    }}
    button[aria-label="Collapse sidebar"] svg {{ display: none !important; }}
    
    .stTooltipIcon {{ display: none !important; }}

    /* 3. MAIN AREA TEXT (WHITE ON DARK) */
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

    /* Metrics */
    [data-testid="stMetricValue"] {{ color: #ffffff !important; text-shadow: 0px 2px 5px rgba(0,0,0,1); }}
    [data-testid="stMetricLabel"] {{ color: #dddddd !important; }}

    /* 4. FORM */
    [data-testid="stForm"] {{
        background: linear-gradient(180deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.05) 100%);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.2);
        border-radius: 16px;
        padding: 25px;
    }}
    [data-testid="stForm"] label p {{ color: #ffffff !important; font-weight: 600; }}

    /* 5. INPUT FIELDS */
    input {{ background-color: #ffffff !important; color: #000000 !important; font-weight: bold; border-radius: 5px; }}
    div[data-baseweb="select"] > div {{ background-color: #ffffff !important; color: #000000 !important; }}
    div[data-baseweb="select"] span {{ color: #000000 !important; }}

    /* 6. SIDEBAR (BLACK TEXT) */
    [data-testid="stSidebar"] {{ background-color: rgba(255, 255, 255, 0.95); }}
    [data-testid="stSidebar"]::before {{
        content: ""; position: absolute; top: 0; left: 0; width: 100%; height: 100%;
        background-image: url("{SIDEBAR_BG}"); background-size: cover;
        filter: blur(5px); z-index: -1;
    }}
    /* Force BLACK text in sidebar */
    [data-testid="stSidebar"] *, [data-testid="stSidebar"] p, [data-testid="stSidebar"] label {{
        color: #000000 !important;
        text-shadow: none !important;
    }}

    /* 7. BANNERS */
    .banner-card {{
        background: rgba(255, 255, 255, 0.95);
        border-radius: 12px;
        padding: 15px 20px;
        margin-bottom: 15px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        border-left: 10px solid #333;
    }}
    .banner-card span, .banner-card div {{
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

    [data-testid="stAppViewContainer"] {{
        background-image: linear-gradient(rgba(0, 0, 0, 0.7), rgba(0, 0, 0, 0.7)), url("{BG_IMAGE}");
        background-attachment: fixed; background-size: cover; background-position: center;
    }}
    [data-testid="stDataFrame"] {{ display: none; }} 
    </style>
""", unsafe_allow_html=True)

# --- 3. BACKEND LOGIC ---
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
            
            cycle_tracker[comp] += stake 
            
            if win:
                net_cycle_profit = gross_win - cycle_tracker[comp]
                cycle_tracker[comp] = 0.0 
            else:
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

# --- 6. MAIN VIEW ---

if view == "🏆 Overview":
    st.markdown("<h1 style='text-align: center; letter-spacing: 5px;'>CENTRAL COMMAND</h1>", unsafe_allow_html=True)
    display_live_br(live_br_val)

    if not df.empty:
        summary = df.groupby('Comp').agg({
            'Match': 'count', 'Stake': 'sum', 'Gross': 'sum', 'Status': lambda x: (x == '✅ Won').sum()
        }).reset_index()
        summary['Profit'] = summary['Gross'] - summary['Stake']
        
        total_profit = summary['Profit'].sum()
        col1, col2, col3 = st.columns(3)
        
        pc = "#00ff88"
        if total_profit < 0: pc = "#ff4b4b"
        
        col1.markdown(f'<div class="metric-box"><div class="m-lbl">Total Profit</div><div class="m-val" style="color:{pc}!important">₪{total_profit:,.0f}</div></div>', unsafe_allow_html=True)
        col2.markdown(f'<div class="metric-box"><div class="m-lbl">Total Volume</div><div class="m-val">{summary["Match"].sum()}</div></div>', unsafe_allow_html=True)
        rate = (summary['Status'].sum()/summary['Match'].sum()*100) if summary['Match'].sum() > 0 else 0
        col3.markdown(f'<div class="metric-box"><div class="m-lbl">Win Rate</div><div class="m-val">{rate:.1f}%</div></div>', unsafe_allow_html=True)

        st.markdown("<br><h3>Performance Breakdown</h3>", unsafe_allow_html=True)
        
        for _, row in summary.iterrows():
            prof = row['Profit']
            
            if prof >= 0:
                p_text = f"+₪{prof:,.0f}"
                p_style = "#2d6a4f"
                border_style = "status-win"
            else:
                p_text = f"-₪{abs(prof):,.0f}"
                p_style = "#d32f2f"
                border_style = "status-loss"
            
            wr_val = 0.0
            if row['Match'] > 0: wr_val = (row['Status'] / row['Match'] * 100)
            
            st.markdown(f"""
                <div class="banner-card {border_style}">
                    <div style="flex: 1.5;">
                        <span style="font-size: 1.4rem; font-weight: 900;">{row['Comp']}</span>
                    </div>
                    <div style="flex: 1; text-align: center;">
                        <span style="font-size: 0.8rem; font-weight: bold; color: #555 !important;">GAMES</span><br>
                        <span style="font-size: 1.2rem; font-weight: 800;">{row['Match']}</span>
                    </div>
                    <div style="flex: 1; text-align: center;">
                        <span style="font-size: 0.8rem; font-weight: bold; color: #555 !important;">WINS</span><br>
                        <span style="font-size: 1.2rem; font-weight: 800;">{row['Status']} ({wr_val:.1f}%)</span>
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
    logos = {"Brighton": "https://i.postimg.cc/x8kdQh5H/Brighton_Hove_Albion_logo.png", "Africa Cup of Nations": "https://i.postimg.cc/5yHtJTgz/2025_Africa_Cup_of_Nations_logo.png"}
    grad = "linear-gradient(90deg, #4CABFF, #E6F7FF)" if view == "Brighton" else "linear-gradient(90deg, #CE1126, #FCD116, #007A33)"
    
    st.markdown(f'<div style="background:{grad}; border-radius:15px; padding:25px; display:flex; align-items:center; margin-bottom:20px; box-shadow: 0 0 20px rgba(0,0,0,0.5);"><img src="{logos[view]}" style="height:80px; margin-right:30px;"><h1 style="color:{"#004085" if view=="Brighton" else "white"} !important; margin:0; text-shadow:none !important;">{view.upper()}</h1></div>', unsafe_allow_html=True)
    display_live_br(live_br_val)

    f_df = df[df['Comp'] == view].copy() if not df.empty else pd.DataFrame()
    t_net = f_df['Gross'].sum() - f_df['Stake'].sum() if not f_df.empty else 0.0

    mc1, mc2, mc3 = st.columns(3)
    mc1.markdown(f'<div class="metric-box"><div class="m-lbl">Invested</div><div class="m-val">₪{f_df["Stake"].sum():,.0f}</div></div>', unsafe_allow_html=True)
    mc2.markdown(f'<div class="metric-box"><div class="m-lbl">Gross Rev</div><div class="m-val">₪{f_df["Gross"].sum():,.0f}</div></div>', unsafe_allow_html=True)
    
    nc = "#00ff88"
    if t_net < 0: nc = "#ff4b4b"
    
    mc3.markdown(f'<div class="metric-box"><div class="m-lbl">Net Profit</div><div class="m-val" style="color:{nc} !important">₪{t_net:,.0f}</div></div>', unsafe_allow_html=True)

    st.markdown("<br><h2>Performance Strategy</h2>", unsafe_allow_html=True)
    cf, cg = st.columns([1, 1.2])
    
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
    
    with cg:
        if not f_df.empty:
            f_df['Equity'] = base_br + (f_df['Gross'].cumsum() - f_df['Stake'].cumsum())
            fig_l = px.line(f_df, y='Equity', x=f_df.index)
            fig_l.update_traces(line_color='#00ff88', line_width=4)
            fig_l.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0.1)', font=dict(color='white'), height=400)
            st.plotly_chart(fig_l, use_container_width=True)

    st.markdown("### 📜 Activity Log")
    if not f_df.empty:
        for _, row in f_df.sort_index(ascending=False).iterrows():
            is_win = "Won" in row['Status']
            b_class = "status-win" if is_win else "status-loss"
            
            if is_win:
                cycle_val = f"+₪{row['Cycle_Net']:,.0f}"
                cycle_col = "#2d6a4f"
                lbl = "CYCLE PROFIT"
            else:
                cycle_val = f"-₪{abs(row['Cycle_Net']):,.0f}"
                cycle_col = "#d32f2f"
                lbl = "LOSS"
            
            stake_display = f"Stake: ₪{row['Stake']:,.0f}"
            
            st.markdown(f"""
                <div class="banner-card {b_class}">
                    <div style="flex: 2;">
                        <span style="font-size: 1.2rem; font-weight: 900;">{row['Match']}</span><br>
                        <span style="font-size: 0.85rem; opacity: 0.7;">{row['Date']} | Odds: {row['Odds']}</span><br>
                        <span style="font-size: 0.8rem; font-weight: bold; color: #333 !important;">{stake_display}</span>
                    </div>
                    <div style="flex: 1; text-align: right;">
                        <span style="font-size: 0.8rem; font-weight: bold; color: #555 !important;">{lbl}</span><br>
                        <span style="font-size: 1.4rem; font-weight: 900; color: {cycle_col} !important;">{cycle_val}</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)