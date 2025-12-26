import streamlit as st
import pandas as pd
import plotly.express as px
import gspread
import datetime

# --- Page Configuration ---
st.set_page_config(
    page_title="Elite Football Tracker",
    layout="wide",
    page_icon="🏟️",
    initial_sidebar_state="expanded"
)

# --- THE CORRECTED CSS SELECTOR FOR BACKGROUND ---
bg_img_url = "https://i.postimg.cc/Xr0jkv6G/Gemini-Generated-Image-lscdsmlscdsmlscd.png"

st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@700;900&display=swap');
    
    /* Targeting the specific Streamlit container for the background */
    [data-testid="stAppViewContainer"] {{
        background-image: linear-gradient(rgba(0, 0, 0, 0.5), rgba(0, 0, 0, 0.7)), url("{bg_img_url}");
        background-attachment: fixed;
        background-size: cover;
        background-position: center;
    }}

    /* Ensuring the header is transparent to show the background */
    [data-testid="stHeader"] {{
        background: rgba(0,0,0,0);
    }}

    /* Main container styling - Glassmorphism */
    .main .block-container {{
        background-color: rgba(0, 0, 0, 0.2); 
        backdrop-filter: blur(10px);
        border-radius: 25px;
        padding: 40px;
        color: white;
        margin-top: 20px;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }}

    /* Dashboard Header */
    .pro-header-container {{
        padding: 20px;
        border-radius: 20px;
        text-align: center;
        margin-bottom: 30px;
        background: rgba(255, 255, 255, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.2);
    }}
    .pro-header-text {{
        font-family: 'Montserrat', sans-serif;
        font-weight: 900;
        font-size: 3.5rem;
        color: white;
        text-transform: uppercase;
        text-shadow: 2px 2px 10px rgba(0,0,0,0.5);
    }}

    /* Metric Cards - High Contrast for Readability */
    .metric-card {{ 
        background-color: rgba(255, 255, 255, 0.95); 
        padding: 25px; 
        border-radius: 18px; 
        text-align: center;
        box-shadow: 0 8px 32px rgba(0,0,0,0.4);
    }}
    .metric-label {{ font-size: 1rem; color: #444; font-weight: bold; text-transform: uppercase; }}
    .metric-value {{ font-size: 2.2rem; font-weight: 900; color: #1b4332; }}

    /* Sidebar Transparency */
    [data-testid="stSidebar"] {{
        background-color: rgba(0, 0, 0, 0.5) !important;
        backdrop-filter: blur(15px);
    }}
    
    /* Forms and Tables */
    div[data-testid="stForm"] {{ background-color: rgba(255, 255, 255, 0.9); border-radius: 20px; padding: 30px; color: black; }}
    .stDataFrame {{ background-color: rgba(255, 255, 255, 0.9) !important; border-radius: 15px; }}
    </style>
""", unsafe_allow_html=True)

# --- Google Sheets Logic ---
def get_data_from_sheets():
    try:
        gc = gspread.service_account_from_dict(st.secrets["service_account"])
        sh = gc.open_by_url(st.secrets["sheet_url"])
        worksheet = sh.get_worksheet(0)
        data = worksheet.get_all_records()
        try:
            val = worksheet.cell(1, 10).value
            initial_bankroll = float(val) if val else 5000.0
        except:
            initial_bankroll = 5000.0
        return data, worksheet, initial_bankroll
    except Exception as e:
        st.error(f"Sync Error: {e}")
        return [], None, 5000.0

def update_bankroll(worksheet, val):
    try:
        worksheet.update_cell(1, 10, val)
        return True
    except: return False

# --- Core Logic ---
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

# --- Execution ---
raw_data, worksheet, saved_br = get_data_from_sheets()
processed, next_stakes = calculate_logic(raw_data, 30.0, 20.0)

if processed:
    df = pd.DataFrame(processed)
    current_bal = saved_br + (df['Income'].sum() - df['Expense'].sum())
else:
    current_bal, df = saved_br, pd.DataFrame()

# --- Sidebar ---
with st.sidebar:
    st.header("Wallet")
    st.metric("Base Bankroll", f"₪{saved_br:,.0f}")
    amt = st.number_input("Transaction", min_value=0.0, value=100.0)
    c1, c2 = st.columns(2)
    if c1.button("Deposit"):
        if update_bankroll(worksheet, saved_br + amt): st.rerun()
    if c2.button("Withdraw"):
        if update_bankroll(worksheet, saved_br - amt): st.rerun()
    st.divider()
    track = st.selectbox("Current Track", ["Brighton", "Africa Cup of Nations"])
    if st.button("🔄 Sync"): st.rerun()

# --- Dashboard UI ---
st.markdown(f"<div class='pro-header-container'><h1 class='pro-header-text'>{track}</h1></div>", unsafe_allow_html=True)
st.markdown(f"<h1 style='text-align: center; font-size: 4rem; text-shadow: 2px 2px 15px #000;'>₪{current_bal:,.2f}</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; letter-spacing: 3px;'>LIVE BANKROLL</p>", unsafe_allow_html=True)

# Metrics Cards
f_df = df[df['Comp'] == track] if not df.empty else pd.DataFrame()
t_exp = f_df['Expense'].sum() if not f_df.empty else 0.0
t_inc = f_df['Income'].sum() if not f_df.empty else 0.0
t_net = t_inc - t_exp

col1, col2, col3 = st.columns(3)
with col1: st.markdown(f"<div class='metric-card'><p class='metric-label'>Total Out</p><p class='metric-value'>₪{t_exp:,.0f}</p></div>", unsafe_allow_html=True)
with col2: st.markdown(f"<div class='metric-card'><p class='metric-label'>Total In</p><p class='metric-value'>₪{t_inc:,.0f}</p></div>", unsafe_allow_html=True)
with col3: st.markdown(f"<div class='metric-card' style='border-bottom: 5px solid {'#2d6a4f' if t_net >= 0 else '#ce1126'}'><p class='metric-label'>Net Profit</p><p class='metric-value'>₪{t_net:,.0f}</p></div>", unsafe_allow_html=True)

# Forms and History
st.write("---")
col_form, col_viz = st.columns([1, 1.2])
with col_form:
    with st.form("match_entry"):
        st.subheader("New Entry")
        h = st.text_input("Home", value="Brighton" if track == "Brighton" else "")
        a = st.text_input("Away")
        o = st.number_input("Odds", value=3.2)
        s = st.number_input("Stake", value=float(next_stakes[track]))
        r = st.radio("Result", ["Draw (X)", "No Draw"], horizontal=True)
        if st.form_submit_button("Sync Game 🚀"):
            worksheet.append_row([str(datetime.date.today()), track, h, a, o, r, s, 0.0])
            st.rerun()

with col_viz:
    if not f_df.empty:
        f_df['Growth'] = saved_br + (f_df['Income'].cumsum() - f_df['Expense'].cumsum())
        fig = px.area(f_df, y='Growth', title="Bankroll Curve")
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white", margin=dict(l=0,r=0,t=30,b=0))
        fig.update_traces(line_color='#2d6a4f', fillcolor='rgba(45, 106, 79, 0.3)')
        st.plotly_chart(fig, use_container_width=True)

st.subheader("📜 Activity Log")
if not f_df.empty:
    st.dataframe(f_df[['Date', 'Match', 'Odds', 'Expense', 'Income', 'Status', 'ROI']].sort_index(ascending=False), use_container_width=True, hide_index=True)

with st.expander("Admin"):
    if st.button("Delete Last Entry"):
        worksheet.delete_rows(len(raw_data) + 1)
        st.rerun()