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
        # ניקוי שורות ריקות בגיליון
        data = [row for row in data if str(row.get('Odds', '')).strip() != '']
        return data, worksheet
    except Exception as e:
        st.error(f"Connection Error: {e}")
        return [], None

# --- Logic: Parallel Martingale Calculation ---
def calculate_parallel_status(raw_data, initial_stake):
    processed_games = []
    # comp_states ינהל את הסטייק הבא לכל מסלול בנפרד
    comp_states = {"Brighton": initial_stake, "Africa Cup of Nations": initial_stake}
    
    total_invested = 0
    total_revenue = 0

    for row in raw_data:
        try:
            comp = str(row.get('Competition', 'Brighton')).strip()
            odds = float(str(row.get('Odds', 1)).replace(',', '.'))
            res_str = str(row.get('Result', '')).strip()
            
            if comp not in comp_states:
                comp_states[comp] = initial_stake
                
            current_stake = comp_states[comp]
            invested = current_stake
            total_invested += invested
            
            # --- תיקון זיהוי תוצאה: בדיקה מדויקת בלבד ---
            is_draw = (res_str == "Draw (X)") 
            
            if is_draw:
                revenue = invested * odds
                profit = revenue - invested
                comp_states[comp] = initial_stake # איפוס לאחר זכייה
                status = "✅ Won"
            else:
                revenue = 0
                profit = -invested # הפסד רשום כמינוס
                comp_states[comp] = current_stake * 2 # הכפלה מרטינגייל
                status = "❌ Lost"
            
            total_revenue += revenue
            
            processed_games.append({
                "Date": row.get('Date', ''),
                "Competition": comp,
                "Match": f"{row.get('Home Team', 'N/A')} vs {row.get('Away Team', 'N/A')}",
                "Odds": odds,
                "Stake": invested,
                "Status": status,
                "Profit": profit
            })
        except Exception:
            continue 

    running_bal = total_revenue - total_invested
    return processed_games, comp_states, total_invested, total_revenue, running_bal

# --- MAIN APP FLOW ---
raw_data, worksheet = get_data_from_sheets()

# Sidebar
with st.sidebar:
    st.title("⚙️ Tactics Board")
    selected_comp = st.selectbox("Current Track", ["Brighton", "Africa Cup of Nations"])
    initial_stake = st.number_input("Base Stake (₪)", min_value=10, value=50, step=10)
    st.divider()
    st.info("System: Parallel Tracking Live 🟢")