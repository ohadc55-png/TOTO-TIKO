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

# --- STADIUM BACKGROUND INTEGRATION ---
# Your Direct Link from Nano Banana/PostImages
bg_img_url = "https://i.postimg.cc/Xr0jkv6G/Gemini-Generated-Image-lscdsmlscdsmlscd.png"

st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@700;900&display=swap');
    
    /* Background setup */
    .stApp {{
        background-image: linear-gradient(rgba(0, 0, 0, 0.5), rgba(0, 0, 0, 0.7)), url("{bg_img_url}");
        background-attachment: fixed;
        background-size: cover;
        background-position: center;
    }}
    
    /* Glassmorphism containers */
    .main .block-container {{
        background-color: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(15px);
        border-radius: 25px;
        padding: 40px;
        color: white;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }}

    /* Header styling */
    .pro-header-container {{
        padding: 25px;
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
        letter-spacing: 3px;
        text-shadow: 2px 2px 10px rgba(0,0,0,0.5);
    }}

    /* Metrics with high contrast */
    .metric-container {{ display: flex; justify-content: space-between; gap: 20px; margin-bottom: 30px; }}
    .metric-card {{ 
        background-color: rgba(255, 255, 255, 0.95); 
        padding: 25px; 
        border-radius: 18px; 
        flex: 1; 
        text-align: center;
        box-shadow: 0 8px 32px rgba(0,0,0,0.3);
    }}
    .metric-label {{ font-size: 1rem; color: #444; font-weight: bold; text-transform: uppercase; }}
    .metric-value {{ font-size: 2.2rem; font-weight: 900; color: #1b4332; }}

    /* Transparent Sidebar */
    [data-testid="stSidebar"] {{
        background-color: rgba(0, 0, 0, 0.4) !important;
        backdrop-filter: blur(10px);
    }}
    
    /* Form fields */
    div[data-testid="stForm"] {{ 
        background-color: rgba(255, 255, 255, 0.9); 
        border-radius: 20px; 
        padding: 30px; 
        color: black; 
    }}
    
    /* Tables styling */
    .stDataFrame {{
        background-color: rgba(255, 255, 255, 0.9) !important;
        border-radius: 15px;
        overflow: hidden;
    }}
    </style>
""", unsafe_allow_html=True)

# --- Google Sheets Functions ---
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
        st.error(f"Connection Error: {e}")
        return [], None, 5000.0

def update_bankroll_value(worksheet, new_val):
    try:
        worksheet.update_cell(1, 10, new_val)
        return True
    except: return False

# --- Core Processing Logic ---
def process_tracker_logic(raw_data, br_base, af_base):
    processed = []
    next_bet_calc = {"Brighton": float(br_base), "Africa Cup of Nations": float(af_base)}
    current_cycle_invest = {"Brighton": 0.0, "Africa Cup of Nations": 0.0}

    for i, row in enumerate(raw_data):
        try:
            comp = str(row.get('Competition', 'Brighton')).strip()
            odds = float(str(row.get('Odds', 1)).replace(',', '.'))
            res_str = str(row.get('Result', '')).strip()
            expense = float(row.get('Stake', next_bet_calc[comp]))
            current_cycle_invest[comp] += expense
            is_win = "Draw (X)" in res_str
            
            if is_win:
                income = expense * odds
                net_profit = income - current_cycle_invest[comp]
                roi = (net_profit / current_cycle_invest[comp]) * 100
                status = "✅ Won"
                next_bet_calc[comp] = float(br_base if "Brighton" in comp else af_base)
                current_cycle_invest[comp] = 0.0
            else:
                income, net_profit, roi = 0.0, -expense, 0.0
                status = "❌ Lost"
                next_bet_calc[comp] = expense * 2.0
            
            processed.append({
                "Date": row.get('Date', ''), "Comp": comp,
                "Match": f"{row.get('Home Team', '')} vs {row.get('Away Team', '')}",
                "Odds": odds, "Expense": expense, "Income": income,
                "Net Profit": net_profit, "Status": status, "ROI": f"{roi:.1f}%" if is_win else "N/A"
            })
        except: continue
    return processed, next_bet_calc

# --- Main App Execution ---
raw_data, worksheet, saved_bankroll = get_data_from_sheets()
processed_games, next_stakes = process_tracker_logic(raw_data, 30.0, 20.0)

if processed_games:
    df = pd.DataFrame(processed_games)
    total_net = df['Income'].sum() - df['Expense'].sum()
    current_balance = saved_bankroll + total_net
else:
    current_balance = saved_bankroll
    df = pd.DataFrame()

# --- Sidebar Management ---
with st.sidebar:
    st.title("💸 Wallet")
    st.metric("Base Bankroll", f"₪{saved_bankroll:,.0f}")
    amount = st.number_input("Transaction", min_value=0.0, value=100.0, step=50.0)
    c_dep, c_wit = st.columns(2)
    if c_dep.button("Deposit"):
        if update_bankroll_value(worksheet, saved_bankroll + amount): st.rerun()
    if c_wit.button("Withdraw"):
        if update_bankroll_value(worksheet, saved_bankroll - amount): st.rerun()
    st.divider()
    selected_comp = st.selectbox("Current Track", ["Brighton", "Africa Cup of Nations"])
    if st.button("🔄 Sync Cloud"): st.rerun()

# --- Visual UI ---
st.markdown(f"<div class='pro-header-container'><h1 class='pro-header-text'>{selected_comp}</h1></div>", unsafe_allow_html=True)

st.markdown(f"<h1 style='text-align: center; font-size: 3.5rem; text-shadow: 4px 4px 15px rgba(0,0,0,0.8);'>₪{current_balance:,.2f}</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; letter-spacing: 5px; font-weight: bold;'>CURRENT LIVE BALANCE</p>", unsafe_allow_html=True)

# Metrics Cards
f_df = df[df['Comp'] == selected_comp] if not df.empty else pd.DataFrame()
track_exp = f_df['Expense'].sum() if not f_df.empty else 0.0
track_inc = f_df['Income'].sum() if not f_df.empty else 0.0
track_net = track_inc - track_exp

st.markdown(f"""
    <div class='metric-container'>
        <div class='metric-card'><div class='metric-label'>Total Out</div><div class='metric-value'>₪{track_exp:,.0f}</div></div>
        <div class='metric-card'><div class='metric-label'>Total In</div><div class='metric-value'>₪{track_inc:,.0f}</div></div>
        <div class='metric-card' style='border-bottom: 5px solid {"#2d6a4f" if track_net >= 0 else "#ce1126"}'><div class='metric-label'>Net Profit</div><div class='metric-value'>₪{track_net:,.0f}</div></div>
    </div>
""", unsafe_allow_html=True)

# Entry and Chart
col_form, col_chart = st.columns([1, 1.2])
with col_form:
    with st.form("entry"):
        st.subheader("Match Registration")
        h = st.text_input("Home", value="Brighton" if selected_comp == "Brighton" else "")
        a = st.text_input("Away")
        od = st.number_input("Odds", value=3.2)
        stk = st.number_input("Stake", value=float(next_stakes[selected_comp]))
        res = st.radio("Result", ["Draw (X)", "No Draw"], horizontal=True)
        if st.form_submit_button("Sync Game 🚀"):
            worksheet.append_row([str(datetime.date.today()), selected_comp, h, a, od, res, stk, 0.0])
            st.rerun()

with col_chart:
    if not f_df.empty:
        f_df['Chart'] = saved_bankroll + (f_df['Income'].cumsum() - f_df['Expense'].cumsum())
        fig = px.area(f_df, y='Chart', title="Performance Analytics")
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white", margin=dict(l=0,r=0,t=40,b=0))
        fig.update_traces(line_color='#2d6a4f', fillcolor='rgba(45, 106, 79, 0.3)')
        st.plotly_chart(fig, use_container_width=True)

# Detailed History
st.subheader("📜 Activity Log")
if not f_df.empty:
    st.dataframe(f_df[['Date', 'Match', 'Odds', 'Expense', 'Income', 'Status', 'ROI']].sort_index(ascending=False), use_container_width=True, hide_index=True)

with st.expander("Admin"):
    if st.button("Undo Last Entry"):
        worksheet.delete_rows(len(raw_data) + 1)
        st.rerun()