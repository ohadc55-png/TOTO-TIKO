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

# --- MODERN PROFESSIONAL CSS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@700;900&display=swap');
    .stApp { background-color: #f0f2f6; }
    .pro-header-container { padding: 30px 20px; border-radius: 16px; box-shadow: 0 8px 32px rgba(0,0,0,0.1); text-align: center; margin-bottom: 35px; border-left: 10px solid #2d6a4f; }
    .pro-header-text { margin: 0; font-family: 'Montserrat', sans-serif; font-weight: 900; font-size: 3rem; text-transform: uppercase; letter-spacing: 2px; }
    .brighton-header { background: linear-gradient(135deg, #0057B8 0%, #0077C8 50%, #4CABFF 100%); border-left-color: #FFFFFF; }
    .brighton-text { color: #FFFFFF; text-shadow: 0px 2px 10px rgba(0,0,0,0.3); }
    .afcon-header { background: linear-gradient(120deg, #CE1126 25%, #FCD116 50%, #007A33 85%); border-left-color: #CE1126; }
    .afcon-text { color: #FFFFFF; text-shadow: 2px 2px 8px rgba(0,0,0,0.6); }
    .metric-card { background-color: white; padding: 20px; border-radius: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); border-left: 5px solid #2d6a4f; text-align: center; }
    div.stButton > button { width: 100%; border-radius: 12px; height: 3.2em; background-color: #2d6a4f; color: white; font-weight: bold; border: none; transition: 0.3s; }
    div.stButton > button:hover { background-color: #1b4332; transform: translateY(-2px); }
    .strategy-box { background-color: #e8f5e9; padding: 20px; border-radius: 12px; border: 1px solid #c8e6c9; color: #1b5e20; }
    div[data-testid="stForm"] { background-color: white; border-radius: 15px; padding: 30px; box-shadow: 0 10px 25px rgba(0,0,0,0.05); }
    </style>
""", unsafe_allow_html=True)

# --- Google Sheets Connection & Bankroll Persistence ---
def get_data_from_sheets():
    try:
        gc = gspread.service_account_from_dict(st.secrets["service_account"])
        sh = gc.open_by_url(st.secrets["sheet_url"])
        worksheet = sh.get_worksheet(0)
        data = worksheet.get_all_records()
        
        # Get Initial Bankroll from Cell J1 (Column 10, Row 1)
        try:
            val = worksheet.cell(1, 10).value
            initial_bankroll = float(val) if val else 5000.0
        except:
            initial_bankroll = 5000.0
            
        return data, worksheet, initial_bankroll
    except Exception as e:
        st.error(f"Connection Error: {e}")
        return [], None, 5000.0

def update_initial_bankroll(worksheet, new_val):
    try:
        worksheet.update_cell(1, 10, new_val)
        return True
    except:
        return False

# --- Logic: Martingale Calculation ---
def calculate_parallel_status(raw_data, br_base, af_base):
    processed_games = []
    comp_states = {"Brighton": br_base, "Africa Cup of Nations": af_base}
    cycle_investments = {"Brighton": 0, "Africa Cup of Nations": 0}

    for i, row in enumerate(raw_data):
        try:
            comp = str(row.get('Competition', 'Brighton')).strip()
            if comp not in comp_states:
                comp_states[comp] = br_base if "Brighton" in comp else af_base
                cycle_investments[comp] = 0
            
            odds = float(str(row.get('Odds', 1)).replace(',', '.'))
            res_str = str(row.get('Result', '')).strip()
            recorded_stake = float(row.get('Stake', comp_states[comp]))

            cycle_investments[comp] += recorded_stake
            is_win = "Draw (X)" in res_str
            
            if is_win:
                revenue = recorded_stake * odds
                profit = revenue - cycle_investments[comp]
                status = "✅ Won"
                comp_states[comp] = br_base if "Brighton" in comp else af_base
                cycle_investments[comp] = 0
            else:
                revenue = 0
                profit = -recorded_stake
                status = "❌ Lost"
                comp_states[comp] = recorded_stake * 2
            
            processed_games.append({
                "SheetRow": i + 2, "Date": row.get('Date', ''), "Comp": comp,
                "Match": f"{row.get('Home Team', '')} vs {row.get('Away Team', '')}",
                "Odds": odds, "Stake": recorded_stake, "Status": status, 
                "Revenue": revenue, "Net": profit
            })
        except: continue
    return processed_games, comp_states

# --- Load Data ---
raw_data, worksheet, saved_initial_bankroll = get_data_from_sheets()

# --- Sidebar ---
with st.sidebar:
    st.title("💰 Financial Center")
    # Persistent Bankroll Input
    new_bankroll = st.number_input("Starting Bankroll (₪)", value=saved_initial_bankroll, step=100)
    if st.button("Save New Starting Bankroll"):
        if update_initial_bankroll(worksheet, new_bankroll):
            st.success("Bankroll Saved to Cloud!")
            st.rerun()
            
    st.divider()
    selected_comp = st.selectbox("Current Track", ["Brighton", "Africa Cup of Nations"])
    default_base = 30 if selected_comp == "Brighton" else 20
    base_stake = st.number_input("Track Base Stake (₪)", min_value=5, value=default_val if 'default_val' in locals() else default_base, key=f"bs_{selected_comp}")
    
    if st.button("🔄 Sync & Refresh"): st.rerun()

# --- Process ---
all_processed_data, next_stakes = calculate_parallel_status(raw_data, 30, 20)

if all_processed_data:
    df = pd.DataFrame(all_processed_data)
    global_p_l = df['Revenue'].sum() - df['Stake'].sum()
    current_balance = saved_initial_bankroll + global_p_l
    filtered_df = df[df['Comp'] == selected_comp].copy()
else:
    current_balance = saved_initial_bankroll
    global_p_l = 0
    filtered_df = pd.DataFrame()

# --- Header ---
h_class = "brighton-header" if selected_comp == "Brighton" else "afcon-header"
t_class = "brighton-text" if selected_comp == "Brighton" else "afcon-text"
st.markdown(f"<div class='pro-header-container {h_class}'><h1 class='pro-header-text {t_class}'>{selected_comp.upper()} HUB</h1></div>", unsafe_allow_html=True)

# --- Bankroll Dashboard ---
c1, c2, c3 = st.columns([1, 2, 1])
with c2:
    st.markdown(f"<h2 style='text-align: center;'>Live Balance: ₪{current_balance:,.0f}</h2>", unsafe_allow_html=True)
    health = min(max(current_balance / saved_initial_bankroll, 0.0), 2.0) / 2.0
    st.progress(health)
    st.markdown(f"<p style='text-align: center; color: {'green' if global_p_l >= 0 else 'red'};'>Overall P/L: ₪{global_p_l:,.0f}</p>", unsafe_allow_html=True)

# --- Track Metrics ---
col1, col2, col3 = st.columns(3)
t_inv = filtered_df['Stake'].sum() if not filtered_df.empty else 0
t_rev = filtered_df['Revenue'].sum() if not filtered_df.empty else 0
t_net = t_rev - t_inv
col1.markdown(f"<div class='metric-card'><b>Investment</b><br>₪{t_inv:,.0f}</div>", unsafe_allow_html=True)
col2.markdown(f"<div class='metric-card'><b>Returned</b><br>₪{t_rev:,.0f}</div>", unsafe_allow_html=True)
col3.markdown(f"<div class='metric-card'><b>Track Net</b><br>₪{t_net:,.0f}</div>", unsafe_allow_html=True)

# --- Input & Intel ---
m1, m2 = st.columns(2)
with m1:
    with st.form("match_form", clear_on_submit=True):
        d_in = st.date_input("Date", datetime.date.today())
        h_t = st.text_input("Home", value="Brighton" if selected_comp == "Brighton" else "")
        a_t = st.text_input("Away")
        o_in = st.number_input("Odds (X)", value=3.2)
        r_in = st.radio("Result", ["Draw (X)", "No Draw"], horizontal=True)
        if st.form_submit_button("🚀 SYNC MATCH"):
            if h_t and a_t:
                rec_stake = next_stakes.get(selected_comp, base_stake)
                worksheet.append_row([str(d_in), selected_comp, h_t, a_t, o_in, r_in, rec_stake, 0])
                st.rerun()
with m2:
    rec_stake = next_stakes.get(selected_comp, base_stake)
    st.markdown(f"<div class='strategy-box'><h4>Target: ₪{rec_stake} on Draw</h4><p>Sequence for {selected_comp}</p></div>", unsafe_allow_html=True)
    if not filtered_df.empty:
        # Equity Curve starting from Initial Bankroll
        filtered_df['Balance_Curve'] = saved_initial_bankroll + (filtered_df['Revenue'].cumsum() - filtered_df['Stake'].cumsum())
        fig = px.area(filtered_df, y='Balance_Curve', title="Cash Evolution (₪)")
        fig.update_traces(line_color='#2d6a4f', fillcolor='rgba(45, 106, 79, 0.2)')
        st.plotly_chart(fig, use_container_width=True)

# --- History ---
if not filtered_df.empty:
    st.markdown("### 📜 Activity Log")
    st.dataframe(filtered_df[['Date', 'Match', 'Odds', 'Stake', 'Status']].style.applymap(lambda v: 'background-color: #d4edda' if 'Won' in str(v) else 'background-color: #f8d7da', subset=['Status']), use_container_width=True, hide_index=True)