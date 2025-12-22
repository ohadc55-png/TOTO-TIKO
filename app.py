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

# --- Modern Custom CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #f0f2f6; }
    .main-header { color: #1b4332; text-align: center; font-size: 2.5rem; font-weight: 800; margin-bottom: 1rem; }
    .metric-card { background-color: white; padding: 20px; border-radius: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); border-left: 5px solid #2d6a4f; }
    .stMetric { background-color: transparent !important; }
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
            
            try:
                odds = float(str(row.get('Odds', 1)).replace(',', '.'))
            except:
                odds = 1.0
            
            res_str = str(row.get('Result', '')).strip()
            
            try:
                recorded_stake = float(row.get('Stake', comp_states[comp]))
            except:
                recorded_stake = comp_states[comp]

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
    st.image("https://cdn-icons-png.flaticon.com/512/805/805401.png", width=100)
    st.title("Financial Center")
    
    # Shared Bankroll Setting
    total_bankroll = st.number_input("Starting Bankroll (₪)", min_value=100, value=5000, step=100)
    
    st.divider()
    selected_comp = st.selectbox("Track Selection", ["Brighton", "Africa Cup of Nations"])
    
    # Dynamic defaults for current session
    default_val = 30 if selected_comp == "Brighton" else 20
    base_stake = st.number_input("Track Base Stake (₪)", min_value=5, value=default_val, step=5)
    
    st.divider()
    if st.button("🔄 Sync & Refresh"):
        st.rerun()

# --- Data processing ---
raw_data, worksheet = get_data_from_sheets()
all_processed_data, next_stakes = calculate_parallel_status(raw_data, 30, 20)

# Global Metrics (All Tracks)
if all_processed_data:
    full_df = pd.DataFrame(all_processed_data)
    global_inv = full_df['Stake'].sum()
    global_rev = full_df['Revenue'].sum()
    global_net = global_rev - global_inv
    current_cash = total_bankroll + global_net
    
    # Filter for UI view
    filtered_df = full_df[full_df['Comp'] == selected_comp].copy()
else:
    global_net = 0
    current_cash = total_bankroll
    filtered_df = pd.DataFrame()

# --- Main UI ---
st.markdown(f"<h1 class='main-header'>⚽ {selected_comp} Strategy</h1>", unsafe_allow_html=True)

# 1. Global Bankroll Status (Top Bar)
with st.container():
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        profit_color = "green" if global_net >= 0 else "red"
        st.markdown(f"<h3 style='text-align: center;'>Bankroll Health: ₪{current_cash:,.0f}</h3>", unsafe_allow_html=True)
        health_pct = min(max(current_cash / total_bankroll, 0.0), 2.0) / 2.0
        st.progress(health_pct)
        st.markdown(f"<p style='text-align: center; color: {profit_color};'>Overall P/L: ₪{global_net:,.0f}</p>", unsafe_allow_html=True)

st.write("")

# 2. Track Specific Metrics
col1, col2, col3 = st.columns(3)
if not filtered_df.empty:
    t_inv = filtered_df['Stake'].sum()
    t_rev = filtered_df['Revenue'].sum()
    t_net = t_rev - t_inv
else:
    t_inv, t_rev, t_net = 0, 0, 0

with col1:
    st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
    st.metric("Track Investment", f"₪{t_inv:,.0f}")
    st.markdown("</div>", unsafe_allow_html=True)
with col2:
    st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
    st.metric("Track Returns", f"₪{t_rev:,.0f}")
    st.markdown("</div>", unsafe_allow_html=True)
with col3:
    st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
    st.metric("Track Net P/L", f"₪{t_net:,.0f}", delta=t_net)
    st.markdown("</div>", unsafe_allow_html=True)

st.write("")

# 3. Dynamic Form & Strategy
m_col1, m_col2 = st.columns([1, 1])

with m_col1:
    st.markdown("### 🏟️ Match Deployment")
    with st.form("modern_input_form", clear_on_submit=True):
        d_in = st.date_input("Match Day", datetime.date.today())
        h_t = st.text_input("Home", value="Brighton" if selected_comp == "Brighton" else "")
        a_t = st.text_input("Away")
        o_in = st.number_input("Draw Odds", min_value=1.0, value=3.2, step=0.1)
        r_in = st.radio("Outcome", ["Draw (X)", "No Draw"], horizontal=True)
        
        if st.form_submit_button("Submit Match to Cloud", use_container_width=True):
            if h_t and a_t:
                # Recommended stake from engine
                rec_stake = next_stakes.get(selected_comp, base_stake)
                new_row = [str(d_in), selected_comp, h_t, a_t, o_in, r_in, rec_stake, 0]
                worksheet.append_row(new_row)
                st.toast("Match Synced to Cloud!", icon="🚀")
                st.rerun()

with m_col2:
    st.markdown("### 🧠 Live Intelligence")
    rec_stake = next_stakes.get(selected_comp, base_stake)
    st.markdown(f"""
        <div class='strategy-box'>
            <h4>Next Strategic Move</h4>
            <p>Based on Martingale sequence for <b>{selected_comp}</b>:</p>
            <h2 style='margin: 0;'>Bet ₪{rec_stake} on Draw</h2>
            <p style='font-size: 0.8rem; margin-top: 10px;'>Target Odds: 3.00 or higher</p>
        </div>
    """, unsafe_allow_html=True)
    
    if not filtered_df.empty:
        filtered_df['Growth'] = filtered_df['Revenue'].cumsum() - filtered_df['Stake'].cumsum()
        fig = px.line(filtered_df, x=filtered_df.index, y='Growth', title="Track Performance Curve")
        fig.update_traces(line_color='#2d6a4f', line_width=3)
        fig.update_layout(height=250, margin=dict(l=0, r=0, t=30, b=0), paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)

# 4. Activity Log
st.markdown("### 📜 Recent Activity Log")
if not filtered_df.empty:
    def style_status(val):
        if 'Won' in str(val): return 'background-color: #d4edda; color: #155724'
        if 'Lost' in str(val): return 'background-color: #f8d7da; color: #721c24'
        return ''
    
    st.dataframe(
        filtered_df.drop(columns=['SheetRow']).style.applymap(style_status, subset=['Status']),
        use_container_width=True, hide_index=True
    )

# 5. Management
st.write("---")
with st.expander("🛠️ Advanced Record Management"):
    if raw_data:
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Undo Last Entry"):
                worksheet.delete_rows(len(raw_data) + 1)
                st.rerun()
        with c2:
            match_map = {f"{g['Date']} - {g['Match']}": g['SheetRow'] for g in all_processed_data}
            to_del = st.selectbox("Select match to delete", options=list(match_map.keys()))
            if st.button("Delete Selected"):
                worksheet.delete_rows(match_map[to_del])
                st.rerun()
    
    if st.button("FACTORY RESET (Delete All)"):
        worksheet.resize(rows=1)
        st.rerun()