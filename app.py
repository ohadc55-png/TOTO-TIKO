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

# --- Logic: Persistent Martingale Calculation ---
def calculate_parallel_status(raw_data, initial_stake):
    processed_games = []
    # Current stake for the NEXT match
    comp_states = {"Brighton": initial_stake, "Africa Cup of Nations": initial_stake}
    # Track the sum of money put into the current open cycle
    cycle_investments = {"Brighton": 0, "Africa Cup of Nations": 0}

    if not raw_data:
        return [], comp_states

    for row in raw_data:
        try:
            comp = str(row.get('Competition', 'Brighton')).strip()
            # Ensure competition exists in our tracking dictionaries
            if comp not in comp_states:
                comp_states[comp] = initial_stake
                cycle_investments[comp] = 0
                
            try:
                odds = float(str(row.get('Odds', 1)).replace(',', '.'))
            except:
                odds = 1.0
            
            res_str = str(row.get('Result', '')).strip()
            
            # Use the stake that was actually recorded in the sheet for this game
            # This prevents desync if the sidebar 'Base Stake' was changed later
            try:
                recorded_stake = float(row.get('Stake', comp_states[comp]))
            except:
                recorded_stake = comp_states[comp]

            cycle_investments[comp] += recorded_stake
            
            # Robust check for "Draw (X)" result
            is_win = "Draw (X)" in res_str
            
            if is_win:
                revenue = recorded_stake * odds
                net_cycle_profit = revenue - cycle_investments[comp]
                comp_states[comp] = initial_stake # Reset to base for NEXT game
                cycle_investments[comp] = 0 # Cycle closed
                status = "✅ Won"
                display_profit = net_cycle_profit
            else:
                status = "❌ Lost"
                display_profit = 0 # Cycle remains open
                comp_states[comp] = recorded_stake * 2 # Double for NEXT game
            
            processed_games.append({
                "Date": row.get('Date', ''),
                "Comp": comp,
                "Match": f"{row.get('Home Team', '')} vs {row.get('Away Team', '')}",
                "Odds": odds,
                "Stake": recorded_stake,
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
    # This is the "Base" for new cycles. Martingale doubles based on previous rows in sheet.
    base_stake = st.number_input("Base Stake (₪)", min_value=10, value=50, step=10)
    st.divider()
    if st.button("Refresh & Sync"):
        st.rerun()

# --- Load and Process ---
raw_data, worksheet = get_data_from_sheets()
all_processed_data, next_stakes = calculate_parallel_status(raw_data, base_stake)

# --- Filter View ---
if all_processed_data:
    full_df = pd.DataFrame(all_processed_data)
    filtered_df = full_df[full_df['Comp'] == selected_comp].copy()
else:
    filtered_df = pd.DataFrame()

# Calculate specific metrics for the UI
if not filtered_df.empty:
    track_inv = filtered_df['Stake'].sum()
    track_net = filtered_df['Cycle Net Profit'].sum()
    track_rev = track_inv + track_net
else:
    track_inv, track_rev, track_net = 0, 0, 0

# --- Main UI ---
st.markdown(f"<h1>⚽ {selected_comp} Tracker</h1>", unsafe_allow_html=True)

# Metrics Dashboard
col1, col2, col3 = st.columns(3)
col1.metric("Total Invested", f"₪{track_inv:,.0f}")
col2.metric("Total Returned", f"₪{track_rev:,.0f}")
col3.metric("Net Cycle Profit", f"₪{track_net:,.0f}", delta=track_net)

# Match Input Form
st.markdown("### 📝 Add Match Result")
with st.container(border=True):
    # This value now correctly persists based on the last row in the Sheet
    rec_stake = next_stakes.get(selected_comp, base_stake)
    st.success(f"💡 Next Required Stake for {selected_comp}: **₪{rec_stake}**")
    
    with st.form("input_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            date_in = st.date_input("Match Date", datetime.date.today())
            home_t = st.text_input("Home Team", value="Brighton" if selected_comp == "Brighton" else "")
            odds_in = st.number_input("Draw Odds (X)", min_value=1.0, value=3.2, step=0.1)
        with c2:
            away_t = st.text_input("Away Team")
            res_in = st.radio("Result", ["Draw (X)", "No Draw"], horizontal=True)
        
        if st.form_submit_button("🚀 Submit to Cloud", use_container_width=True):
            if home_t and away_t:
                # Save the current rec_stake to the 'Stake' column so logic can follow it on reload
                new_row = [str(date_in), selected_comp, home_t, away_t, odds_in, res_in, rec_stake, 0]
                worksheet.append_row(new_row)
                st.balloons()
                st.rerun()
            else:
                st.error("Please fill in both team names.")

# History Display
if not filtered_df.empty:
    st.markdown("### 📜 Activity Log")
    def style_status(val):
        if 'Won' in str(val): return 'background-color: #d4edda; color: #155724'
        if 'Lost' in str(val): return 'background-color: #f8d7da; color: #721c24'
        return ''

    st.dataframe(filtered_df.style.applymap(style_status, subset=['Status']), use_container_width=True, hide_index=True)
    
    # Growth Chart
    st.markdown("### 📈 Profit Growth")
    filtered_df['Cumulative'] = filtered_df['Cycle Net Profit'].cumsum()
    fig = px.area(filtered_df, x=filtered_df.index, y='Cumulative', title=f"{selected_comp} - Net Performance")
    fig.update_traces(line_color='#2d6a4f', fillcolor='rgba(45, 106, 79, 0.2)')
    st.plotly_chart(fig, use_container_width=True)

# --- DANGER ZONE ---
st.write("---")
with st.expander("⚠️ Danger Zone"):
    st.warning("Resetting will wipe the cloud database. This cannot be undone.")
    if st.button("Clear All Data"):
        if worksheet:
            worksheet.resize(rows=1)
            st.success("Database Reset!")
            st.rerun()