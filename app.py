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
    page_title="Elite Football Tracker",
    layout="wide",
    page_icon=APP_LOGO_URL,
    initial_sidebar_state="expanded"
)

# --- 2. CSS STYLING (Professional Fix for Arrows) ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;600;900&family=Inter:wght@400;600&display=swap');
    
    /* --- 1. CLEANUP & HEADER --- */
    /* Hide standard footer and top decoration bar */
    footer {{display: none !important;}}
    [data-testid="stDecoration"] {{display: none !important;}}
    #MainMenu {{visibility: hidden;}}

    /* Make header transparent but keep it visible for interactive elements */
    [data-testid="stHeader"] {{
        background-color: transparent !important;
        z-index: 100 !important;
    }}

    /* --- 2. ARROW STYLING (THE FIX) --- */
    
    /* >>> CASE A: SIDEBAR CLOSED -> OPEN ARROW (Must be WHITE on dark background) <<< */
    /* Target the container of the open button */
    [data-testid="stSidebarCollapsedControl"] {{
        color: #ffffff !important;
        z-index: 10000 !important; /* Ensure it's clickable */
    }}
    /* Force the actual SVG icon inside to be bright WHITE */
    [data-testid="stSidebarCollapsedControl"] svg,
    [data-testid="stSidebarCollapsedControl"] svg path {{
        fill: #ffffff !important;
        stroke: #ffffff !important;
    }}

    /* >>> CASE B: SIDEBAR OPEN -> CLOSE ARROW/X (Must be BLACK on light background) <<< */
    /* We target the specific button located within the sidebar header area */
    [data-testid="stSidebar"] [data-testid="stSidebarUserContent"] > div:first-child button {{
         border: none !important;
         background: transparent !important;
    }}
    /* Force the SVG icon inside this specific button to be BLACK */
    [data-testid="stSidebar"] [data-testid="stSidebarUserContent"] > div:first-child button svg,
    [data-testid="stSidebar"] [data-testid="stSidebarUserContent"] > div:first-child button svg path {{
        fill: #000000 !important;
        stroke: #000000 !important;
    }}
    
    /* Add padding to sidebar content so it doesn't overlap the close button */
    [data-testid="stSidebarUserContent"] {{
        padding-top: 3rem !important; 
    }}


    /* --- 3. BACKGROUNDS --- */
    /* Main Stadium Background */
    [data-testid="stAppViewContainer"] {{
        background-image: linear-gradient(rgba(0, 0, 0, 0.7), rgba(0, 0, 0, 0.7)), url("{BG_IMAGE_URL}");
        background-attachment: fixed;
        background-size: cover;
        background-position: center;
    }}

    /* Sidebar Blurred Background */
    [data-testid="stSidebar"] {{
        position: relative;
        background-color: rgba(255, 255, 255, 0.75) !important;
        border-right: 1px solid rgba(255,255,255,0.2);
    }}
    [data-testid="stSidebar"]::before {{
        content: "";
        position: absolute;
        top: 0; left: 0; width: 100%; height: 100%;
        background-image: url("{SIDEBAR_BG_IMAGE_URL}");
        background-size: cover;
        background-position: center;
        filter: blur(5px); 
        z-index: -1;
        transform: scale(1.05);
    }}

    /* --- 4. CONTENT STYLING --- */
    /* Sidebar Text (Black) */
    [data-testid="stSidebar"] *, 
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] div,
    [data-testid="stSidebar"] label, [data-testid="stSidebar"] .stMarkdown,
    [data-testid="stSidebar"] [data-testid="stMetricValue"] {{
        color: #000000 !important;
        text-shadow: none !important;
        font-family: 'Montserrat', sans-serif;
    }}
    
    /* Sidebar Inputs */
    [data-testid="stSidebar"] input {{
        color: #000000 !important;
        background-color: rgba(255, 255, 255, 0.9) !important;
        border: 1px solid #ccc;
    }}
    
    /* Action Buttons (Green) */
    [data-testid="stSidebar"] [data-testid="stButton"] button {{
        color: #ffffff !important;
        background-color: #2E7D32 !important;
    }}

    /* Main Area Text (White) */
    .main h1, .main h2, .main h3, .main h4, .main p {{
        color: #ffffff !important;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.8);
    }}

    /* --- 5. COMPONENTS --- */
    [data-testid="stDataFrame"] {{ background-color: white !important; border-radius: 8px; }}
    [data-testid="stDataFrame"] * {{ color: #000000 !important; text-shadow: none !important; }}

    [data-testid="stForm"] {{ background-color: rgba(255, 255, 255, 0.95); border-radius: 15px; padding: 25px; }}
    [data-testid="stForm"] * {{ color: #000000 !important; text-shadow: none !important; }}

    .custom-metric-box {{
        background-color: rgba(255, 255, 255, 0.95);
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }}
    .metric-card-label {{ color: #555 !important; font-weight: 700; font-size: 13px; text-shadow: none !important; }}
    .metric-card-value {{ color: #1b4332 !important; font-weight: 900; font-size: 26px; text-shadow: none !important; }}

    /* --- 6. MOBILE RESPONSIVE --- */
    @media only screen and (max-width: 768px) {{
        .banner-text {{ display: none !important; }}
        .banner-container {{ justify-content: center !important; padding: 10px !important; }}
        .banner-img {{ height: 120px !important; margin: 0 !important; filter: drop-shadow(0 0 10px rgba(255,255,255,0.3)) !important; }}
        [data-testid="stDataFrame"] * {{ font-size: 12px !important; }}
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
            try: odds = float(str(row.get('Odds', 1)).replace(',', '.'))
            except: odds = 1.0
            try:
                stake_val = row.get('Stake')
                if stake_val in [None, '', ' ']: exp = next_bets[comp]
                else: exp = float(str(stake_val).replace(',', ''))
            except: exp = next_bets[comp]
            res = str(row.get('Result', '')).strip()
            cycle_invest[comp] += exp
            is_win = "Draw (X)" in res
            
            if is_win:
                inc = exp * odds
                net = inc - cycle_invest[comp]
                try: roi = f"{(net / cycle_invest[comp]) * 100:.1f}%"
                except: roi = "0.0%"
                next_bets[comp] = float(br_base if "Brighton" in comp else af_base)
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
    df = pd.DataFrame()
    current_bal = saved_br

# --- 5. UI LAYOUT ---

# SIDEBAR
with st.sidebar:
    try: st.image(APP_LOGO_URL, width=120)
    except: pass
    
    st.markdown("## WALLET CONTROL")
    st.metric("Base Bankroll", f"₪{saved_br:,.0f}")
    
    st.write("Transaction Amount:")
    amt = st.number_input("Amount", min_value=0.0, value=100.0, step=50.0, label_visibility="collapsed")
    
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Deposit", use_container_width=True):
            if update_bankroll(worksheet, saved_br + amt): st.rerun()
    with c2:
        if st.button("Withdraw", use_container_width=True):
            if update_bankroll(worksheet, saved_br - amt): st.rerun()
            
    st.divider()
    st.write("Current Track:")
    track = st.selectbox("Track", ["Brighton", "Africa Cup of Nations"], label_visibility="collapsed")
    if st.button("🔄 Sync Cloud", use_container_width=True): st.rerun()

# BANNER
brighton_logo = "https://i.postimg.cc/x8kdQh5H/Brighton_Hove_Albion_logo.png"
afcon_logo = "https://i.postimg.cc/5yHtJTgz/2025_Africa_Cup_of_Nations_logo.png"

if track == "Brighton":
    banner_bg = "linear-gradient(90deg, #4CABFF 0%, #E6F7FF 50%, #4CABFF 100%)"
    text_color = "#004085"
    logo_src = brighton_logo
    shadow_style = "none"
else:
    banner_bg = "linear-gradient(90deg, #CE1126 0%, #FCD116 50%, #007A33 100%)"
    text_color = "#FFFFFF"
    logo_src = afcon_logo
    shadow_style = "2px 2px 4px #000000"

st.markdown(f"""
    <div class="banner-container" style="
        background: {banner_bg};
        border-radius: 15px;
        padding: 20px;
        display: flex;
        align-items: center;
        margin-bottom: 30px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.5);
        border: 2px solid rgba(255,255,255,0.4);
    ">
        <img class="banner-img" src="{logo_src}" style="height: 70px; margin-right: 25px; filter: drop-shadow(0 4px 6px rgba(0,0,0,0.3)); transition: all 0.3s;">
        <h1 class="banner-text" style="
            margin: 0;
            font-size: 2.2rem;
            font-weight: 900;
            text-transform: uppercase;
            color: {text_color} !important;
            text-shadow: {shadow_style};
            font-family: 'Montserrat', sans-serif;
            letter-spacing: 2px;
            flex: 1;
            text-align: left;
        ">{track.upper()}</h1>
    </div>
""", unsafe_allow_html=True)

# LIVE BANKROLL
st.markdown(f"""
    <div style="text-align: center; margin-bottom: 35px;">
        <div style="font-size: 2.3rem; font-weight: 300; color: #ffffff; text-shadow: 0 0 20px rgba(255,255,255,0.3); line-height: 1; margin-bottom: 8px;">
            ₪{current_bal:,.2f}
        </div>
        <div style="font-size: 0.8rem; font-weight: 600; color: #cccccc; letter-spacing: 3px; text-transform: uppercase;">
            LIVE BANKROLL
        </div>
    </div>
""", unsafe_allow_html=True)

# METRICS
if not df.empty:
    f_df = df[df['Comp'] == track].copy()
else:
    f_df = pd.DataFrame()
if not f_df.empty:
    m_exp = f_df['Expense'].sum(); m_inc = f_df['Income'].sum(); m_net = m_inc - m_exp
else: m_exp = 0.0; m_inc = 0.0; m_net = 0.0

c1, c2, c3 = st.columns(3)
with c1: st.markdown(f"""<div class="custom-metric-box"><div class="metric-card-label">TOTAL EXPENSES</div><div class="metric-card-value">₪{m_exp:,.0f}</div></div>""", unsafe_allow_html=True)
with c2: st.markdown(f"""<div class="custom-metric-box"><div class="metric-card-label">TOTAL REVENUE</div><div class="metric-card-value">₪{m_inc:,.0f}</div></div>""", unsafe_allow_html=True)
with c3:
    # ROBUST COLOR LOGIC
    if m_net >= 0:
        color_net = "#2d6a4f"
    else:
        color_net = "#d32f2f"
    st.markdown(f"""<div class="custom-metric-box"><div class="metric-card-label">NET PROFIT</div><div class="metric-card-value" style="color: {color_net} !important;">₪{m_net:,.0f}</div></div>""", unsafe_allow_html=True)

# NEXT BET
next_val = next_stakes.get(track, 30.0)
st.markdown(f"""
    <div style="text-align: center; margin: 30px 0;">
        <span style="font-size: 1.4rem; color: white; font-weight: bold;">Next Bet: </span>
        <span style="font-size: 1.6rem; color: #4CAF50; font-weight: 900; text-shadow: 0 0 10px rgba(76,175,80,0.6);">₪{next_val:,.0f}</span>
    </div>
""", unsafe_allow_html=True)

# FORM & CHART
col_form, col_chart = st.columns([1, 1])
with col_form:
    with st.form("new_match"):
        st.subheader("Add Match")
        h_team = st.text_input("Home Team", value="Brighton" if track == "Brighton" else "")
        a_team = st.text_input("Away Team")
        odds_val = st.number_input("Odds", value=3.2, step=0.1)
        stake_val = st.number_input("Stake", value=float(next_val), step=10.0)
        result_val = st.radio("Result", ["Draw (X)", "No Draw"], horizontal=True)
        if st.form_submit_button("Submit Game", use_container_width=True):
            if h_team and a_team:
                worksheet.append_row([str(datetime.date.today()), track, h_team, a_team, odds_val, result_val, stake_val, 0.0])
                st.toast("Match Added!", icon="✅")
                st.rerun()
            else: st.warning("Please enter team names")

with col_chart:
    st.subheader("Performance")
    if not f_df.empty:
        f_df['Balance'] = saved_br + (f_df['Income'].cumsum() - f_df['Expense'].cumsum())
        fig = px.line(f_df, y='Balance', x=f_df.index, title=None)
        fig.update_traces(line_color='#00ff88', line_width=3)
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0.2)',
            font=dict(color='white'), margin=dict(l=20, r=20, t=20, b=20), height=300
        )
        st.plotly_chart(fig, use_container_width=True)
        wins = len(f_df[f_df['Status'] == "✅ Won"]); losses = len(f_df[f_df['Status'] == "❌ Lost"])
        rate = (wins / len(f_df) * 100) if len(f_df) > 0 else 0
        st.caption(f"Win Rate: {rate:.1f}% ({wins} W / {losses} L)")

# LOG
st.subheader("📜 Activity Log")
if not f_df.empty:
    def highlight_results(row):
        bg = '#d1e7dd' if 'Won' in str(row['Status']) else '#f8d7da'
        return [f'background-color: {bg}'] * len(row)
    display_df = f_df[['Date', 'Match', 'Odds', 'Expense', 'Income', 'Net Profit', 'Status', 'ROI']].copy()
    display_df = display_df.sort_index(ascending=False)
    st.dataframe(
        display_df.style.apply(highlight_results, axis=1).format({
            "Odds": "{:.2f}", "Expense": "{:,.0f}", "Income": "{:,.0f}", "Net Profit": "{:,.0f}"
        }),
        use_container_width=True, hide_index=True
    )
else: st.info("No matches found.")

with st.expander("🛠️ Admin Actions"):
    if st.button("Undo Last Entry"):
        if len(raw_data) > 0:
            try: worksheet.delete_rows(len(raw_data) + 1); st.rerun()
            except: st.error("Error")
        else: st.warning("Empty")