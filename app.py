import streamlit as st
import pandas as pd
import plotly.express as px
import gspread
import datetime

# --- Page Configuration ---
st.set_page_config(
    page_title="Pro Football Tracker",
    layout="centered",
    page_icon="⚽",
    initial_sidebar_state="expanded"
)

# --- Custom CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    h1 { color: #1b4332; font-family: 'Helvetica Neue', sans-serif; font-weight: 700; text-align: center; }
    div[data-testid="stMetricValue"] { font-size: 28px; color: #2d6a4f; }
    .stButton>button { border-radius: 20px; font-weight: bold; border: none; transition: 0.3s; }
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
        st.error(f"Connection Error: {e}")
        return [], None

# --- Logic: Parallel Martingale Calculation ---
def calculate_parallel_status(raw_data, initial_stake):
    if not raw_data:
        return [], {}, 0, 0, 0

    df_raw = pd.DataFrame(raw_data)
    processed_games = []
    
    # מילון לשמירת הסטייק הבא לכל תחרות בנפרד
    next_stakes = {"Brighton": initial_stake, "Africa Cup of Nations": initial_stake}
    
    total_invested = 0
    total_revenue = 0
    
    # עוברים על הנתונים ומחשבים לוגיקה לכל תחרות בנפרד
    # אנחנו מניחים שהנתונים בשיטס מסודרים לפי תאריך
    comp_states = {} # שומר את ה-current_stake הנוכחי לכל תחרות

    for index, row in df_raw.iterrows():
        comp = row['Competition']
        if comp not in comp_states:
            comp_states[comp] = initial_stake
        
        current_stake = comp_states[comp]
        odds = float(row['Odds'])
        res_str = str(row['Result'])
        
        invested = current_stake
        total_invested += invested
        
        is_draw = "Draw" in res_str or "תיקו" in res_str or "X" in res_str
        
        if is_draw:
            revenue = invested * odds
            profit = revenue - invested
            comp_states[comp] = initial_stake # איפוס
            status = "✅ Won"
        else:
            revenue = 0
            profit = -invested
            comp_states[comp] = current_stake * 2 # הכפלה
            status = "❌ Lost"
            
        total_revenue += revenue
        
        processed_games.append({
            "Date": row['Date'],
            "Comp": comp,
            "Match": f"{row['Home Team']} vs {row['Away Team']}",
            "Odds": odds,
            "Stake": invested,
            "Status": status,
            "P/L": profit
        })

    running_bal = total_revenue - total_invested
    return processed_games, comp_states, total_invested, total_revenue, running_bal

# --- Sidebar ---
with st.sidebar:
    st.title("⚙️ Tactics Board")
    # בחירת התחרות לניהול בטופס
    selected_comp = st.selectbox("Current Competition", ["Brighton", "Africa Cup of Nations"])
    initial_stake = st.number_input("Initial Stake", min_value=10, value=50, step=10)
    st.divider()
    st.info("Parallel Tracking Enabled 🟢")

# --- MAIN APP FLOW ---
raw_data, worksheet = get_data_from_sheets()
processed_data, next_stakes_map, total_inv, total_rev, total_bal = calculate_parallel_status(raw_data, initial_stake)

# Header
display_name = "Brighton" if selected_comp == "Brighton" else "Africa Cup"
st.markdown(f"<h1>⚽ {display_name} Tracker</h1>", unsafe_allow_html=True)

# 1. Key Stats
st.markdown("### 📊 Overall Performance (All Tracks)")
col1, col2, col3 = st.columns(3)
with col1:
    st.container(border=True).metric("Total Invested", f"{total_inv:,.0f}")
with col2:
    st.container(border=True).metric("Total Returned", f"{total_rev:,.0f}")
with col3:
    color = "normal" if total_bal >= 0 else "inverse"
    st.container(border=True).metric("Net Profit", f"{total_bal:,.0f}", delta=total_bal, delta_color=color)

# 2. Input Form
st.markdown(f"### 📝 Match Day Input: {selected_comp}")
with st.container(border=True):
    # שליפת הסטייק הבא עבור התחרות הספציפית שנבחרה
    recommended_stake = next_stakes_map.get(selected_comp, initial_stake)
    
    st.markdown(f"""
        <div style='background-color: #d8f3dc; padding: 15px; border-radius: 10px; border-left: 5px solid #2d6a4f; margin-bottom: 20px;'>
            <strong style='color: #1b4332;'>💡 Strategy for {selected_comp}:</strong> 
            Next bet: <span style='font-size: 1.2em; font-weight: bold;'>{recommended_stake}</span> on X.
        </div>
    """, unsafe_allow_html=True)

    with st.form("add_game_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            date_input = st.date_input("Match Date")
            home_team = st.text_input("Home Team", value="Brighton" if selected_comp == "Brighton" else "")
            odds_input = st.number_input("Odds (X)", min_value=1.0, value=3.0, step=0.1)
        with c2:
            away_team = st.text_input("Away Team")
            result_input = st.radio("Result", ["Draw (X)", "Win/Loss"], horizontal=True)
        
        submitted = st.form_submit_button("⚽ Save Match to Cloud", use_container_width=True)
        
        if submitted and worksheet:
            if home_team and away_team:
                # מבנה השורה החדש: Date, Competition, Home, Away, Odds, Result
                new_row = [str(date_input), selected_comp, home_team, away_team, odds_input, result_input]
                worksheet.append_row(new_row)
                st.success(f"Saved {selected_comp} match!")
                st.rerun()
            else:
                st.error("Please enter both team names.")

# 3. Visuals & History
if processed_data:
    df = pd.DataFrame(processed_data)
    
    st.markdown("### 📜 Match History (Combined)")
    
    def color_status(val):
        color = '#d4edda' if 'Won' in val else '#f8d7da'
        return f'background-color: {color}; color: black; border-radius: 5px;'

    st.dataframe(
        df.style.map(color_status, subset=['Status'])
          .format({"Stake": "{:.0f}", "P/L": "{:.0f}", "Odds": "{:.2f}"}),
        use_container_width=True, hide_index=True
    )
    
    with st.expander("⚠️ Danger Zone"):
        if st.button("Delete Database History"):
            worksheet.resize(rows=1) 
            st.warning("Database cleared.")
            st.rerun()
else:
    st.info("Database is empty. Add the first match above.")