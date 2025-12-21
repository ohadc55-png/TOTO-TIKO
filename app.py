import streamlit as st
import pandas as pd
import plotly.express as px
import gspread

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

# --- Google Sheets Connection Function ---
def get_data_from_sheets():
    try:
        # Access secrets securely
        gc = gspread.service_account_from_dict(st.secrets["service_account"])
        sh = gc.open_by_url(st.secrets["sheet_url"])
        worksheet = sh.get_worksheet(0)
        data = worksheet.get_all_records()
        return data, worksheet
    except Exception as e:
        st.error(f"Connection Error: {e}")
        return [], None

# --- Logic: Calculation Function ---
def calculate_status(games_data, start_stake):
    processed_games = []
    current_stake = start_stake
    total_invested = 0
    total_revenue = 0
    balance_history = []
    
    running_balance = 0 
    
    for game in games_data:
        try:
            # Safe conversion of data
            odds = float(game['Odds'])
            res_str = str(game['Result'])
        except:
            continue 

        invested = current_stake
        total_invested += invested
        
        is_draw = "Draw" in res_str or "תיקו" in res_str or "X" in res_str
        
        revenue = 0
        profit = -invested 
        
        if is_draw:
            revenue = invested * odds
            profit = revenue - invested
            next_stake = start_stake 
            status = "✅ Won"
        else:
            next_stake = current_stake * 2 
            status = "❌ Lost"
            
        total_revenue += revenue
        running_balance = total_revenue - total_invested
        
        processed_game = {
            "Date": game['Date'],
            "Opponent": game['Opponent'],
            "Odds": odds,
            "Stake": invested,
            "Result": res_str,
            "Status": status,
            "Game P/L": profit,
            "Total Balance": running_balance
        }
        processed_games.append(processed_game)
        balance_history.append(running_balance)
        
        current_stake = next_stake

    return processed_games, current_stake, total_invested, total_revenue, running_balance if balance_history else 0

# --- Sidebar ---
with st.sidebar:
    st.title("⚙️ Tactics Board")
    team_name = st.text_input("Selected Team", "Hapoel Be'er Sheva")
    initial_stake = st.number_input("Initial Stake", min_value=10, value=50, step=10)
    st.divider()
    st.info("Connected to Google Sheets Database 🟢")

# --- MAIN APP FLOW ---

# 1. Load Data
raw_data, worksheet = get_data_from_sheets()

# 2. Run Calculations
processed_data, next_stake, total_inv, total_rev, total_bal = calculate_status(raw_data, initial_stake)

# Header
st.markdown(f"<h1>⚽ {team_name} Tracker</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: grey;'>Live Cloud Database</p>", unsafe_allow_html=True)

# 3. Key Stats
st.markdown("### 📊 Performance Overview")
col1, col2, col3 = st.columns(3)
with col1:
    st.container(border=True).metric("Total Invested", f"{total_inv:,.0f}")
with col2:
    st.container(border=True).metric("Total Returned", f"{total_rev:,.0f}")
with col3:
    color = "normal" if total_bal >= 0 else "inverse"
    st.container(border=True).metric("Net Profit", f"{total_bal:,.0f}", delta=total_bal, delta_color=color)

# 4. Input Form
st.write("")
st.markdown("### 📝 Match Day Input")

with st.container(border=True):
    # Recommended Stake
    st.markdown(f"""
        <div style='background-color: #d8f3dc; padding: 15px; border-radius: 10px; border-left: 5px solid #2d6a4f; margin-bottom: 20px;'>
            <strong style='color: #1b4332;'>💡 Next Match Strategy:</strong> 
            Place a bet of <span style='font-size: 1.2em; font-weight: bold;'>{next_stake}</span> on X (Draw).
        </div>
    """, unsafe_allow_html=True)

    with st.form("add_game_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            date_input = st.date_input("Match Date")
            odds_input = st.number_input("Odds (X)", min_value=1.0, value=3.0, step=0.1)
        with c2:
            opponent_input = st.text_input("Opponent Name")
            result_input = st.radio("Result", ["Draw (X)", "Win/Loss"], horizontal=True)
        
        # FIX: Changed use_container_width=True to width='stretch'
        submitted = st.form_submit_button("⚽ Add Match to Cloud", width='stretch')
        
        if submitted and worksheet:
            if opponent_input:
                new_row = [str(date_input), opponent_input, odds_input, result_input]
                worksheet.append_row(new_row)
                st.success("Saved to Google Sheets!")
                st.rerun()
            else:
                st.error("Please enter opponent name.")

# 5. Visuals
if processed_data:
    df = pd.DataFrame(processed_data)
    
    st.write("")
    st.markdown("### 📈 Profit Trajectory")
    
    fig = px.area(df, x="Date", y="Total Balance", markers=True)
    fig.update_traces(line_color='#2d6a4f', fillcolor='rgba(45, 106, 79, 0.2)')
    fig.update_layout(
        plot_bgcolor='white', paper_bgcolor='white',
        font=dict(family="Helvetica", size=12, color="#333"),
        xaxis_title="", yaxis_title="Balance",
        margin=dict(l=20, r=20, t=30, b=20), hovermode="x unified"
    )
    fig.add_hline(y=0, line_dash="dot", line_color="red", opacity=0.5)
    
    # FIX: Changed use_container_width=True to width='stretch'
    st.plotly_chart(fig, width='stretch')

    st.markdown("### 📜 Match History")
    
    def color_status(val):
        color = '#d4edda' if 'Won' in val else '#f8d7da'
        return f'background-color: {color}; color: black; border-radius: 5px;'

    # FIX: Changed applymap() to map() and use_container_width=True to width='stretch'
    st.dataframe(
        df.style.map(color_status, subset=['Status'])
          .format({"Stake": "{:.0f}", "Game P/L": "{:.0f}", "Total Balance": "{:.0f}", "Odds": "{:.2f}"}),
        width='stretch', hide_index=True
    )
    
    with st.expander("⚠️ Danger Zone"):
        if st.button("Delete Database History"):
            worksheet.resize(rows=1) 
            st.warning("Database cleared.")
            st.rerun()
else:
    st.info("Database is empty. Add the first match above.")