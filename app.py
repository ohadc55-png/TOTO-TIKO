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

# --- 2. THE "ULTIMATE" CSS (FORCE STYLING V3) ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;700;900&display=swap');
    
    /* Global Reset & Cleanup */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    [data-testid="stDecoration"] {{display: none;}}
    header[data-testid="stHeader"] {{ background: transparent !important; }}
    
    /* 1. ARROW FIX V3 - AGGRESSIVE TEXT HIDING */
    /* Outer Arrow (Open Sidebar) */
    [data-testid="stSidebarCollapsedControl"] {{
        background-color: rgba(0, 0, 0, 0.5) !important;
        border-radius: 12px !important;
        width: 45px !important; height: 45px !important;
        display: flex !important; align-items: center !important; justify-content: center !important;
        margin: 15px !important;
        /* Ensure container text is transparent, only show SVG icon color */
        color: transparent !important; 
    }}
    [data-testid="stSidebarCollapsedControl"] svg {{ 
        fill: white !important; 
        width: 25px !important; height: 25px !important; 
    }}
    
    /* Inner Arrow (Close Sidebar) */
    section[data-testid="stSidebar"] button[kind="header"] {{
        color: transparent !important; /* Hide text like "Collapse" */
    }}
    section[data-testid="stSidebar"] button[kind="header"] svg {{
        fill: #000000 !important; /* Force icon black */
        width: 25px !important; height: 25px !important;
    }}

    /* Kill tooltips globally */
    .stTooltipIcon, [data-testid="stTooltipContent"] {{ display: none !important; }}


    /* 2. MAIN AREA TEXT - FORCE WHITE & SHADOW */
    [data-testid="stAppViewContainer"] h1, 
    [data-testid="stAppViewContainer"] h2, 
    [data-testid="stAppViewContainer"] h3, 
    [data-testid="stAppViewContainer"] p, 
    [data-testid="stAppViewContainer"] span,
    [data-testid="stAppViewContainer"] label,
    .stMarkdown p {{
        color: #ffffff !important;
        text-shadow: 2px 2px 8px rgba(0,0,0,1) !important;
        font-family: 'Montserrat', sans-serif !important;
    }}
    [data-testid="stMetricValue"] {{ color: white !important; text-shadow: 2px 2px 4px black !important; }}
    [data-testid="stMetricLabel"] {{ color: #eeeeee !important; }}

    /* 3. BACKGROUND ARCHITECTURE */
    [data-testid="stAppViewContainer"] {{
        background-image: linear-gradient(rgba(0, 0, 0, 0.65), rgba(0, 0, 0, 0.65)), url("{BG_IMAGE}");
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

    /* 4. SIDEBAR CONTENT (BLACK) */
    [data-testid="stSidebar"] *, [data-testid="stSidebar"] p, [data-testid="stSidebar"] label {{
        color: #000000 !important;
        text-shadow: none !important;
    }}

    /* 5. ACTIVITY LOG BANNER CARDS (V2 - Enhanced Data) */
    .activity-banner {{
        padding: 15px 20px;
        border-radius: 15px;
        margin-bottom: 12px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 8px 20px rgba(0,0,0,0.4);
        border-left: 8px solid;
    }}
    .banner-win {{
        background: linear-gradient(90deg, rgba(20, 50, 40, 0.95), rgba(40, 90, 70, 0.95));
        border-color: #00ff88;
    }}
    .banner-loss {{
        background: linear-gradient(90deg, rgba(80, 10, 10, 0.95), rgba(130, 20, 20, 0.95));
        border-color: #ff4b4b;
    }}
    .banner-details-right {{
        text-align: right;
        line-height: 1.2;
    }}

    /* 6. FORM & CARDS */
    [data-testid="stForm"] {{ 
        background-color: rgba(255, 255, 255, 0.1) !important; 
        border-radius: 20px; border: 1px solid rgba(255,255,255,0.25);
    }}
    .metric-card-box {{
        background-color: rgba(255, 255, 255, 0.95);
        border-radius: 15px; padding: 20px; text-align: center;
        box-shadow: 0 10px 25px rgba(0,0,0,0.5);
    }}
    .card-lbl {{ color: #444 !important; font-weight: 700; font-size: 13px; text-shadow: none !important; }}
    .card-val {{ color: #1b4332 !important; font-weight: 900; font-size: 26px; text-shadow: none !important; }}

    </style>
""", unsafe_allow_html=True)

# --- 3. DATA BACKEND ---
def connect_to_cloud():
    try:
        gc = gspread.service_account_from_dict(st.secrets["service_account"])
        sh = gc.open_by_url(st.secrets["sheet_url"])
        ws = sh.get_worksheet(0)
        raw = ws.get_all_records()
        try:
            br_val = ws.cell(1, 10).value
            base_br = float(str(br_val).replace(',', '')) if br_val else 5000.0
        except: base_br = 5000.0
        return raw, ws, base_br
    except Exception as e:
        st.error(f"Sync Lost: {e}")
        return [], None, 5000.0

def process_engine(data):
    if not data: return pd.DataFrame()
    rows = []
    for r in data:
        try:
            c = str(r.get('Competition', 'Brighton')).strip() or 'Brighton'
            o = float(str(r.get('Odds', 1)).replace(',', '.'))
            s = float(str(r.get('Stake', 0)).replace(',', '')) if r.get('Stake') else 0.0
            res = str(r.get('Result', '')).strip()
            win = "Draw (X)" in res
            inc = s * o if win else 0.0
            rows.append({
                "Date": r.get('Date', ''), "Comp": c,
                "Match": f"{r.get('Home Team','')} vs {r.get('Away Team','')}",
                "Odds": o, "Out": s, "In": inc,
                "Status": "✅ Won" if win else "❌ Lost"
            })
        except: continue
    return pd.DataFrame(rows)

# --- 4. EXECUTION ---
raw_data, worksheet, initial_br = connect_to_cloud()
df = process_engine(raw_data)
live_br = initial_br + (df['In'].sum() - df['Out'].sum()) if not df.empty else initial_br

# --- 5. SIDEBAR ---
with st.sidebar:
    st.image(APP_LOGO, width=120)
    st.markdown("### WALLET CONTROL")
    st.metric("Base Bankroll", f"₪{initial_br:,.0f}")
    amt = st.number_input("Amount", min_value=0.0, value=100.0, step=50.0)
    c1, c2 = st.columns(2)
    if c1.button("Deposit", use_container_width=True):
        worksheet.update_cell(1, 10, initial_br + amt); st.rerun()
    if c2.button("Withdraw", use_container_width=True):
        worksheet.update_cell(1, 10, initial_br - amt); st.rerun()
    st.divider()
    view = st.selectbox("View", ["🏆 Overview", "Brighton", "Africa Cup of Nations"])
    if st.button("🔄 Sync Systems", use_container_width=True): st.rerun()

# --- 6. DISPLAY ---
if view == "🏆 Overview":
    st.markdown("<h1 style='text-align: center; font-size: 3.5rem;'>CENTRAL COMMAND</h1>", unsafe_allow_html=True)
    st.markdown(f"<h2 style='text-align: center; font-size: 3rem;'>₪{live_br:,.2f}</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>GLOBAL POSITION</p>", unsafe_allow_html=True)

    if not df.empty:
        summary = df.groupby('Comp').agg({'Match': 'count', 'Out': 'sum', 'In': 'sum', 'Status': lambda x: (x == '✅ Won').sum()}).reset_index()
        summary['Profit'] = summary['In'] - summary['Out']
        summary['Rate'] = (summary['Status'] / summary['Match'] * 100).map("{:.1f}%".format)
        
        t_p = summary['Profit'].sum()
        col1, col2, col3 = st.columns(3)
        p_color = "#00ff88" if t_p >= 0 else "#ff4b4b"
        
        col1.markdown(f'<div class="metric-card-box"><div class="card-lbl">Net Profit</div><div class="card-val" style="color:{p_color}!important">₪{t_p:,.0f}</div></div>', unsafe_allow_html=True)
        col2.markdown(f'<div class="metric-card-box"><div class="card-lbl">Games Played</div><div class="card-val">{summary["Match"].sum()}</div></div>', unsafe_allow_html=True)
        col3.markdown(f'<div class="metric-card-box"><div class="card-lbl">Win Ratio</div><div class="card-val">{(summary["Status"].sum()/summary["Match"].sum()*100):.1f}%</div></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        c_ch, c_tb = st.columns([1, 1.2])
        with c_ch:
            fig = px.bar(summary, x='Comp', y='Profit', color='Profit', color_continuous_scale=['#ff4b4b', '#00ff88'])
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0.1)', font=dict(color='white'), height=350, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        with c_tb:
            st.markdown("### Performance Table")
            st.table(summary[['Comp', 'Match', 'Rate', 'Profit']].rename(columns={'Comp': 'Track', 'Profit': 'Net'}).style.format({"Net": "₪{:,.0f}"}))

else:
    # SPECIFIC TRACK
    logos = {"Brighton": "https://i.postimg.cc/x8kdQh5H/Brighton_Hove_Albion_logo.png", "Africa Cup of Nations": "https://i.postimg.cc/5yHtJTgz/2025_Africa_Cup_of_Nations_logo.png"}
    grad = "linear-gradient(90deg, #4CABFF, #E6F7FF)" if view == "Brighton" else "linear-gradient(90deg, #CE1126, #FCD116, #007A33)"
    
    # Banner
    st.markdown(f'<div style="background:{grad}; border-radius:15px; padding:25px; display:flex; align-items:center; margin-bottom:30px;"><img src="{logos[view]}" style="height:80px; margin-right:30px;"><h1 style="color:{"#004085" if view=="Brighton" else "white"} !important; margin:0; text-shadow:none !important;">{view.upper()}</h1></div>', unsafe_allow_html=True)
    
    # --- NEW: Live Bankroll in Track View ---
    st.markdown(f"<h2 style='text-align: center; font-size: 2.5rem;'>₪{live_br:,.2f}</h2><p style='text-align: center; opacity: 0.8;'>LIVE BANKROLL</p>", unsafe_allow_html=True)
    # ----------------------------------------

    f_df = df[df['Comp'] == view].copy() if not df.empty else pd.DataFrame()
    track_net = f_df['In'].sum() - f_df['Out'].sum() if not f_df.empty else 0.0

    mc1, mc2, mc3 = st.columns(3)
    mc1.markdown(f'<div class="metric-card-box"><div class="card-lbl">Invested</div><div class="card-val">₪{f_df["Out"].sum():,.0f}</div></div>', unsafe_allow_html=True)
    mc2.markdown(f'<div class="metric-card-box"><div class="card-lbl">Revenue</div><div class="card-val">₪{f_df["In"].sum():,.0f}</div></div>', unsafe_allow_html=True)
    n_c = "#2d6a4f" if track_net >= 0 else "#d32f2f"
    mc3.markdown(f'<div class="metric-card-box"><div class="card-lbl">Net Track</div><div class="card-val" style="color:{n_c} !important">₪{track_net:,.0f}</div></div>', unsafe_allow_html=True)

    st.markdown("<br><h3>Performance Strategy</h3>", unsafe_allow_html=True)
    cf, cg = st.columns([1, 1.2])
    with cf:
        with st.form("add"):
            st.subheader("New Entry")
            h, a = st.text_input("Home", value="Brighton" if view == "Brighton" else ""), st.text_input("Away")
            o, s = st.number_input("Odds", 3.2), st.number_input("Stake", 30.0)
            r = st.radio("Result", ["Draw (X)", "No Draw"], horizontal=True)
            if st.form_submit_button("COMMIT"):
                worksheet.append_row([str(datetime.date.today()), view, h, a, o, r, s, 0.0]); st.rerun()
    with cg:
        if not f_df.empty:
            f_df['Eq'] = initial_br + (f_df['In'].cumsum() - f_df['Out'].cumsum())
            fig_l = px.line(f_df, y='Eq', x=f_df.index)
            fig_l.update_traces(line_color='#00ff88', line_width=4)
            fig_l.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0.1)', font=dict(color='white'), height=280)
            st.plotly_chart(fig_l, use_container_width=True)
            st.markdown(f"**Track Success Rate: {(len(f_df[f_df['Status']=='✅ Won'])/len(f_df)*100):.1f}%**")

    st.markdown("### 📜 Activity Log")
    if not f_df.empty:
        for _, row in f_df.sort_index(ascending=False).iterrows():
            b_class = "banner-win" if "Won" in row['Status'] else "banner-loss"
            diff = row['In'] - row['Out']
            # --- NEW: Enhanced Data in Banner ---
            st.markdown(f"""
                <div class="activity-banner {b_class}">
                    <div>
                        <span style="font-size: 1.3rem; font-weight: 900;">{row['Match']}</span><br>
                        <span style="font-size: 0.9rem; opacity: 0.9;">{row['Date']} | Odds: {row['Odds']}</span>
                    </div>
                    <div class="banner-details-right">
                        <span style="font-size: 0.85rem; opacity: 0.9;">Stake: ₪{row['Out']:,.0f} | Gross: ₪{row['In']:,.0f}</span><br>
                        <span style="font-size: 1.6rem; font-weight: 900;">₪{diff:,.0f} (Net)</span><br>
                        <span style="font-size: 0.8rem; font-weight: bold; text-transform: uppercase;">{row['Status']}</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)