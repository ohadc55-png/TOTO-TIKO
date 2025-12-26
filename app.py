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
    
    .pro-header-container {
        padding: 30px 20px;
        border-radius: 16px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        text-align: center;
        margin-bottom: 35px;
        display: flex;
        align-items: center;
        justify-content: center;
        border-left: 10px solid #2d6a4f;
    }

    .pro-header-text {
        margin: 0;
        font-family: 'Montserrat', sans-serif;
        font-weight: 900;
        font-size: 3rem;
        text-transform: uppercase;
        letter-spacing: 2px;
    }

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

# --- Google Sheets Connection ---
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
    except:
        return False

# --- Logic: Martingale Calculation with ROI Tracking ---
def calculate_parallel_status(raw_data, br_base, af_base):
    processed_games = []
    comp_states = {"Brighton": float(br_base), "Africa Cup of Nations": float(af_base)}
    cycle_investments = {"Brighton": 0.0, "Africa Cup of Nations": 0.0}

    for i, row in enumerate(raw_data):
        try:
            comp = str(row.get('Competition', 'Brighton')).strip()
            if comp not in comp_states:
                comp_states[comp] = float(br_base if "Brighton" in comp else af_base)
                cycle_investments[comp] = 0.0
            
            odds = float(str(row.get('Odds', 1)).replace(',', '.'))
            res_str = str(row.get('Result', '')).strip()
            recorded_stake = float(row.get('Stake', comp_states[comp]))

            cycle_investments[comp] += recorded_stake
            is_win = "Draw (X)" in res_str
            
            if is_win:
                revenue = recorded_stake * odds
                chain_profit = revenue - cycle_investments[comp]
                chain_roi = (chain_profit / cycle_investments[comp]) * 100
                status = "✅ Won"
                
                # Report this info
                p_profit = chain_profit
                p_roi = f"{chain_roi:.1f}%"
                
                # Reset for next match
                comp_states[comp] = float(br_base if "Brighton" in comp else af_base)
                cycle_investments[comp] = 0.0
            else:
                revenue = 0.0
                p_profit = -recorded_stake
                p_roi = "Pending"
                status = "❌ Lost"
                comp_states[comp] = recorded_stake * 2.0
            
            processed_games.append({
                "SheetRow": i + 2, "Date": row.get('Date', ''), "Comp": comp,
                "Match": f"{row.get('Home Team', '')} vs {row.get('Away Team', '')}",
                "Odds": odds, "Stake": recorded_stake, "Status": status, 
                "Cycle Net": p_profit, "Chain ROI": p_roi
            })
        except: continue
    return processed_games, comp_states

# --- Load Data ---
raw_data, worksheet, saved_bankroll = get_data_from_sheets()

# --- Sidebar ---
with st.sidebar:
    st.title("💰 Financial Center")
    st.subheader("Current Base Bankroll")
    st.markdown(f"**₪{saved_bankroll:,.0f}**")
    
    st.divider()
    st.subheader("Manage Cash")
    trans_amount = st.number_input("Transaction Amount (₪)", min_value=0.0, value=100.0, step=50.0)
    
    col_dep, col_with = st.columns(2)
    with col_dep:
        if st.button("Deposit (+)", use_container_width=True):
            new_val = saved_bankroll + trans_amount
            if update_bankroll_value(worksheet, new_val):
                st.toast(f"Deposited ₪{trans_amount}", icon="💰")
                st.rerun()
    with col_with:
        if st.button("Withdraw (-)", use_container_width=True):
            new_val = saved_bankroll - trans_amount
            if update_bankroll_value(worksheet, new_val):
                st.toast(f"Withdrew ₪{trans_amount}", icon="💸")
                st.rerun()
                
    st.divider()
    selected_comp = st.selectbox("Track Selection", ["Brighton", "Africa Cup of Nations"])
    current_default = 30.0 if selected_comp == "Brighton" else 20.0
    base_stake = st.number_input("Base Stake (₪)", min_value=5.0, value=current_default, step=5.0)
    
    if st.button("🔄 Sync & Refresh"): st.rerun()

# --- Process Data ---
all_processed_data, next_stakes = calculate_parallel_status(raw_data, 30.0, 20.0)

if all_processed_data:
    df = pd.DataFrame(all_processed_data)
    # Calculate global P/L based on single row net (Revenue - Stake)
    # Note: Global balance uses simple summation
    global_p_l = sum([row['Cycle Net'] if row['Status'] == "✅ Won" else -row['Stake'] for row in all_processed_data])
    current_balance = saved_bankroll + global_p_l
    filtered_df = df[df['Comp'] == selected_comp].copy()
else:
    current_balance, global_p_l = saved_bankroll, 0.0
    filtered_df = pd.DataFrame()

# --- UI Branding ---
h_class = "brighton-header" if selected_comp == "Brighton" else "afcon-header"
t_class = "brighton-text" if selected_comp == "Brighton" else "afcon-text"
st.markdown(f"<div class='pro-header-container {h_class}'><h1 class='pro-header-text {t_class}'>{selected_comp.upper()} HUB</h1></div>", unsafe_allow_html=True)

# --- Bankroll Dashboard ---
c1, c2, c3 = st.columns([1, 2, 1])
with c2:
    st.markdown(f"<h2 style='text-align: center;'>Live Balance: ₪{current_balance:,.0f}</h2>", unsafe_allow_html=True)
    health = min(max(current_balance / saved_bankroll, 0.0), 2.0) / 2.0 if saved_bankroll != 0 else 0.5
    st.progress(health)
    p_color = "green" if global_p_l >= 0 else "red"
    st.markdown(f"<p style='text-align: center; color: {p_color}; font-weight: bold;'>Net Betting P/L: ₪{global_p_l:,.0f}</p>", unsafe_allow_html=True)

# --- Track Metrics ---
col1, col2, col3 = st.columns(3)
t_inv = filtered_df['Stake'].sum() if not filtered_df.empty else 0.0
t_net = filtered_df[filtered_df['Status'] == "✅ Won"]['Cycle Net'].sum() + filtered_df[filtered_df['Status'] == "❌ Lost"]['Cycle Net'].sum()
col1.markdown(f"<div class='metric-card'><b>Investment</b><br>₪{t_inv:,.0f}</div>", unsafe_allow_html=True)
col2.markdown(f"<div class='metric-card'><b>Track Net Profit</b><br>₪{t_net:,.0f}</div>", unsafe_allow_html=True)
col3.markdown(f"<div class='metric-card'><b>Total Entries</b><br>{len(filtered_df)}</div>", unsafe_allow_html=True)

st.write("")

# --- Input Section ---
m1, m2 = st.columns(2)
with m1:
    st.markdown("### 🏟️ Match Entry")
    with st.form("match_form", clear_on_submit=True):
        d_in = st.date_input("Date", datetime.date.today())
        h_t = st.text_input("Home", value="Brighton" if selected_comp == "Brighton" else "")
        a_t = st.text_input("Away")
        o_in = st.number_input("Odds (X)", value=3.2, step=0.1)
        rec_stake_auto = next_stakes.get(selected_comp, base_stake)
        final_stake = st.number_input("Final Stake (₪)", min_value=1.0, value=float(rec_stake_auto), step=5.0)
        r_in = st.radio("Result", ["Draw (X)", "No Draw"], horizontal=True)
        if st.form_submit_button("🚀 SYNC MATCH"):
            if h_t and a_t:
                worksheet.append_row([str(d_in), selected_comp, h_t, a_t, o_in, r_in, final_stake, 0.0])
                st.toast("Match Saved!", icon="✅")
                st.rerun()

with m2:
    st.markdown("### 🧠 Live Intelligence")
    st.markdown(f"<div class='strategy-box'><h4>Suggested Stake: ₪{rec_stake_auto}</h4><p>Sequence for {selected_comp}</p></div>", unsafe_allow_html=True)
    if not filtered_df.empty:
        # Simple cumulative growth for the chart
        filtered_df['Cumulative'] = saved_bankroll + (filtered_df['Cycle Net'].cumsum())
        fig = px.area(filtered_df, y='Cumulative', title="Bankroll Growth (₪)")
        fig.update_traces(line_color='#2d6a4f', fillcolor='rgba(45, 106, 79, 0.2)')
        fig.update_layout(height=250, margin=dict(l=0,r=0,t=30,b=0), paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)

# --- Activity Log עם העמודות החדשות ---
if not filtered_df.empty:
    st.markdown("### 📜 Activity Log")
    
    # עיצוב טבלה - צבעים לפי סטטוס
    def highlight_results(row):
        color = '#d4edda' if 'Won' in row['Status'] else '#f8d7da'
        return [f'background-color: {color}'] * len(row)

    # הצגת הטבלה עם העמודות החדשות
    st.dataframe(
        filtered_df[['Date', 'Match', 'Odds', 'Stake', 'Status', 'Cycle Net', 'Chain ROI']].style.apply(highlight_results, axis=1),
        use_container_width=True, 
        hide_index=True
    )

with st.expander("🛠️ Admin Tools"):
    if st.button("Undo Last Entry"):
        worksheet.delete_rows(len(raw_data) + 1)
        st.rerun()