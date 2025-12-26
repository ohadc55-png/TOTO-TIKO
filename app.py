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
    
    /* Branded Header Styling */
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

    /* Metric Card Styling */
    .metric-container { display: flex; justify-content: space-between; gap: 15px; margin-bottom: 25px; }
    .metric-card { 
        background-color: white; 
        padding: 20px; 
        border-radius: 15px; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.1); 
        flex: 1; 
        text-align: center;
        border-bottom: 5px solid #2d6a4f;
    }
    .metric-label { font-size: 0.9rem; color: #666; font-weight: bold; text-transform: uppercase; }
    .metric-value { font-size: 1.8rem; font-weight: 900; color: #1b4332; }

    /* Button and Form Styling */
    div.stButton > button { width: 100%; border-radius: 12px; height: 3.2em; background-color: #2d6a4f; color: white; font-weight: bold; border: none; transition: 0.3s; }
    div.stButton > button:hover { background-color: #1b4332; transform: translateY(-2px); }
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
        # Fetch initial bankroll from cell J1
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

# --- Core Tracking Logic ---
def process_tracker_logic(raw_data, br_base, af_base):
    processed = []
    # Tracks the recommended next bet
    next_bet_calc = {"Brighton": float(br_base), "Africa Cup of Nations": float(af_base)}
    # Tracks cumulative investment within the current cycle for ROI calculation
    current_cycle_invest = {"Brighton": 0.0, "Africa Cup of Nations": 0.0}

    for i, row in enumerate(raw_data):
        try:
            comp = str(row.get('Competition', 'Brighton')).strip()
            odds = float(str(row.get('Odds', 1)).replace(',', '.'))
            res_str = str(row.get('Result', '')).strip()
            # Money out (Expense)
            expense = float(row.get('Stake', next_bet_calc[comp]))
            
            current_cycle_invest[comp] += expense
            is_win = "Draw (X)" in res_str
            
            if is_win:
                income = expense * odds # Gross winnings
                net_profit = income - current_cycle_invest[comp] # Net gain after clearing the cycle
                roi = (net_profit / current_cycle_invest[comp]) * 100
                status = "✅ Won"
                
                # Reset cycle
                next_bet_calc[comp] = float(br_base if "Brighton" in comp else af_base)
                current_cycle_invest[comp] = 0.0
            else:
                income = 0.0
                net_profit = -expense
                roi = 0.0
                status = "❌ Lost"
                # Double the stake for next bet
                next_bet_calc[comp] = expense * 2.0
            
            processed.append({
                "Date": row.get('Date', ''),
                "Comp": comp,
                "Match": f"{row.get('Home Team', '')} vs {row.get('Away Team', '')}",
                "Odds": odds,
                "Expense": expense,
                "Income": income,
                "Net Profit": net_profit if is_win else -expense,
                "Status": status,
                "ROI": f"{roi:.1f}%" if is_win else "N/A"
            })
        except: continue
    return processed, next_bet_calc

# --- Load Data ---
raw_data, worksheet, saved_bankroll = get_data_from_sheets()
processed_games, next_stakes = process_tracker_logic(raw_data, 30.0, 20.0)

# --- Global Calculations ---
if processed_games:
    df = pd.DataFrame(processed_games)
    # Filter by track for the UI
    global_expenses = df['Expense'].sum()
    global_income = df['Income'].sum()
    current_balance = saved_bankroll + (global_income - global_expenses)
else:
    global_expenses = global_income = 0.0
    current_balance = saved_bankroll
    df = pd.DataFrame()

# --- Sidebar (Finance & Tracks) ---
with st.sidebar:
    st.title("💰 Finance Center")
    st.metric("Base Bankroll (J1)", f"₪{saved_bankroll:,.0f}")
    
    st.subheader("Cash Management")
    amount = st.number_input("Transaction Amount (₪)", min_value=0.0, value=100.0, step=50.0)
    c_dep, c_wit = st.columns(2)
    if c_dep.button("Deposit (+)", use_container_width=True):
        if update_bankroll_value(worksheet, saved_bankroll + amount): st.rerun()
    if c_wit.button("Withdraw (-)", use_container_width=True):
        if update_bankroll_value(worksheet, saved_bankroll - amount): st.rerun()
    
    st.divider()
    selected_comp = st.selectbox("Track Selection", ["Brighton", "Africa Cup of Nations"])
    if st.button("🔄 Sync & Refresh"): st.rerun()

# --- Branded Header ---
h_style = "brighton-header" if selected_comp == "Brighton" else "afcon-header"
t_style = "brighton-text" if selected_comp == "Brighton" else "afcon-text"
st.markdown(f"<div class='pro-header-container {h_style}'><h1 class='pro-header-text {t_style}'>{selected_comp}</h1></div>", unsafe_allow_html=True)

# --- Live Dashboard ---
st.markdown(f"<h1 style='text-align: center; color: #1b4332; margin-bottom: 25px;'>Live Balance: ₪{current_balance:,.2f}</h1>", unsafe_allow_html=True)

# --- Track Specific Metrics (Expense, Income, Net) ---
f_df = df[df['Comp'] == selected_comp] if not df.empty else pd.DataFrame()
track_exp = f_df['Expense'].sum() if not f_df.empty else 0.0
track_inc = f_df['Income'].sum() if not f_df.empty else 0.0
track_net = track_inc - track_exp

st.markdown(f"""
    <div class='metric-container'>
        <div class='metric-card'>
            <div class='metric-label'>Total Expense (Out)</div>
            <div class='metric-value'>₪{track_exp:,.2f}</div>
        </div>
        <div class='metric-card'>
            <div class='metric-label'>Total Income (In)</div>
            <div class='metric-value'>₪{track_inc:,.2f}</div>
        </div>
        <div class='metric-card' style='border-bottom-color: {"#2d6a4f" if track_net >= 0 else "#ce1126"}'>
            <div class='metric-label'>Net Profit / Loss</div>
            <div class='metric-value'>₪{track_net:,.2f}</div>
        </div>
    </div>
""", unsafe_allow_html=True)

# --- Match Entry & Visualization ---
col_form, col_viz = st.columns([1, 1])
with col_form:
    with st.form("match_entry"):
        st.subheader("🏟️ Match Entry")
        h_team = st.text_input("Home Team", value="Brighton" if selected_comp == "Brighton" else "")
        a_team = st.text_input("Away Team")
        odds_val = st.number_input("Odds (X)", value=3.2, step=0.1)
        # Recommendation with manual overwrite
        rec_stake = float(next_stakes[selected_comp])
        stake_val = st.number_input("Stake (Expense)", value=rec_stake)
        result_val = st.radio("Result", ["Draw (X)", "No Draw"], horizontal=True)
        
        if st.form_submit_button("Sync Game to Cloud 🚀"):
            if h_team and a_team:
                worksheet.append_row([str(datetime.date.today()), selected_comp, h_team, a_team, odds_val, result_val, stake_val, 0.0])
                st.toast("Match Synchronized!", icon="✅")
                st.rerun()

with col_viz:
    if not f_df.empty:
        # Chart shows the evolution of the bankroll
        f_df['Growth_Line'] = saved_bankroll + (f_df['Income'].cumsum() - f_df['Expense'].cumsum())
        fig = px.line(f_df, x=f_df.index, y='Growth_Line', title="Live Bankroll Evolution", markers=True)
        fig.update_traces(line_color='#2d6a4f')
        st.plotly_chart(fig, use_container_width=True)

# --- Activity Log ---
st.subheader("📜 Activity Log")
if not f_df.empty:
    log_display = f_df[['Date', 'Match', 'Odds', 'Expense', 'Income', 'Net Profit', 'Status', 'ROI']].sort_index(ascending=False)
    
    def style_row(row):
        color = '#d4edda' if 'Won' in row['Status'] else '#f8d7da'
        return [f'background-color: {color}'] * len(row)

    st.dataframe(log_display.style.apply(style_row, axis=1), use_container_width=True, hide_index=True)

# --- Admin Section ---
with st.expander("🛠️ Admin Tools"):
    if st.button("Delete Last Row"):
        worksheet.delete_rows(len(raw_data) + 1)
        st.rerun()