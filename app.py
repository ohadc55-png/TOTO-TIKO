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

# --- ADVANCED CUSTOM CSS ---
st.markdown("""
    <style>
    /* Main App Background */
    .stApp { background-color: #f0f2f6; }
    
    /* Headers Styling */
    .main-header { color: #1b4332; text-align: center; font-size: 2.5rem; font-weight: 800; margin-bottom: 1rem; }
    
    /* Metric Cards Styling */
    .metric-card { 
        background-color: white; 
        padding: 20px; 
        border-radius: 15px; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.1); 
        border-left: 5px solid #2d6a4f; 
    }
    
    /* Modern Button Styling */
    div.stButton > button {
        width: 100%;
        border-radius: 12px;
        height: 3em;
        background-color: #2d6a4f;
        color: white;
        font-weight: bold;
        border: none;
        transition: all 0.3s ease;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    /* Button Hover Effect */
    div.stButton > button:hover {
        background-color: #1b4332;
        color: #d8f3dc;
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.15);
        border: none;
    }

    /* Form and Strategy Box */
    div[data-testid="stForm"] { background-color: white; border-radius: 15px; padding: 30px; box-shadow: 0 10px 25px rgba(0,0,0,0.05); }
    .strategy-box { background-color: #e8f5e9; padding: 20px; border-radius: 12px; border: 1px solid #c8e6c9; color: #1b5e20; }
    </style>
""", unsafe_allow_html=True)

# --- Google Sheets Connection ---
def get_data_from_sheets():
    try:
        gc = gspread.service_account_from_dict(st.secrets["service_account"])
        sh = gc.open_by_url(st.secrets["sheet_url"])
        worksheet = sh.get_worksheet(0)
        data = worksheet.get_all_records()
        return data, worksheet
    except Exception as e:
        st.error(f"Google Sheets Connection Error: {e}")
        return [], None

# --- Logic: Parallel Calculation & Bankroll Analysis ---
def calculate_parallel_status(raw_data, br_base, af_base):
    processed_games = []
    comp_states = {"Brighton": br_base, "Africa Cup of Nations": af_base}
    cycle_investments = {"Brighton": 0, "Africa Cup of Nations": 0}

    if not raw_data:
        return [], comp_states

    for i, row in enumerate(raw_data):
        try:
            comp = str(row.get('Competition', 'Brighton')).strip()
            if comp not in comp_states:
                comp_states[comp] = br_base if "Brighton" in comp else af_base
                cycle_investments[comp] = 0
            
            try: odds = float(str(row.get('Odds', 1)).replace(',', '.'))
            except: odds = 1.0
            
            res_str = str(row.get('Result', '')).strip()
            
            try: recorded_stake = float(row.get('Stake', comp_states[comp]))
            except: recorded_stake = comp_states[comp]

            cycle_investments[comp] += recorded_stake
            is_win = "Draw (X)" in res_str
            
            if is_win:
                revenue = recorded_stake * odds
                status = "✅ Won"
                display_revenue = revenue
                comp_states[comp] = br_base if "Brighton" in comp else af_base
                cycle_investments[comp] = 0
            else:
                status = "❌ Lost"
                display_revenue = 0
                comp_states[comp] = recorded_stake * 2
            
            processed_games.append({
                "SheetRow": i + 2,
                "Date": row.get('Date', ''),
                "Comp": comp,
                "Match": f"{row.get('Home Team', '')} vs {row.get('Away Team', '')}",
                "Odds": odds,
                "Stake": recorded_stake,
                "Status": status,
                "Revenue": display_revenue
            })
        except Exception:
            continue
    return processed_games, comp_states

# --- Sidebar: Financial Settings ---
with st.sidebar:
    st.title("💰 Financial Center")
    total_bankroll = st.number_input("Starting Bankroll (₪)", min_value=100, value=5000, step=100)
    st.divider()
    selected_comp = st.selectbox("Track Selection", ["Brighton", "Africa Cup of Nations"])
    default_val = 30 if selected_comp == "Brighton" else 20
    base_stake = st.number_input("Track Base Stake (₪)", min_value=5, value=default_val, step=5)
    st.divider()
    if st.button("🔄 Sync & Refresh"):
        st.rerun()

# --- Data processing ---
raw_data, worksheet = get_data_from_sheets()
all_processed_data, next_stakes = calculate_parallel_status(raw_data, 30, 20)

if all_processed_data:
    full_df = pd.DataFrame(all_processed_data)
    global_inv = full_df['Stake'].sum()
    global_rev = full_df['Revenue'].sum()
    global_net = global_rev - global_inv
    current_cash = total_bankroll + global_net
    filtered_df = full_df[full_df['Comp'] == selected_comp].copy()
else:
    global_net, current_cash = 0, total_bankroll
    filtered_df = pd.DataFrame()

# --- Main UI ---
st.markdown(f"<h1 class='main-header'>⚽ {selected_comp} Hub</h1>", unsafe_allow_html=True)

# 1. Bankroll Status
c1, c2, c3 = st.columns([1, 2, 1])
with c2:
    st.markdown(f"<h3 style='text-align: center;'>Current Balance: ₪{current_cash:,.0f}</h3>", unsafe_allow_html=True)
    health_pct = min(max(current_cash / total_bankroll, 0.0), 2.0) / 2.0
    st.progress(health_pct)
    p_color = "green" if global_net >= 0 else "red"
    st.markdown(f"<p style='text-align: center; color: {p_color}; font-weight: bold;'>Total P/L: ₪{global_net:,.0f}</p>", unsafe_allow_html=True)

# 2. Track Metrics
col1, col2, col3 = st.columns(3)
t_inv = filtered_df['Stake'].sum() if not filtered_df.empty else 0
t_rev = filtered_df['Revenue'].sum() if not filtered_df.empty else 0
t_net = t_rev - t_inv

col1.markdown(f"<div class='metric-card'><b>Investment</b><br>₪{t_inv:,.0f}</div>", unsafe_allow_html=True)
col2.markdown(f"<div class='metric-card'><b>Returns</b><br>₪{t_rev:,.0f}</div>", unsafe_allow_html=True)
col3.markdown(f"<div class='metric-card'><b>Track Net</b><br>₪{t_net:,.0f}</div>", unsafe_allow_html=True)

st.write("")

# 3. Input & Strategy
m_col1, m_col2 = st.columns([1, 1])
with m_col1:
    st.markdown("### 🏟️ Match Entry")
    with st.form("input_form", clear_on_submit=True):
        d_in = st.date_input("Match Day")
        h_t = st.text_input("Home", value="Brighton" if selected_comp == "Brighton" else "")
        a_t = st.text_input("Away")
        o_in = st.number_input("Odds", value=3.2)
        r_in = st.radio("Result", ["Draw (X)", "No Draw"], horizontal=True)
        if st.form_submit_button("Submit to Cloud"):
            rec_stake = next_stakes.get(selected_comp, base_stake)
            worksheet.append_row([str(d_in), selected_comp, h_t, a_t, o_in, r_in, rec_stake, 0])
            st.toast("Match Saved!", icon="✅")
            st.rerun()

with m_col2:
    st.markdown("### 🧠 Intelligence")
    rec_stake = next_stakes.get(selected_comp, base_stake)
    st.markdown(f"<div class='strategy-box'><h4>Next Bet: ₪{rec_stake}</h4><p>Target: Draw (X) for {selected_comp}</p></div>", unsafe_allow_html=True)
    if not filtered_df.empty:
        filtered_df['Growth'] = filtered_df['Revenue'].cumsum() - filtered_df['Stake'].cumsum()
        fig = px.line(filtered_df, y='Growth', title="Track Curve")
        fig.update_traces(line_color='#2d6a4f')
        st.plotly_chart(fig, use_container_width=True)

# 4. History
if not filtered_df.empty:
    st.markdown("### 📜 Activity Log")
    st.dataframe(filtered_df.drop(columns=['SheetRow']), use_container_width=True, hide_index=True)

# 5. Management
with st.expander("🛠️ Admin Tools"):
    if raw_data:
        if st.button("Undo Last Entry"):
            worksheet.delete_rows(len(raw_data) + 1)
            st.rerun()
    if st.button("FACTORY RESET"):
        worksheet.resize(rows=1)
        st.rerun()