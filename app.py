import streamlit as st
import pandas as pd
import plotly.express as px
import gspread
import datetime

# --- Page Configuration ---
st.set_page_config(
    page_title="Elite Football Tracker | Pro Branding",
    layout="wide",
    page_icon="🏟️",
    initial_sidebar_state="expanded"
)

# --- ADVANCED UX/UI CSS ---
bg_img_url = "https://i.postimg.cc/GmFZ4KS7/Gemini-Generated-Image-k1h11zk1h11zk1h1.png"

st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;700;900&family=Inter:wght@400;700&display=swap');
    
    /* Background Setup */
    [data-testid="stAppViewContainer"] {{
        background-image: linear-gradient(rgba(0, 0, 0, 0.4), rgba(0, 0, 0, 0.7)), url("{bg_img_url}");
        background-attachment: fixed;
        background-size: cover;
        background-position: center;
        font-family: 'Inter', sans-serif;
    }}

    [data-testid="stHeader"] {{ background: rgba(0,0,0,0); }}

    /* Main Content Area */
    .main .block-container {{
        background-color: rgba(0, 0, 0, 0.25);
        backdrop-filter: blur(25px);
        border-radius: 30px;
        padding: 50px;
        margin-top: 20px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 15px 50px rgba(0,0,0,0.8);
    }}

    /* Branded Banner Styling with Logo Support */
    .pro-header-container {{
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 30px;
        padding: 20px;
        border-radius: 20px;
        margin-bottom: 40px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.4);
        border: 1px solid rgba(255,255,255,0.2);
    }}
    
    .banner-logo {{
        height: 100px;
        filter: drop-shadow(2px 4px 8px rgba(0,0,0,0.5));
    }}

    .brighton-banner {{
        background: linear-gradient(90deg, #0057B8, #FFFFFF, #4CABFF);
        background-size: 200% auto;
    }}
    .afcon-banner {{
        background: linear-gradient(90deg, #CE1126, #FCD116, #007A33);
        background-size: 200% auto;
    }}

    .pro-header-text {{
        font-family: 'Montserrat', sans-serif;
        font-weight: 900;
        font-size: 3.2rem;
        text-transform: uppercase;
        letter-spacing: 5px;
        margin: 0;
        color: white;
        text-shadow: 3px 3px 15px rgba(0,0,0,0.6);
    }}
    
    .brighton-text-fix {{
        color: #0057B8 !important;
        text-shadow: 1px 1px 2px rgba(255,255,255,0.5) !important;
    }}

    /* Dashboard Metrics */
    .live-balance-value {{
        font-family: 'Montserrat', sans-serif;
        font-size: 6rem;
        font-weight: 900;
        color: #ffffff;
        text-align: center;
        text-shadow: 0 0 30px rgba(0,0,0,1);
    }}
    .live-balance-label {{
        text-align: center;
        font-size: 1.2rem;
        letter-spacing: 10px;
        color: rgba(255,255,255,0.7);
        text-transform: uppercase;
        margin-bottom: 40px;
    }}

    .pro-metric-card {{ 
        background: rgba(255, 255, 255, 0.98); 
        padding: 30px; 
        border-radius: 22px; 
        flex: 1; 
        text-align: center;
        box-shadow: 0 12px 40px rgba(0,0,0,0.5);
    }}
    .pro-metric-label {{ font-size: 0.9rem; color: #555; font-weight: 800; text-transform: uppercase; }}
    .pro-metric-value {{ font-size: 2.5rem; font-weight: 900; color: #111; font-family: 'Montserrat', sans-serif; }}

    /* Sidebar & Components */
    [data-testid="stSidebar"] {{ background-color: rgba(0, 0, 0, 0.7) !important; backdrop-filter: blur(20px); }}
    div[data-testid="stForm"] {{ background: rgba(255, 255, 255, 0.95); border-radius: 25px; padding: 35px; color: #111; }}
    .stDataFrame {{ background: rgba(255, 255, 255, 0.95) !important; border-radius: 20px; }}
    </style>
""", unsafe_allow_html=True)

# --- Data & Logic (Functions) ---
def get_data_from_sheets():
    try:
        gc = gspread.service_account_from_dict(st.secrets["service_account"])
        sh = gc.open_by_url(st.secrets["sheet_url"])
        worksheet = sh.get_worksheet(0)
        data = worksheet.get_all_records()
        try:
            val = worksheet.cell(1, 10).value
            initial_bankroll = float(val) if val else 5000.0
        except: initial_bankroll = 5000.0
        return data, worksheet, initial_bankroll
    except Exception as e:
        st.error(f"Sync Error: {e}")
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

    for i, row in enumerate(raw_data):
        try:
            comp = str(row.get('Competition', 'Brighton')).strip()
            odds = float(str(row.get('Odds', 1)).replace(',', '.'))
            res = str(row.get('Result', '')).strip()
            exp = float(row.get('Stake', next_bets[comp]))
            cycle_invest[comp] += exp
            is_win = "Draw (X)" in res
            
            if is_win:
                inc = exp * odds
                net = inc - cycle_invest[comp]
                roi = f"{(net / cycle_invest[comp]) * 100:.1f}%"
                next_bets[comp] = float(br_base if "Brighton" in comp else af_base)
                cycle_invest[comp] = 0.0
                status = "✅ Won"
            else:
                inc, net, roi = 0.0, -exp, "N/A"
                next_bets[comp] = exp * 2.0
                status = "❌ Lost"
            
            processed.append({
                "Date": row.get('Date', ''), "Comp": comp, "Match": f"{row.get('Home Team', '')} vs {row.get('Away Team', '')}",
                "Odds": odds, "Expense": exp, "Income": inc, "Net Profit": net, "Status": status, "ROI": roi
            })
        except: continue
    return processed, next_bets

# --- Main App Execution ---
raw_data, worksheet, saved_br = get_data_from_sheets()
processed, next_stakes = calculate_logic(raw_data, 30.0, 20.0)

if processed:
    df = pd.DataFrame(processed)
    current_bal = saved_br + (df['Income'].sum() - df['Expense'].sum())
else:
    current_bal, df = saved_br, pd.DataFrame()

# --- Sidebar ---
with st.sidebar:
    st.markdown("<h2 style='color:white; letter-spacing:2px;'>WALLET CONTROL</h2>", unsafe_allow_html=True)
    st.metric("Base Bankroll", f"₪{saved_br:,.0f}")
    amt = st.number_input("Transaction Amount", min_value=0.0, value=100.0)
    c1, c2 = st.columns(2)
    if c1.button("Deposit"):
        if update_bankroll(worksheet, saved_br + amt): st.rerun()
    if c2.button("Withdraw"):
        if update_bankroll(worksheet, saved_br - amt): st.rerun()
    st.divider()
    track = st.selectbox("Current Track", ["Brighton", "Africa Cup of Nations"])
    if st.button("🔄 Sync Cloud"): st.rerun()

# --- Banner Logic with Logos ---
if track == "Brighton":
    banner_class = "brighton-banner"
    text_class = "brighton-text-fix"
    logo_url = "https://i.postimg.cc/tnjbtrLC/Brighton-Hove-Albion-logo.png"
else:
    banner_class = "afcon-banner"
    text_class = ""
    logo_url = "https://i.postimg.cc/8fSGByqk/2025-Africa-Cup-of-Nations-logo.png"

st.markdown(f"""
    <div class='pro-header-container {banner_class}'>
        <img src='{logo_url}' class='banner-logo'>
        <h1 class='pro-header-text {text_class}'>{track}</h1>
    </div>
""", unsafe_allow_html=True)

# --- Hero Stats ---
st.markdown(f"<div class='live-balance-value'>₪{current_bal:,.2f}</div>", unsafe_allow_html=True)
st.markdown("<div class='live-balance-label'>LIVE TOTAL BANKROLL</div>", unsafe_allow_html=True)

f_df = df[df['Comp'] == track] if not df.empty else pd.DataFrame()
t_exp, t_inc = f_df['Expense'].sum() if not f_df.empty else 0.0, f_df['Income'].sum() if not f_df.empty else 0.0
t_net = t_inc - t_exp

col1, col2, col3 = st.columns(3)
with col1: st.markdown(f"<div class='pro-metric-card'><div class='pro-metric-label'>Total Outbound</div><div class='pro-metric-value'>₪{t_exp:,.0f}</div></div>", unsafe_allow_html=True)
with col2: st.markdown(f"<div class='pro-metric-card'><div class='pro-metric-label'>Total Inbound</div><div class='pro-metric-value'>₪{t_inc:,.0f}</div></div>", unsafe_allow_html=True)
with col3: st.markdown(f"<div class='pro-metric-card' style='border-bottom: 8px solid {'#2d6a4f' if t_net >= 0 else '#ce1126'}'><div class='pro-metric-label'>Track Net Profit</div><div class='pro-metric-value' style='color: {'#1b4332' if t_net >= 0 else '#ce1126'}'>₪{t_net:,.0f}</div></div>", unsafe_allow_html=True)

# --- Forms & Viz ---
st.write("")
c_form, c_viz = st.columns([1, 1.3])
with c_form:
    with st.form("match_entry"):
        st.markdown("<h3 style='color:#111; margin-top:0;'>Match Entry</h3>", unsafe_allow_html=True)
        h = st.text_input("Home", value="Brighton" if track == "Brighton" else "")
        a = st.text_input("Away")
        o = st.number_input("Odds (X)", value=3.2)
        s = st.number_input("Stake (Expense)", value=float(next_stakes[track]))
        r = st.radio("Result", ["Draw (X)", "No Draw"], horizontal=True)
        if st.form_submit_button("SYNC MATCH 🚀"):
            worksheet.append_row([str(datetime.date.today()), track, h, a, o, r, s, 0.0])
            st.rerun()

with c_viz:
    if not f_df.empty:
        f_df['Growth'] = saved_br + (f_df['Income'].cumsum() - f_df['Expense'].cumsum())
        fig = px.area(f_df, y='Growth', title="Bankroll Evolution")
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white", margin=dict(l=0,r=0,t=40,b=0))
        fig.update_traces(line_color='#2d6a4f', fillcolor='rgba(45, 106, 79, 0.4)')
        st.plotly_chart(fig, use_container_width=True)

# --- Log ---
st.write("")
st.markdown("<h3 style='color:white; text-shadow:2px 2px 10px #000;'>📜 Activity Log</h3>", unsafe_allow_html=True)
if not f_df.empty:
    st.dataframe(f_df[['Date', 'Match', 'Odds', 'Expense', 'Income', 'Status', 'ROI']].sort_index(ascending=False), use_container_width=True, hide_index=True)

with st.expander("🛠️ Admin"):
    if st.button("Delete Last Record"):
        worksheet.delete_rows(len(raw_data) + 1)
        st.rerun()