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

# --- 2. THE "IRON-CLAD" CSS (FORCE OVERRIDE V4) ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;700;900&display=swap');
    
    /* 1. Reset & Cleanup */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    [data-testid="stDecoration"] {{display: none;}}
    header[data-testid="stHeader"] {{ background: transparent !important; }}
    
    /* 2. ULTIMATE ARROW FIX (Hides 'keyb' and text) */
    /* Target Open Button */
    button[aria-label="Open sidebar"] {{
        background-color: rgba(0, 0, 0, 0.6) !important;
        border-radius: 50% !important;
        color: white !important;
        font-size: 0px !important; /* Hides text */
    }}
    button[aria-label="Open sidebar"] svg {{
        fill: white !important;
        width: 30px !important; height: 30px !important;
    }}

    /* Target Close Button */
    button[aria-label="Collapse sidebar"] {{
        color: transparent !important;
        font-size: 0px !important;
    }}
    button[aria-label="Collapse sidebar"] svg {{
        fill: black !important;
        width: 30px !important; height: 30px !important;
    }}

    /* 3. GLOBAL TEXT WHITENING (High Specificity) */
    .main .stMarkdown h1, .main .stMarkdown h2, .main .stMarkdown h3, 
    .main .stMarkdown p, .main .stMarkdown span, .main label, 
    .main [data-testid="stCaptionContainer"] p {{
        color: #ffffff !important;
        text-shadow: 2px 2px 10px rgba(0,0,0,1) !important;
        font-family: 'Montserrat', sans-serif !important;
    }}

    /* Metrics on Stadium Background */
    [data-testid="stMetricValue"] {{ color: white !important; text-shadow: 2px 2px 4px black !important; }}
    [data-testid="stMetricLabel"] {{ color: #ffffff !important; font-weight: bold !important; opacity: 0.9; }}

    /* 4. BACKGROUND LAYERS */
    [data-testid="stAppViewContainer"] {{
        background-image: linear-gradient(rgba(0, 0, 0, 0.6), rgba(0, 0, 0, 0.6)), url("{BG_IMAGE}");
        background-attachment: fixed; background-size: cover; background-position: center;
    }}
    [data-testid="stSidebar"] {{
        background-color: rgba(255, 255, 255, 0.85) !important;
    }}
    [data-testid="stSidebar"]::before {{
        content: ""; position: absolute; top: 0; left: 0; width: 100%; height: 100%;
        background-image: url("{SIDEBAR_BG}"); background-size: cover;
        filter: blur(4px); z-index: -1;
    }}

    /* 5. SIDEBAR TEXT (FORCE BLACK) */
    [data-testid="stSidebar"] * {{
        color: #000000 !important;
        text-shadow: none !important;
    }}

    /* 6. ACTIVITY LOG BANNER CARDS V2 */
    .activity-banner {{
        padding: 18px 25px;
        border-radius: 15px;
        margin-bottom: 15px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 10px 25px rgba(0,0,0,0.6);
        border-left: 12px solid;
    }}
    .banner-win {{
        background: linear-gradient(90deg, rgba(20, 50, 40, 0.98), rgba(30, 80, 60, 0.98));
        border-color: #00ff88;
    }}
    .banner-loss {{
        background: linear-gradient(90deg, rgba(80, 10, 10, 0.98), rgba(120, 20, 20, 0.98));
        border-color: #ff4b4b;
    }}
    .banner-right-info {{ text-align: right; line-height: 1.1; }}

    /* 7. WIDGETS */
    [data-testid="stForm"] {{ 
        background-color: rgba(255, 255, 255, 0.1) !important; 
        border-radius: 20px; border: 1px solid rgba(255,255,255,0.3);
    }}
    .metric-card-white {{
        background-color: rgba(255, 255, 255, 0.95);
        border-radius: 15px; padding: 20px; text-align: center;
        box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    }}
    .m-label {{ color: #333 !important; font-weight: 700; font-size: 13px; text-shadow: none !important; }}
    .m-value {{ color: #1b4332 !important; font-weight: 900; font-size: 30px; text-shadow: none !important; }}

    </style>
""", unsafe_allow_html=True)

# --- 3. DATA ENGINE ---
def load_and_sync():
    try:
        gc = gspread.service_account_from_dict(st.secrets["service_account"])
        sh = gc.open_by_url(st.secrets["sheet_url"])
        ws = sh.get_worksheet(0)
        data = ws.get_all_records()
        try:
            br_val = ws.cell(1, 10).value
            initial_br = float(str(br_val).replace(',', '')) if br_val else 5000.0
        except: initial_br = 5000.0
        return data, ws, initial_br
    except Exception as e:
        st.error(f"Sync Issue: {e}")
        return [], None, 5000.0

def process_logic(data):
    if not data: return pd.DataFrame()
    rows = []
    for r in data:
        try:
            c = str(r.get('Competition', 'Brighton')).strip() or 'Brighton'
            o = float(str(r.get('Odds', 1)).replace(',', '.'))
            s = float(str(r.get('Stake', 0)).replace(',', '')) if r.get('Stake') else 0.0
            res = str(r.get('Result', '')).strip()
            win = "Draw (X)" in res
            gross_win = s * o if win else 0.0
            rows.append({
                "Date": r.get('Date', ''), "Comp": c,
                "Match": f"{r.get('Home Team','')} vs {r.get('Away Team','')}",
                "Odds": o, "Stake": s, "Gross": gross_win,
                "Status": "✅ Won" if win else "❌ Lost"
            })
        except: continue
    return pd.DataFrame(rows)

# --- 4. EXECUTION ---
raw, worksheet, base_br = load_and_sync()
df = process_logic(raw)
# Global logic: live_br is initial + sum(gross) - sum(stake)
live_br_calc = base_br + (df['Gross'].sum() - df['Stake'].sum()) if not df.empty else base_br

# --- 5. SIDEBAR ---
with st.sidebar:
    st.image(APP_LOGO, width=120)
    st.markdown("### WALLET CONTROL")
    st.metric("Base Bankroll", f"₪{base_br:,.0f}")
    amt = st.number_input("Amount", min_value=0.0, value=100.0, step=50.0)
    c1, c2 = st.columns(2)
    if c1.button("Deposit", use_container_width=True):
        worksheet.update_cell(1, 10, base_br + amt); st.rerun()
    if c2.button("Withdraw", use_container_width=True):
        worksheet.update_cell(1, 10, base_br - amt); st.rerun()
    st.divider()
    view = st.selectbox("Navigation View", ["🏆 Overview", "Brighton", "Africa Cup of Nations"])
    if st.button("🔄 Sync Cloud", use_container_width=True): st.rerun()

# --- 6. UI RENDERER ---

# Shared live bankroll component
def show_live_br(val):
    st.markdown(f"""
    <div style="text-align: center; margin: 10px 0 40px 0;">
        <div style="font-size: 3.5rem; font-weight: 300; color: #ffffff; text-shadow: 0 0 25px rgba(255,255,255,0.4); line-height: 1;">₪{val:,.2f}</div>
        <div style="font-size: 0.9rem; font-weight: 700; color: #ffffff; letter-spacing: 4px; text-transform: uppercase; opacity: 0.8;">LIVE BANKROLL</div>
    </div>
    """, unsafe_allow_html=True)

if view == "🏆 Overview":
    st.markdown("<h1 style='text-align: center; font-size: 3rem; letter-spacing: 5px;'>CENTRAL COMMAND</h1>", unsafe_allow_html=True)
    show_live_br(live_br_calc)

    if not df.empty:
        summary = df.groupby('Comp').agg({'Match': 'count', 'Stake': 'sum', 'Gross': 'sum', 'Status': lambda x: (x == '✅ Won').sum()}).reset_index()
        summary['Profit'] = summary['Gross'] - summary['Stake']
        summary['Rate'] = (summary['Status'] / summary['Match'] * 100).map("{:.1f}%".format)
        
        t_p = summary['Profit'].sum()
        col1, col2, col3 = st.columns(3)
        p_color = "#00ff88" if t_p >= 0 else "#ff4b4b"
        
        col1.markdown(f'<div class="metric-card-white"><div class="m-label">Total Profit</div><div class="m-value" style="color:{p_color}!important">₪{t_p:,.0f}</div></div>', unsafe_allow_html=True)
        col2.markdown(f'<div class="metric-card-white"><div class="m-label">Total Games</div><div class="m-value">{summary["Match"].sum()}</div></div>', unsafe_allow_html=True)
        col3.markdown(f'<div class="metric-card-white"><div class="m-label">Success Rate</div><div class="m-value">{(summary["Status"].sum()/summary["Match"].sum()*100):.1f}%</div></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        c_ch, c_tb = st.columns([1, 1.2])
        with c_ch:
            fig = px.bar(summary, x='Comp', y='Profit', color='Profit', color_continuous_scale=['#ff4b4b', '#00ff88'])
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0.1)', font=dict(color='white'), height=350, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        with c_tb:
            st.markdown("### 📊 Track Breakdown")
            st.table(summary[['Comp', 'Match', 'Rate', 'Profit']].rename(columns={'Comp': 'Track', 'Profit': 'Net'}).style.format({"Net": "₪{:,.0f}"}))

else:
    # TRACK VIEW
    logos = {"Brighton": "https://i.postimg.cc/x8kdQh5H/Brighton_Hove_Albion_logo.png", "Africa Cup of Nations": "https://i.postimg.cc/5yHtJTgz/2025_Africa_Cup_of_Nations_logo.png"}
    grad = "linear-gradient(90deg, #4CABFF, #E6F7FF)" if view == "Brighton" else "linear-gradient(90deg, #CE1126, #FCD116, #007A33)"
    
    st.markdown(f'<div style="background:{grad}; border-radius:15px; padding:25px; display:flex; align-items:center; margin-bottom:20px;"><img src="{logos[view]}" style="height:80px; margin-right:30px;"><h1 style="color:{"#004085" if view=="Brighton" else "white"} !important; margin:0; text-shadow:none !important;">{view.upper()}</h1></div>', unsafe_allow_html=True)
    
    # Live Bankroll displayed below banner
    show_live_br(live_br_calc)

    f_df = df[df['Comp'] == view].copy() if not df.empty else pd.DataFrame()
    t_net = f_df['Gross'].sum() - f_df['Stake'].sum() if not f_df.empty else 0.0

    mc1, mc2, mc3 = st.columns(3)
    mc1.markdown(f'<div class="metric-card-white"><div class="m-label">Total Invested</div><div class="m-value">₪{f_df["Stake"].sum():,.0f}</div></div>', unsafe_allow_html=True)
    mc2.markdown(f'<div class="metric-card-white"><div class="m-label">Total Gross</div><div class="m-value">₪{f_df["Gross"].sum():,.0f}</div></div>', unsafe_allow_html=True)
    nc = "#2d6a4f" if t_net >= 0 else "#d32f2f"
    mc3.markdown(f'<div class="metric-card-white"><div class="m-label">Track Net</div><div class="m-value" style="color:{nc} !important">₪{t_net:,.0f}</div></div>', unsafe_allow_html=True)

    st.markdown("<br><h2>Performance & Entry</h2>", unsafe_allow_html=True)
    cf, cg = st.columns([1, 1.2])
    with cf:
        with st.form("add_match"):
            st.subheader("Add Match")
            h, a = st.text_input("Home", value="Brighton" if view == "Brighton" else ""), st.text_input("Away")
            o, s = st.number_input("Odds", 3.2), st.number_input("Stake", 30.0)
            r = st.radio("Outcome", ["Draw (X)", "No Draw"], horizontal=True)
            if st.form_submit_button("SUBMIT"):
                worksheet.append_row([str(datetime.date.today()), view, h, a, o, r, s, 0.0]); st.rerun()
    with cg:
        if not f_df.empty:
            f_df['Equity'] = base_br + (f_df['Gross'].cumsum() - f_df['Stake'].cumsum())
            fig_l = px.line(f_df, y='Equity', x=f_df.index)
            fig_l.update_traces(line_color='#00ff88', line_width=4)
            fig_l.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0.1)', font=dict(color='white'), height=280)
            st.plotly_chart(fig_l, use_container_width=True)
            wins_count = len(f_df[f_df['Status']=='✅ Won'])
            st.markdown(f"**Win Rate: {(wins_count/len(f_df)*100):.1f}% | Total Matches: {len(f_df)}**")

    st.markdown("### 📜 Activity Log")
    if not f_df.empty:
        for _, row in f_df.sort_index(ascending=False).iterrows():
            b_class = "banner-win" if "Won" in row['Status'] else "banner-loss"
            net_cycle = row['Gross'] - row['Stake']
            st.markdown(f"""
                <div class="activity-banner {b_class}">
                    <div>
                        <span style="font-size: 1.3rem; font-weight: 900; color: white;">{row['Match']}</span><br>
                        <span style="font-size: 0.9rem; opacity: 0.9; color: white;">{row['Date']} | Odds: {row['Odds']}</span>
                    </div>
                    <div class="banner-right-info">
                        <span style="font-size: 0.85rem; opacity: 0.8; color: white;">Stake: ₪{row['Stake']:,.0f} | Gross: ₪{row['Gross']:,.0f}</span><br>
                        <span style="font-size: 1.6rem; font-weight: 900; color: white;">₪{net_cycle:,.0f} (Net)</span><br>
                        <span style="font-size: 0.8rem; font-weight: bold; color: white; text-transform: uppercase;">{row['Status']}</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)