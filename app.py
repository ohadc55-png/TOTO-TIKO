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
                # Net profit for this specific winning row
                net_cycle_profit = revenue - cycle_investments[comp]
                status = "✅ Won"
                display_revenue = revenue # Money back from bookie
                
                # Reset for next match
                comp_states[comp] = br_base if "Brighton" in comp else af_base
                cycle_investments[comp] = 0
            else:
                status = "❌ Lost"
                display_revenue = 0 # No money back
                # Stake for next match
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

# --- Sidebar ---
with st.sidebar:
    st.title("⚙️ Tactics Board")
    selected_comp = st.selectbox("Current Track", ["Brighton", "Africa Cup of Nations"])
    
    # Set requested defaults
    default_val = 30 if selected_comp == "Brighton" else 20
    stake_key = f"base_stake_{selected_comp}"
    base_stake = st.number_input("Base Stake (₪)", min_value=5, value=default_val, step=5, key=stake_key)
    
    st.divider()
    if st.button("Refresh & Sync"):
        st.rerun()

# --- Load and Process ---
raw_data, worksheet = get_data_from_sheets()
# Pass the requested defaults to the engine
all_processed_data, next_stakes = calculate_parallel_status(raw_data, 30, 20)

# --- Filter & Metrics ---
if all_processed_data:
    full_df = pd.DataFrame(all_processed_data)
    filtered_df = full_df[full_df['Comp'] == selected_comp].copy()
else:
    filtered_df = pd.DataFrame()

if not filtered_df.empty:
    total_invested = filtered_df['Stake'].sum()
    total_returned = filtered_df['Revenue'].sum()
    net_profit = total_returned - total_invested
else:
    total_invested, total_returned, net_profit = 0, 0, 0

# --- Main UI ---
st.markdown(f"<h1>⚽ {selected_comp} Tracker</h1>", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)
col1.metric("Total Invested", f"₪{total_invested:,.0f}")
col2.metric("Total Returned", f"₪{total_returned:,.0f}")
col3.metric("Net Profit", f"₪{net_profit:,.0f}", delta=net_profit)

# Input Form
st.markdown("### 📝 Add Match Result")
with st.container(border=True):
    rec_stake = next_stakes.get(selected_comp, base_stake)
    st.success(f"💡 Next Required Stake: **₪{rec_stake}**")
    
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

# History Table
if not filtered_df.empty:
    st.markdown("### 📜 Activity Log")
    def style_status(val):
        if 'Won' in str(val): return 'background-color: #d4edda; color: #155724'
        if 'Lost' in str(val): return 'background-color: #f8d7da; color: #721c24'
        return ''

    st.dataframe(filtered_df.drop(columns=['SheetRow']).style.applymap(style_status, subset=['Status']), use_container_width=True, hide_index=True)

# --- Danger Zone & Record Management ---
st.write("---")
with st.expander("⚠️ Manage Records & Danger Zone"):
    if raw_data:
        st.subheader("Undo & Specific Deletion")
        if st.button("Delete Last Entry"):
            worksheet.delete_rows(len(raw_data) + 1)
            st.rerun()
            
        st.divider()
        match_options = {f"{g['Date']} - {g['Match']}": g['SheetRow'] for g in all_processed_data}
        selected_to_delete = st.selectbox("Select specific match to remove:", options=list(match_options.keys()))
        if st.button("Delete Selected"):
            worksheet.delete_rows(match_options[selected_to_delete])
            st.rerun()

    st.divider()
    if st.button("Nuke Everything (Factory Reset)"):
        worksheet.resize(rows=1)
        st.rerun()