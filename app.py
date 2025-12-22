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
    /* Import Professional Font from Google */
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@700;900&display=swap');

    .stApp { background-color: #f0f2f6; }
    
    /* --- Professional Header Banner --- */
    .pro-header-container {
        background-color: #ffffff;
        padding: 25px 20px;
        border-radius: 16px;
        box-shadow: 0 6px 20px rgba(0,0,0,0.08);
        text-align: center;
        margin-bottom: 35px;
        border-left: 8px solid #2d6a4f;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .pro-header-text {
        margin: 0;
        color: #1a1a1a;
        font-family: 'Montserrat', sans-serif;
        font-weight: 900;
        font-size: 2.8rem;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        background: linear-gradient(45deg, #1b4332, #2d6a4f);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    /* Metric Cards Styling */
    .metric-card { 
        background-color: white; 
        padding: 20px; 
        border-radius: 15px; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.1); 
        border-left: 5px solid #2d6a4f; 
        text-align: center;
    }
    
    /* Modern Button Styling */
    div.stButton > button {
        width: 100%;
        border-radius: 12px;
        height: 3.2em;
        background-color: #2d6a4f;
        color: white;
        font-weight: bold;
        border: none;
        transition: all 0.3s ease;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    div.stButton > button:hover {
        background-color: #1b4332;
        color: #d8f3dc;
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.15);
    }

    /* Strategy Intelligence Box */
    .strategy-box { 
        background-color: #e8f5e9; 
        padding: 20px; 
        border-radius: 12px; 
        border: 1px solid #c8e6c9; 
        color: #1b5e20;
    }

    div[data-testid="stForm"] { 
        background-color: white; 
        border-radius: 15px; 
        padding: 30px; 
        box-shadow: 0 10px 25px rgba(0,0,0,0.05); 
    }
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

# --- Logic: Parallel Martingale & Cycle Calculation ---
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
                display_rev = revenue
                # Correct cycle profit calculation
                cycle_net = revenue - cycle_investments[comp]
                # Reset for next match
                comp_states[comp] = br_base if "Brighton" in comp else af_base
                cycle_investments[comp] = 0
            else:
                status = "❌ Lost"
                display_rev = 0
                cycle_net = 0
                comp_states[comp] = recorded_stake * 2
            
            processed_games.append({
                "SheetRow": i + 2,
                "Date": row.get('Date', ''),
                "Comp": comp,
                "Match": f"{row.get('Home Team', '')} vs {row.get('Away Team', '')}",
                "Odds": odds,
                "Stake": recorded_stake,
                "Status": status,
                "Revenue": display_rev,
                "Cycle Net": cycle_net
            })
        except Exception:
            continue
    return processed_games, comp_states

# --- Sidebar ---
with st.sidebar:
    st.title("💰 Financial Center")
    total_bankroll = st.number_input("Starting Bankroll (₪)", min_value=100, value=5000, step=100)
    st.divider()
    selected_comp = st.selectbox("Current Track", ["Brighton", "Africa Cup of Nations"])
    
    # Defaults as requested: Brighton (30), Africa (20)
    default_val = 30 if selected_comp == "Brighton" else 20
    stake_key = f"base_stake_{selected_comp}"
    base_stake = st.number_input("Track Base Stake (₪)", min_value=5, value=default_val, step=5, key=stake_key)
    
    st.divider()
    if st.button("🔄 Sync & Refresh Database"):
        st.rerun()

# --- Load and Process Data ---
raw_data, worksheet = get_data_from_sheets()
# Maintain track defaults for recalculation
all_processed_data, next_stakes = calculate_parallel_status(raw_data, 30, 20)

if all_processed_data:
    full_df = pd.DataFrame(all_processed_data)
    # Global metrics for shared bankroll
    global_inv = full_df['Stake'].sum()
    global_rev = full_df['Revenue'].sum()
    global_net = global_rev - global_inv
    current_cash = total_bankroll + global_net
    # Track-specific filter
    filtered_df = full_df[full_df['Comp'] == selected_comp].copy()
else:
    global_net, current_cash = 0, total_bankroll
    filtered_df = pd.DataFrame()

# --- MAIN UI ---
# Updated Professional Header Banner
st.markdown(f"""
    <div class='pro-header-container'>
        <h1 class='pro-header-text'>{selected_comp.upper()} HUB</h1>
    </div>
""", unsafe_allow_html=True)

# 1. Global Bankroll Indicator
c1, c2, c3 = st.columns([1, 2, 1])
with c2:
    st.markdown(f"<h3 style='text-align: center;'>Total Bankroll: ₪{current_cash:,.0f}</h3>", unsafe_allow_html=True)
    health_pct = min(max(current_cash / total_bankroll, 0.0), 2.0) / 2.0
    st.progress(health_pct)
    p_color = "green" if global_net >= 0 else "red"
    st.markdown(f"<p style='text-align: center; color: {p_color}; font-weight: bold;'>Overall P/L: ₪{global_net:,.0f}</p>", unsafe_allow_html=True)

# 2. Track Specific Metrics
col1, col2, col3 = st.columns(3)
t_inv = filtered_df['Stake'].sum() if not filtered_df.empty else 0
t_rev = filtered_df['Revenue'].sum() if not filtered_df.empty else 0
t_net = filtered_df['Cycle Net'].sum() if not filtered_df.empty else 0

col1.markdown(f"<div class='metric-card'><b>Investment</b><br>₪{t_inv:,.0f}</div>", unsafe_allow_html=True)
col2.markdown(f"<div class='metric-card'><b>Returned</b><br>₪{t_rev:,.0f}</div>", unsafe_allow_html=True)
col3.markdown(f"<div class='metric-card'><b>Net Profit</b><br>₪{t_net:,.0f}</div>", unsafe_allow_html=True)

st.write("")

# 3. Match Deployment & Intelligence
m_col1, m_col2 = st.columns([1, 1])

with m_col1:
    st.markdown("### 🏟️ Match Entry")
    with st.form("modern_form", clear_on_submit=True):
        d_in = st.date_input("Date", datetime.date.today())
        h_t = st.text_input("Home Team", value="Brighton" if selected_comp == "Brighton" else "")
        a_t = st.text_input("Away Team")
        o_in = st.number_input("Odds (X)", value=3.2, step=0.1)
        r_in = st.radio("Result", ["Draw (X)", "No Draw"], horizontal=True)
        
        if st.form_submit_button("🚀 SYNC MATCH TO CLOUD"):
            if h_t and a_t:
                # Recalculate rec_stake to ensure sync
                rec_stake = next_stakes.get(selected_comp, base_stake)
                worksheet.append_row([str(d_in), selected_comp, h_t, a_t, o_in, r_in, rec_stake, 0])
                st.toast("Synchronized Successfully!", icon="✅")
                st.rerun()

with m_col2:
    st.markdown("### 🧠 Deployment Intelligence")
    rec_stake = next_stakes.get(selected_comp, base_stake)
    st.markdown(f"""
        <div class='strategy-box'>
            <h4>Next Target Stake</h4>
            <p>Martingale sequence for {selected_comp}:</p>
            <h2 style='margin: 0;'>Bet ₪{rec_stake} on Draw</h2>
            <p style='font-size: 0.85rem; margin-top: 10px;'>Recommended Odds: 3.20+</p>
        </div>
    """, unsafe_allow_html=True)
    
    if not filtered_df.empty:
        # Mini performance curve
        filtered_df['Cumulative'] = filtered_df['Revenue'].cumsum() - filtered_df['Stake'].cumsum()
        fig = px.line(filtered_df, y='Cumulative', title="Equity Curve")
        fig.update_traces(line_color='#2d6a4f', line_width=3)
        fig.update_layout(height=240, margin=dict(l=0,r=0,t=30,b=0), paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)

# 4. Activity Log
if not filtered_df.empty:
    st.markdown("### 📜 Strategy Activity Log")
    def style_status(val):
        if 'Won' in str(val): return 'background-color: #d4edda; color: #155724'
        if 'Lost' in str(val): return 'background-color: #f8d7da; color: #721c24'
        return ''
    
    st.dataframe(
        filtered_df.drop(columns=['SheetRow', 'Cumulative']).style.applymap(style_status, subset=['Status']),
        use_container_width=True, hide_index=True
    )

# 5. Advanced Record Management
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
            to_del = st.selectbox("Specific match removal:", options=list(match_map.keys()))
            if st.button("Delete Selected Match"):
                worksheet.delete_rows(match_map[to_del])
                st.rerun()
    
    if st.button("FACTORY RESET (Wipe All History)"):
        worksheet.resize(rows=1)
        st.rerun()