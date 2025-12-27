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

# --- 2. ELITE CSS (ARROWS & WHITENING) ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;700;900&display=swap');
    
    /* Global Reset */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    [data-testid="stDecoration"] {{display: none;}}
    header[data-testid="stHeader"] {{ background: transparent !important; }}
    
    /* 1. ARROW FIX - NO TEXT ALLOWED */
    button[aria-label="Open sidebar"], button[aria-label="Collapse sidebar"] {{
        font-size: 0px !important;
        color: transparent !important;
        border: none !important;
    }}
    button[aria-label="Open sidebar"] {{
        background-color: rgba(0, 0, 0, 0.6) !important;
        border-radius: 12px !important;
        width: 45px !important; height: 45px !important;
        margin: 15px !important;
    }}
    button[aria-label="Open sidebar"] svg {{ fill: white !important; width: 28px !important; height: 28px !important; }}
    button[aria-label="Collapse sidebar"] svg {{ fill: black !important; width: 28px !important; height: 28px !important; }}

    /* 2. GLOBAL TEXT WHITENING */
    .main .stMarkdown h1, .main .stMarkdown h2, .main .stMarkdown h3, 
    .main .stMarkdown p, .main .stMarkdown span, .main label {{
        color: #ffffff !important;
        text-shadow: 2px 2px 10px rgba(0,0,0,1) !important;
        font-family: 'Montserrat', sans-serif !important;
    }}
    [data-testid="stMetricValue"] {{ color: white !important; text-shadow: 2px 2px 4px black !important; }}
    [data-testid="stMetricLabel"] {{ color: #ffffff !important; font-weight: bold !important; }}

    /* 3. BACKGROUNDS */
    [data-testid="stAppViewContainer"] {{
        background-image: linear-gradient(rgba(0, 0, 0, 0.6), rgba(0, 0, 0, 0.6)), url("{BG_IMAGE}");
        background-attachment: fixed; background-size: cover; background-position: center;
    }}
    [data-testid="stSidebar"] {{ background-color: rgba(255, 255, 255, 0.85) !important; }}
    [data-testid="stSidebar"]::before {{
        content: ""; position: absolute; top: 0; left: 0; width: 100%; height: 100%;
        background-image: url("{SIDEBAR_BG}"); background-size: cover;
        filter: blur(4px); z-index: -1;
    }}
    [data-testid="stSidebar"] * {{ color: #000000 !important; text-shadow: none !important; }}

    /* 4. ACTIVITY CARDS */
    .activity-banner {{
        padding: 18px 25px; border-radius: 15px; margin-bottom: 15px;
        display: flex; justify-content: space-between; align-items: center;
        box-shadow: 0 10px 25px rgba(0,0,0,0.6); border-left: 12px solid;
    }}
    .banner-win {{ background: linear-gradient(90deg, rgba(20, 55, 45, 0.98), rgba(35, 90, 70, 0.98)); border-color: #00ff88; }}
    .banner-loss {{ background: linear-gradient(90deg, rgba(85, 15, 15, 0.98), rgba(125, 25, 25, 0.98)); border-color: #ff4b4b; }}
    
    [data-testid="stForm"] {{ background-color: rgba(255, 255, 255, 0.1) !important; border-radius: 20px; border: 1px solid rgba(255,255,255,0.3); }}
    .metric-card-white {{ background-color: rgba(255, 255, 255, 0.95); border-radius: 15px; padding: 20px; text-align: center; box-shadow: 0 10px 30px rgba(0,0,0,0.5); }}
    .m-label {{ color: #333 !important; font-weight: 700; font-size: 13px; }}
    .m-value {{ color: #1b4332 !important; font-weight: 900; font-size: 30px; }}

    </style>
""", unsafe_allow_html=True)

# --- 3. DATA ENGINE (MARTINGALE LOGIC) ---
def load_data():
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
        st.error(f"Backend Sync Error: {e}"); return [], None, 5000.0

def process_with_cycles(raw_data):
    if not raw_data: return pd.DataFrame()
    processed = []
    # Tracker per competition to manage independent cycles
    cycle_loss_tracker = {} 

    for r in raw_data:
        try:
            comp = str(r.get('Competition', 'Brighton')).strip() or 'Brighton'
            if comp not in cycle_loss_tracker: cycle_loss_tracker[comp] = 0.0
            
            odds = float(str(r.get('Odds', 1)).replace(',', '.'))
            stake = float(str(r.get('Stake', 0)).replace(',', '')) if r.get('Stake') else 0.0
            res = str(r.get('Result', '')).strip()
            win = "Draw (X)" in res
            gross = stake * odds if win else 0.0
            
            # --- MARTINGALE MATH ---
            cycle_loss_tracker[comp] += stake # Accumulate stakes in this cycle
            
            if win:
                # Cycle Profit: Total Win minus all stakes in this sequence
                display_profit = gross - cycle_loss_tracker[comp]
                cycle_loss_tracker[comp] = 0.0 # Reset cycle on win
            else:
                # Display current bet loss
                display_profit = -stake
            
            processed.append({
                "Date": r.get('Date', ''), "Comp": comp,
                "Match": f"{r.get('Home Team','')} vs {r.get('Away Team','')}",
                "Odds": odds, "Stake": stake, "Gross": gross,
                "Cycle_Net": display_profit, "Status": "✅ Won" if win else "❌ Lost"
            })
        except: continue
    return pd.DataFrame(processed)

# --- 4. EXECUTION ---
raw, worksheet, initial_br = load_data()
df = process_with_cycles(raw)
live_br_calc = initial_br + (df['Gross'].sum() - df['Stake'].sum()) if not df.empty else initial_br

# --- 5. SIDEBAR ---
with st.sidebar:
    st.image(APP_LOGO, width=120)
    st.markdown("### WALLET CONTROL")
    st.metric("Base Bankroll", f"₪{initial_br:,.0f}")
    amt = st.number_input("Amount", min_value=0.0, value=100.0, step=50.0)
    c1, c2 = st.columns(2)
    if c1.button("Deposit", use_container_width=True): worksheet.update_cell(1, 10, initial_br + amt); st.rerun()
    if c2.button("Withdraw", use_container_width=True): worksheet.update_cell(1, 10, initial_br - amt); st.rerun()
    st.divider()
    view = st.selectbox("Navigation", ["🏆 Overview", "Brighton", "Africa Cup of Nations"])
    if st.button("🔄 Sync Cloud", use_container_width=True): st.rerun()

# --- 6. UI RENDERER ---
def draw_live_wallet(val):
    st.markdown(f"""<div style='text-align: center; margin-bottom: 35px;'><div style='font-size: 3.5rem; color: #fff; text-shadow: 0 0 20px rgba(255,255,255,0.4);'>₪{val:,.2f}</div><div style='letter-spacing: 3px; opacity: 0.8;'>LIVE BANKROLL</div></div>""", unsafe_allow_html=True)

if view == "🏆 Overview":
    st.markdown("<h1 style='text-align: center; font-size: 3rem; letter-spacing: 5px;'>CENTRAL COMMAND</h1>", unsafe_allow_html=True)
    draw_live_wallet(live_br_calc)

    if not df.empty:
        # Metrics based on calculated totals
        summary = df.groupby('Comp').agg({'Match': 'count', 'Stake': 'sum', 'Gross': 'sum', 'Status': lambda x: (x == '✅ Won').sum()}).reset_index()
        summary['Profit'] = summary['Gross'] - summary['Stake']
        summary['Rate'] = (summary['Status'] / summary['Match'] * 100).map("{:.1f}%".format)
        
        t_p = summary['Profit'].sum()
        col1, col2, col3 = st.columns(3)
        p_c = "#00ff88" if t_p >= 0 else "#ff4b4b"
        col1.markdown(f'<div class="metric-card-white"><div class="m-label">Net Total</div><div class="m-value" style="color:{p_c}!important">₪{t_p:,.0f}</div></div>', unsafe_allow_html=True)
        col2.markdown(f'<div class="metric-card-white"><div class="m-label">Total Games</div><div class="m-value">{summary["Match"].sum()}</div></div>', unsafe_allow_html=True)
        col3.markdown(f'<div class="metric-card-white"><div class="m-label">Global Health</div><div class="m-value">{(summary["Status"].sum()/summary["Match"].sum()*100):.1f}%</div></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        ch, tb = st.columns([1, 1.2])
        with ch:
            fig = px.bar(summary, x='Comp', y='Profit', color='Profit', color_continuous_scale=['#ff4b4b', '#00ff88'])
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0.1)', font=dict(color='white'), height=350, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        with tb:
            st.markdown("### Track Performance")
            st.table(summary[['Comp', 'Match', 'Rate', 'Profit']].rename(columns={'Comp': 'Track', 'Profit': 'Net'}).style.format({"Net": "₪{:,.0f}"}))

else:
    # SPECIFIC TRACK
    logos = {"Brighton": "https://i.postimg.cc/x8kdQh5H/Brighton_Hove_Albion_logo.png", "Africa Cup of Nations": "https://i.postimg.cc/5yHtJTgz/2025_Africa_Cup_of_Nations_logo.png"}
    grad = "linear-gradient(90deg, #4CABFF, #E6F7FF)" if view == "Brighton" else "linear-gradient(90deg, #CE1126, #FCD116, #007A33)"
    st.markdown(f'<div style="background:{grad}; border-radius:15px; padding:25px; display:flex; align-items:center; margin-bottom:20px;"><img src="{logos[view]}" style="height:80px; margin-right:30px;"><h1 style="color:{"#004085" if view=="Brighton" else "white"} !important; margin:0; text-shadow:none !important;">{view.upper()}</h1></div>', unsafe_allow_html=True)
    
    draw_live_wallet(live_br_calc)

    f_df = df[df['Comp'] == view].copy() if not df.empty else pd.DataFrame()
    t_net = f_df['Gross'].sum() - f_df['Stake'].sum() if not f_df.empty else 0.0

    mc1, mc2, mc3 = st.columns(3)
    mc1.markdown(f'<div class="metric-card-white"><div class="m-label">Total Out</div><div class="m-value">₪{f_df["Stake"].sum():,.0f}</div></div>', unsafe_allow_html=True)
    mc2.markdown(f'<div class="metric-card-white"><div class="m-label">Total In</div><div class="m-value">₪{f_df["Gross"].sum():,.0f}</div></div>', unsafe_allow_html=True)
    nc_color = "#2d6a4f" if t_net >= 0 else "#d32f2f"
    mc3.markdown(f'<div class="metric-card-white"><div class="m-label">Actual Profit</div><div class="m-value" style="color:{nc_color}!important">₪{t_net:,.0f}</div></div>', unsafe_allow_html=True)

    st.markdown("<br><h2>Performance Tracking</h2>", unsafe_allow_html=True)
    c1, c2 = st.columns([1, 1.2])
    with c1:
        with st.form("add"):
            st.subheader("New Entry")
            h, a = st.text_input("Home", value="Brighton" if view == "Brighton" else ""), st.text_input("Away")
            o, s = st.number_input("Odds", 3.2), st.number_input("Stake", 30.0)
            r = st.radio("Result", ["Draw (X)", "No Draw"], horizontal=True)
            if st.form_submit_button("COMMIT TO CLOUD"):
                worksheet.append_row([str(datetime.date.today()), view, h, a, o, r, s, 0.0]); st.rerun()
    with c2:
        if not f_df.empty:
            f_df['Equity'] = initial_br + (f_df['Gross'].cumsum() - f_df['Stake'].cumsum())
            fig_l = px.line(f_df, y='Equity', x=f_df.index)
            fig_l.update_traces(line_color='#00ff88', line_width=4)
            fig_l.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0.1)', font=dict(color='white'), height=280)
            st.plotly_chart(fig_l, use_container_width=True)

    st.markdown("### 📜 ACTIVITY LOG (CYCLE RECOVERY MODE)")
    if not f_df.empty:
        for _, row in f_df.sort_index(ascending=False).iterrows():
            is_win = "Won" in row['Status']
            b_class = "banner-win" if is_win else "banner-loss"
            
            st.markdown(f"""
                <div class="activity-banner {b_class}">
                    <div>
                        <span style="font-size: 1.3rem; font-weight: 900; color: white;">{row['Match']}</span><br>
                        <span style="font-size: 0.9rem; opacity: 0.9; color: white;">{row['Date']} | Odds: {row['Odds']}</span>
                    </div>
                    <div style="text-align: right; line-height: 1.1;">
                        <span style="font-size: 0.85rem; opacity: 0.8; color: white;">{'Cycle Profit:' if is_win else 'Loss:'}</span><br>
                        <span style="font-size: 1.8rem; font-weight: 900; color: white;">₪{row['Cycle_Net']:,.0f}</span><br>
                        <span style="font-size: 0.75rem; font-weight: bold; color: white; text-transform: uppercase;">{row['Status']}</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)