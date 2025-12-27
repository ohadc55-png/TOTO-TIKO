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

# --- 2. ELITE UI STYLING (CSS) ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;700;900&family=Inter:wght@400;600&display=swap');
    
    /* 1. Global Cleanup */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    [data-testid="stDecoration"] {{display: none;}}
    header[data-testid="stHeader"] {{ background: transparent !important; }}
    
    /* 2. Arrows & keyb Artifact Fix */
    [data-testid="stSidebarCollapsedControl"] {{
        background-color: rgba(255, 255, 255, 0.2) !important;
        backdrop-filter: blur(5px);
        border-radius: 10px !important;
        width: 45px !important; height: 45px !important;
        display: flex !important; align-items: center !important; justify-content: center !important;
        margin: 15px !important;
    }}
    [data-testid="stSidebarCollapsedControl"] svg {{ fill: white !important; }}
    /* Kill the 'keyb' text */
    [data-testid="stSidebarCollapsedControl"]::after {{ content: none !important; }}
    .stTooltipIcon, [data-testid="stTooltipContent"] {{ display: none !important; }}
    
    /* Sidebar Close Button */
    [data-testid="stSidebar"] button[kind="header"] svg {{ fill: #000000 !important; }}

    /* 3. Main Text Whitening & Shadow */
    .main h1, .main h2, .main h3, .main p, .main span, .main label, .main div {{
        color: #ffffff !important;
        text-shadow: 2px 2px 8px rgba(0,0,0,1) !important;
        font-family: 'Montserrat', sans-serif;
    }}
    
    /* Special fix for Metrics inside main area */
    [data-testid="stMetricValue"] {{ color: white !important; }}
    [data-testid="stMetricLabel"] {{ color: #dddddd !important; }}

    /* 4. Backgrounds */
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

    /* 5. Sidebar Text (Black) */
    [data-testid="stSidebar"] *, [data-testid="stSidebar"] p, [data-testid="stSidebar"] label {{
        color: #000000 !important;
        text-shadow: none !important;
    }}

    /* 6. Activity Log Banner Styling */
    .log-card {{
        padding: 15px;
        border-radius: 12px;
        margin-bottom: 10px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-left: 8px solid;
        box-shadow: 0 4px 15px rgba(0,0,0,0.5);
    }}
    .log-win {{
        background: linear-gradient(90deg, rgba(27, 67, 50, 0.9), rgba(45, 106, 79, 0.9));
        border-color: #52b788;
    }}
    .log-loss {{
        background: linear-gradient(90deg, rgba(102, 7, 8, 0.9), rgba(186, 24, 27, 0.9));
        border-color: #e5383b;
    }}

    /* 7. Components */
    [data-testid="stForm"] {{ 
        background-color: rgba(255, 255, 255, 0.1) !important; 
        border-radius: 20px; border: 1px solid rgba(255,255,255,0.2);
    }}
    .custom-card {{
        background-color: rgba(255, 255, 255, 0.95);
        border-radius: 15px; padding: 20px; text-align: center;
        box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    }}
    .c-label {{ color: #555 !important; font-weight: 700; font-size: 12px; text-shadow: none !important; }}
    .c-value {{ color: #1b4332 !important; font-weight: 900; font-size: 26px; text-shadow: none !important; }}

    </style>
""", unsafe_allow_html=True)

# --- 3. DATA & LOGIC ENGINE ---
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
    if not raw_data: return pd.DataFrame()
    processed = []
    for row in raw_data:
        try:
            comp = str(row.get('Competition', 'Brighton')).strip() or 'Brighton'
            odds = float(str(row.get('Odds', 1)).replace(',', '.'))
            stake = float(str(row.get('Stake', 0)).replace(',', '')) if row.get('Stake') else 0.0
            res = str(row.get('Result', '')).strip()
            is_win = "Draw (X)" in res
            income = stake * odds if is_win else 0.0
            processed.append({
                "Date": row.get('Date', ''), "Comp": comp,
                "Match": f"{row.get('Home Team','')} vs {row.get('Away Team','')}",
                "Odds": odds, "Expense": stake, "Income": income,
                "Status": "✅ Won" if is_win else "❌ Lost"
            })
        except: continue
    return pd.DataFrame(processed)

# --- 4. EXECUTION ---
raw_rows, sheet_ws, initial_bankroll = get_connection()
df = process_data(raw_rows)
live_bankroll = initial_bankroll + (df['Income'].sum() - df['Expense'].sum()) if not df.empty else initial_bankroll

# --- 5. SIDEBAR NAVIGATION ---
with st.sidebar:
    st.image(APP_LOGO, width=120)
    st.markdown("### WALLET")
    st.metric("Base Bankroll", f"₪{initial_bankroll:,.0f}")
    amt = st.number_input("Transaction", min_value=0.0, value=100.0, step=50.0)
    c1, c2 = st.columns(2)
    if c1.button("Deposit", use_container_width=True):
        sheet_ws.update_cell(1, 10, initial_bankroll + amt); st.rerun()
    if c2.button("Withdraw", use_container_width=True):
        sheet_ws.update_cell(1, 10, initial_bankroll - amt); st.rerun()
    st.divider()
    view = st.selectbox("View", ["🏆 Overview", "Brighton", "Africa Cup of Nations"])
    if st.button("🔄 Sync Systems", use_container_width=True): st.rerun()

# --- 6. CONTENT RENDERING ---
if view == "🏆 Overview":
    st.markdown("<h1 style='text-align: center; font-size: 3.5rem;'>CENTRAL COMMAND</h1>", unsafe_allow_html=True)
    st.markdown(f"<h2 style='text-align: center; font-size: 3rem;'>₪{live_bankroll:,.2f}</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-weight: bold;'>GLOBAL LIQUIDITY</p>", unsafe_allow_html=True)

    if not df.empty:
        summary = df.groupby('Comp').agg({'Match': 'count', 'Expense': 'sum', 'Income': 'sum', 'Status': lambda x: (x == '✅ Won').sum()}).reset_index()
        summary['Net Profit'] = summary['Income'] - summary['Expense']
        summary['Win Rate'] = (summary['Status'] / summary['Match'] * 100).map("{:.1f}%".format)
        
        total_p = summary['Net Profit'].sum()
        col1, col2, col3 = st.columns(3)
        p_c = "#52b788" if total_p >= 0 else "#e5383b"
        
        col1.markdown(f'<div class="custom-card"><div class="c-label">Total Profit</div><div class="c-value" style="color:{p_c} !important">₪{total_p:,.0f}</div></div>', unsafe_allow_html=True)
        col2.markdown(f'<div class="custom-card"><div class="c-label">Total Volume</div><div class="c-value">{summary["Match"].sum()}</div></div>', unsafe_allow_html=True)
        col3.markdown(f'<div class="custom-card"><div class="c-label">Avg Success</div><div class="c-value">{(summary["Status"].sum()/summary["Match"].sum()*100):.1f}%</div></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        ch, tb = st.columns([1, 1.2])
        with ch:
            fig = px.bar(summary, x='Comp', y='Net Profit', color='Net Profit', color_continuous_scale=['#e5383b', '#52b788'])
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0.1)', font=dict(color='white'), height=350, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        with tb:
            st.markdown("### Track Performance")
            st.table(summary[['Comp', 'Match', 'Win Rate', 'Net Profit']].rename(columns={'Comp': 'Track'}).style.format({"Net Profit": "₪{:,.0f}"}))

else:
    # SPECIFIC TRACK VIEW
    logos = {"Brighton": "https://i.postimg.cc/x8kdQh5H/Brighton_Hove_Albion_logo.png", "Africa Cup of Nations": "https://i.postimg.cc/5yHtJTgz/2025_Africa_Cup_of_Nations_logo.png"}
    grad = "linear-gradient(90deg, #4CABFF, #E6F7FF)" if view == "Brighton" else "linear-gradient(90deg, #CE1126, #FCD116, #007A33)"
    
    st.markdown(f'<div style="background:{grad}; border-radius:15px; padding:25px; display:flex; align-items:center; margin-bottom:40px;"><img src="{logos[view]}" style="height:80px; margin-right:30px;"><h1 style="color:{"#004085" if view=="Brighton" else "white"} !important; margin:0; text-shadow:none !important;">{view.upper()}</h1></div>', unsafe_allow_html=True)
    st.markdown(f"<h2 style='text-align: center;'>₪{live_bankroll:,.2f}</h2>", unsafe_allow_html=True)

    f_df = df[df['Comp'] == view].copy() if not df.empty else pd.DataFrame()
    t_net = f_df['Income'].sum() - f_df['Expense'].sum() if not f_df.empty else 0.0

    mc1, mc2, mc3 = st.columns(3)
    mc1.markdown(f'<div class="custom-card"><div class="c-label">Expenses</div><div class="c-value">₪{f_df["Expense"].sum():,.0f}</div></div>', unsafe_allow_html=True)
    mc2.markdown(f'<div class="custom-card"><div class="c-label">Revenue</div><div class="c-value">₪{f_df["Income"].sum():,.0f}</div></div>', unsafe_allow_html=True)
    mc3.markdown(f'<div class="custom-card"><div class="c-label">Net Profit</div><div class="c-value" style="color:{"#2d6a4f" if t_net >= 0 else "#d32f2f"} !important">₪{t_net:,.0f}</div></div>', unsafe_allow_html=True)

    st.markdown("<br><h2 style='text-align: center;'>Performance</h2>", unsafe_allow_html=True)
    c_f, c_c = st.columns([1, 1.2])
    with c_f:
        with st.form("entry"):
            h = st.text_input("Home", value="Brighton" if view == "Brighton" else "")
            a = st.text_input("Away")
            o = st.number_input("Odds", 3.2)
            s = st.number_input("Stake", 30.0)
            r = st.radio("Outcome", ["Draw (X)", "No Draw"], horizontal=True)
            if st.form_submit_button("COMMIT"):
                sheet_ws.append_row([str(datetime.date.today()), view, h, a, o, r, s, 0.0]); st.rerun()
    with c_c:
        if not f_df.empty:
            f_df['Equity'] = initial_bankroll + (f_df['Income'].cumsum() - f_df['Expense'].cumsum())
            fig_l = px.line(f_df, y='Equity', x=f_df.index)
            fig_l.update_traces(line_color='#00ff88', line_width=4)
            fig_l.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0.1)', font=dict(color='white'), height=280)
            st.plotly_chart(fig_l, use_container_width=True)
            w = len(f_df[f_df['Status'] == "✅ Won"])
            st.markdown(f"**Win Rate: {(w/len(f_df)*100):.1f}%**")

    st.markdown("### 📜 Activity Log")
    if not f_df.empty:
        for _, row in f_df.sort_index(ascending=False).iterrows():
            style_class = "log-win" if "Won" in row['Status'] else "log-loss"
            st.markdown(f"""
                <div class="log-card {style_class}">
                    <div>
                        <span style="font-size: 1.1rem; font-weight: 900;">{row['Match']}</span><br>
                        <span style="font-size: 0.8rem; opacity: 0.8;">{row['Date']} | Odds: {row['Odds']}</span>
                    </div>
                    <div style="text-align: right;">
                        <span style="font-size: 1.2rem; font-weight: 900;">₪{row['Income'] - row['Expense']:,.0f}</span><br>
                        <span style="font-size: 0.7rem; font-weight: bold;">{row['Status']}</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)