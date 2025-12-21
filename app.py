import streamlit as st
import pandas as pd
import plotly.express as px
import gspread
import datetime

# --- Page Configuration ---
st.set_page_config(page_title="Pro Football Tracker", layout="centered", page_icon="⚽")

# --- Custom CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    h1 { color: #1b4332; text-align: center; font-family: 'Arial', sans-serif; }
    .stMetric { background-color: white; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    div[data-testid="stForm"] { background-color: white; border-radius: 10px; padding: 20px; }
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

# --- Logic: Intelligent Parallel Calculation with Cycle Profit ---
def calculate_parallel_status(raw_data, initial_stake):
    processed_games = []
    # Tracks the next required stake
    comp_states = {"Brighton": initial_stake, "Africa Cup of Nations": initial_stake}
    # Tracks cumulative investment in the current unfinished cycle
    cycle_investments = {"Brighton": 0, "Africa Cup of Nations": 0}

    if not raw_data:
        return [], comp_states

    for row in raw_data:
        try:
            comp = str(row.get('Competition', 'Brighton')).strip()
            try:
                odds = float(str(row.get('Odds', 1)).replace(',', '.'))
            except:
                odds = 1.0
            
            res_str = str(row.get('Result', '')).strip()
            
            if comp not in comp_states:
                comp_states[comp] = initial_stake
                cycle_investments[comp] = 0
            
            current_stake = comp_states[comp]
            cycle_investments[comp] += current_stake # Add current bet to cycle total
            
            is_win = (res_str == "Draw (X)")
            
            if is_win:
                revenue = current_stake * odds
                # Profit = Total Revenue minus ALL money spent in this specific cycle
                net_cycle_profit = revenue - cycle_investments[comp]
                comp_states[comp] = initial_stake # Reset stake
                cycle_investments[comp] = 0 # Reset cycle investment
                status = "✅ Won"
                display_profit = net_cycle_profit
            else:
                status = "❌ Lost"
                display_profit = 0 # Record 0 profit for loss rows to avoid double-counting cycle net
                comp_states[comp] = current_stake * 2 # Double stake
            
            processed_games.append({
                "Date": row.get('Date', ''),
                "Comp": comp,
                "Match": f"{row.get('Home Team', '')} vs {row.get('Away Team', '')}",
                "Odds": odds,
                "Stake": current_stake,
                "Status": status,
                "Cycle Net Profit": display_profit
            })
        except Exception:
            continue

    return processed_games, comp_states

# --- Sidebar ---
with st.sidebar:
    st.title("⚙️ Tactics Board")
    selected_comp = st.selectbox("Current Track", ["Brighton", "Africa Cup of Nations"])
    base_stake = st.number_input("Base Stake (₪)", min_value=10, value=50, step=10)
    st.divider()
    if st.button("Refresh Data"):
        st.rerun()

# --- Data Loading & Processing ---
raw_data, worksheet = get_data_from_sheets()
all_processed_data, next_stakes = calculate_parallel_status(raw_data, base_stake)

# --- FILTERING LOGIC ---
if all_processed_data:
    full_df = pd.DataFrame(all_processed_data)
    filtered_df = full_df[full_df['Comp'] == selected_comp].copy()
else:
    filtered_df = pd.DataFrame()

# Calculate specific metrics based on history
if not filtered_df.empty:
    track_inv = filtered_df['Stake'].sum()
    track_net = filtered_df['Cycle Net Profit'].sum()
    track_rev = track_inv + track_profit if 'track_profit' in locals() else track_inv + track_net
else:
    track_inv, track_rev, track_net = 0, 0, 0

# --- Main UI Display ---
st.markdown(f"<h1>⚽ {selected_comp} Tracker</h1>", unsafe_allow_html=True)

# Performance Metrics
col1, col2, col3 = st.columns(3)
col1.metric("Total Invested", f"₪{track_inv:,.0f}")
col2.metric("Total Revenue", f"₪{track_rev:,.0f}")
col3.metric("Net Cycle Profit", f"₪{track_net:,.0f}", delta=track_net)

# Match Input Form
st.markdown("### 📝 Add New Match")
with st.container(border=True):
    rec_stake = next_stakes.get(selected_comp, base_stake)
    st.success(f"💡 Recommended Stake for {selected_comp}: **₪{rec_stake}**")
    
    with st.form("input_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            date_in = st.date_input("Match Date", datetime.date.today())
            home_t = st.text_input("Home Team", value="Brighton" if selected_comp == "Brighton" else "")
            odds_in = st.number_input("Draw Odds (X)", min_value=1.0, value=3.2, step=0.1)
        with c2:
            away_t = st.text_input("Away Team")
            res_in = st.radio("Result", ["Draw (X)", "No Draw"], horizontal=True)
        
        if st.form_submit_button("🚀 Sync to Cloud", use_container_width=True):
            if home_t and away_t:
                # Calculate quick profit for the sheet record
                new_row = [str(date_in), selected_comp, home_t, away_t, odds_in, res_in, rec_stake, 0] # 0 as placeholder
                worksheet.append_row(new_row)
                st.balloons()
                st.rerun()
            else:
                st.error("Please provide both team names.")

# Filtered History & Visuals
if not filtered_df.empty:
    st.markdown("### 📜 Match History")
    def style_status(val):
        if 'Won' in str(val): return 'background-color: #d4edda; color: #155724'
        if 'Lost' in str(val): return 'background-color: #f8d7da; color: #721c24'
        return ''

    st.dataframe(
        filtered_df.style.applymap(style_status, subset=['Status']),
        use_container_width=True, hide_index=True
    )
    
    st.markdown("### 📈 Cumulative Performance")
    filtered_df['Cumulative Profit'] = filtered_df['Cycle Net Profit'].cumsum()
    fig = px.area(filtered_df, x=filtered_df.index, y='Cumulative Profit', title=f"{selected_comp} Account Growth")
    fig.update_traces(line_color='#2d6a4f', fillcolor='rgba(45, 106, 79, 0.2)')
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info(f"No data available for {selected_comp}.")