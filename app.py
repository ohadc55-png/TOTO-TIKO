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
        # סינון שורות ריקות שעלולות לגרום לשגיאות
        data = [row for row in data if str(row.get('Odds', '')).strip() != '']
        return data, worksheet
    except Exception as e:
        st.error(f"Connection Error: {e}")
        return [], None

# --- Expert Logic: Parallel Martingale Engine ---
def calculate_parallel_status(raw_data, initial_stake):
    processed_games = []
    # comp_states יחזיק את הסטייק הבא לכל תחרות
    comp_states = {"Brighton": initial_stake, "Africa Cup of Nations": initial_stake}
    
    total_invested = 0
    total_revenue = 0

    for row in raw_data:
        try:
            # שלב 1: חילוץ וניקוי נתונים (מניעת ValueErrors)
            comp = str(row.get('Competition', 'Brighton')).strip()
            odds = float(str(row.get('Odds', 1)).replace(',', '.'))
            res_str = str(row.get('Result', '')).strip()
            
            # אם התחרות לא קיימת במילון הסטייט, נוסיף אותה
            if comp not in comp_states:
                comp_states[comp] = initial_stake
                
            current_stake = comp_states[comp]
            invested = current_stake
            total_invested += invested
            
            # שלב 2: בדיקת תוצאה (Draw Detection)
            is_draw = any(x in res_str for x in ["Draw", "תיקו", "X", "(X)"])
            
            if is_draw:
                revenue = invested * odds
                profit = revenue - invested
                comp_states[comp] = initial_stake # חזרה לסטייק התחלתי
                status = "✅ Won"
            else:
                revenue = 0
                profit = -invested
                comp_states[comp] = current_stake * 2 # הכפלה מרטינגייל
                status = "❌ Lost"
            
            total_revenue += revenue
            
            # שלב 3: בניית הנתון המעובד
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
            continue # דילוג על שורות פגומות כדי למנוע קריסה

    running_bal = total_revenue - total_invested
    return processed_games, comp_states, total_invested, total_revenue, running_bal

# --- MAIN APP FLOW ---
raw_data, worksheet = get_data_from_sheets()

# Sidebar Settings
with st.sidebar:
    st.title("⚙️ Tactics Board")
    selected_comp = st.selectbox("Current Tracking Track", ["Brighton", "Africa Cup of Nations"])
    initial_stake = st.number_input("Base Stake (₪)", min_value=10, value=50, step=10)
    st.divider()
    st.info("System Status: Operational 🟢")

# Calculation Engine
processed_data, next_stakes_map, total_inv, total_rev, total_bal = calculate_parallel_status(raw_data, initial_stake)

# Header
st.markdown(f"<h1>⚽ {selected_comp} Tracker</h1>", unsafe_allow_html=True)

# 1. Dashboard Metrics
st.markdown("### 📊 Financial Summary")
col1, col2, col3 = st.columns(3)
with col1:
    st.container(border=True).metric("Total Investment", f"₪{total_inv:,.0f}")
with col2:
    st.container(border=True).metric("Total Returns", f"₪{total_rev:,.0f}")
with col3:
    st.container(border=True).metric("Net Profit/Loss", f"₪{total_bal:,.0f}", delta=total_bal)

# 2. Input Form
st.markdown(f"### 📝 New Match: {selected_comp}")
with st.container(border=True):
    recommended_stake = next_stakes_map.get(selected_comp, initial_stake)
    
    st.markdown(f"""
        <div style='background-color: #d8f3dc; padding: 15px; border-radius: 10px; border-left: 5px solid #2d6a4f; margin-bottom: 20px; color: #1b4332;'>
            <strong>💡 Smart Strategy:</strong> Place <b>₪{recommended_stake}</b> on a Draw for the next {selected_comp} game.
        </div>
    """, unsafe_allow_html=True)

    with st.form("match_input_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            date_in = st.date_input("Match Date", datetime.date.today())
            home_t = st.text_input("Home Team", value="Brighton" if selected_comp == "Brighton" else "")
            odds_in = st.number_input("Odds for Draw (X)", min_value=1.0, value=3.2, step=0.1)
        with c2:
            away_t = st.text_input("Away Team")
            res_in = st.radio("Outcome", ["Draw (X)", "No Draw"], horizontal=True)
        
        if st.form_submit_button("🚀 Sync Match to Cloud", use_container_width=True):
            if home_t and away_t and worksheet:
                # חישוב רווח משוער לשמירה בגיליון
                est_p = (recommended_stake * odds_in) - recommended_stake if res_in == "Draw (X)" else -recommended_stake
                
                # סדר העמודות: Date, Competition, Home Team, Away Team, Odds, Result, Stake, Profit
                new_row = [str(date_in), selected_comp, home_t, away_t, odds_in, res_in, recommended_stake, est_p]
                worksheet.append_row(new_row)
                st.success("Data synchronized successfully!")
                st.rerun()
            else:
                st.warning("Please complete all match details.")

# 3. Data Visualization
if processed_data:
    df = pd.DataFrame(processed_data)
    
    # טבלת היסטוריה מעוצבת
    st.markdown("### 📜 Match Log")
    def style_status(val):
        color = '#d4edda' if 'Won' in val else '#f8d7da'
        return f'background-color: {color}; color: black;'

    st.dataframe(
        df.style.map(style_status, subset=['Status'])
          .format({"Stake": "₪{:.0f}", "Profit": "₪{:.0f}", "Odds": "{:.2f}"}),
        use_container_width=True, hide_index=True
    )

    # גרף ביצועים
    st.markdown("### 📈 Equity Curve")
    df['Cumulative'] = df['Profit'].cumsum()
    fig = px.line(df, x=df.index, y='Cumulative', title='Account Growth', markers=True)
    fig.update_traces(line_color='#2d6a4f')
    st.plotly_chart(fig, use_container_width=True)
    
    with st.expander("🛠 Maintenance"):
        if st.button("Reset Database"):
            worksheet.resize(rows=1)
            st.rerun()
else:
    st.info("Waiting for data... Add your first match to begin tracking.")