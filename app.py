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

# --- Logic: Intelligent Parallel Calculation ---
def calculate_parallel_status(raw_data, br_base, af_base):
    processed_games = []
    # Set default bases per track
    comp_states = {"Brighton": br_base, "Africa Cup of Nations": af_base}
    cycle_investments = {"Brighton": 0, "Africa Cup of Nations": 0}

    if not raw_data:
        return [], comp_states

    for i, row in enumerate(raw_data):
        try:
            comp = str(row.get('Competition', 'Brighton')).strip()
            
            # Use current track base if not already in state
            if comp not in comp_states:
                comp_states[comp] = br_base if "Brighton" in comp else af_base
                cycle_investments[comp] = 0
            
            try:
                odds = float(str(row.get('Odds', 1)).replace(',', '.'))
            except:
                odds = 1.0
            
            res_str = str(row.get('Result', '')).strip()
            
            # Use the stake recorded in the sheet for accurate history
            try:
                recorded_stake = float(row.get('Stake', comp_states[comp]))
            except:
                recorded_stake = comp_states[comp]

            cycle_investments[comp] += recorded_stake
            is_win = "Draw (X)" in res_str
            
            if is_win:
                revenue = recorded_stake * odds
                net_cycle_profit = revenue - cycle_investments[comp]
                comp_states[comp] = br_base if "Brighton" in comp else af_base
                cycle_investments[comp] = 0
                status = "✅ Won"
                display_profit = net_cycle_profit
            else:
                status = "❌ Lost"
                display_profit = 0
                comp_states[comp] = recorded_stake * 2
            
            processed_games.append({
                "SheetRow": i + 2, # Helpers to track row in GSheets
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
    
    # Dynamic defaults based on selection
    default_val = 30 if selected_comp == "Brighton" else 20
    
    # We use a unique key for each track to maintain their separate base stakes if changed manually
    stake_key = f"base_stake_{selected_comp}"
    base_stake = st.number_input("Base Stake (₪)", min_value=5, value=default_val, step=5, key=stake_key)
    
    st.divider()
    if st.button("Refresh & Sync"):
        st.rerun()

# --- Load and Process ---
raw_data, worksheet = get_data_from_sheets()
# Pass both defaults to the engine
all_processed_data, next_stakes = calculate_parallel_status(raw_data, 30, 20)

# Update next_stakes logic to use the sidebar's current value for the selected track
next_stakes[selected_comp] = next_stakes.get(selected_comp, base_stake)

# --- Filter View ---
if all_processed_data:
    full_df = pd.DataFrame(all_processed_data)
    filtered_df = full_df[full_df['Comp'] == selected_comp].copy()
else:
    filtered_df = pd.DataFrame()

# Stats calculation
if not filtered_df.empty:
    track_inv = filtered_df['Stake'].sum()
    track_net = filtered_df['Cycle Net Profit'].sum()
    track_rev = track_inv + track_net
else:
    track_inv, track_rev, track_net = 0, 0, 0

# --- Main UI ---
st.markdown(f"<h1>⚽ {selected_comp} Tracker</h1>", unsafe_allow_html=True)

# Metrics
col1, col2, col3 = st.columns(3)
col1.metric("Total Invested", f"₪{track_inv:,.0f}")
col2.metric("Total Returned", f"₪{track_rev:,.0f}")
col3.metric("Net Cycle Profit", f"₪{track_net:,.0f}", delta=track_net)

# Match Input Form
st.markdown("### 📝 Add Match Result")
with st.container(border=True):
    # Determine next stake. If no history, use the current sidebar base_stake
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

    st.dataframe(filtered_df.drop(columns=['SheetRow']).style.applymap(style_status, subset=['Status']), use_container_width=True, hide_index=True)
    
    # Growth Chart
    st.markdown("### 📈 Profit Growth")
    filtered_df['Cumulative'] = filtered_df['Cycle Net Profit'].cumsum()
    fig = px.area(filtered_df, x=filtered_df.index, y='Cumulative', title=f"{selected_comp} Growth")
    fig.update_traces(line_color='#2d6a4f', fillcolor='rgba(45, 106, 79, 0.2)')
    st.plotly_chart(fig, use_container_width=True)

# --- DANGER ZONE & EDITING ---
st.write("---")
with st.expander("⚠️ Manage Records & Danger Zone"):
    st.subheader("Edit History")
    
    # 1. Delete Last Match
    if st.button("Undo Last Match (Delete Last Entry)"):
        if raw_data:
            last_row_index = len(raw_data) + 1 # +1 because of header row 1
            worksheet.delete_rows(last_row_index)
            st.success("Last entry removed.")
            st.rerun()
        else:
            st.info("No data to delete.")

    st.divider()
    
    # 2. Delete Specific Match
    if all_processed_data:
        st.write("Delete a specific match:")
        match_options = {f"{g['Date']} - {g['Match']} ({g['Comp']})": g['SheetRow'] for g in all_processed_data}
        selected_match_label = st.selectbox("Select match to remove:", options=list(match_options.keys()))
        
        if st.button("Delete Selected Match"):
            row_to_delete = match_options[selected_match_label]
            worksheet.delete_rows(row_to_delete)
            st.success(f"Removed: {selected_match_label}")
            st.rerun()

    st.divider()
    
    # 3. Full Reset
    st.warning("Clear All Data (Factory Reset)")
    if st.button("Nuke Everything"):
        if worksheet:
            worksheet.resize(rows=1)
            st.success("Database Reset!")
            st.rerun()