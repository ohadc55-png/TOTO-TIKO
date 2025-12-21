import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- Page Configuration ---
st.set_page_config(
    page_title="Pro Football Tracker",
    layout="centered",
    page_icon="⚽",
    initial_sidebar_state="expanded"
)

# --- Custom CSS for Modern Football Look ---
st.markdown("""
    <style>
    /* Main Background */
    .stApp {
        background-color: #f8f9fa;
    }
    
    /* Custom Title Styling */
    h1 {
        color: #1b4332; /* Dark Green */
        font-family: 'Helvetica Neue', sans-serif;
        font-weight: 700;
        text-align: center;
    }
    
    /* Metrics Styling */
    div[data-testid="stMetricValue"] {
        font-size: 28px;
        color: #2d6a4f;
    }
    
    /* Buttons */
    .stButton>button {
        border-radius: 20px;
        font-weight: bold;
        border: none;
        transition: 0.3s;
    }
    
    /* Success/Green messages */
    .stAlert {
        border-radius: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# --- Sidebar Settings ---
with st.sidebar:
    st.title("⚙️ Tactics Board")
    st.markdown("Configure your betting strategy.")
    
    team_name = st.text_input("Selected Team", "Hapoel Be'er Sheva")
    initial_stake = st.number_input("Initial Stake (₪)", min_value=10, value=50, step=10)
    
    st.divider()
    st.markdown("### Strategy info")
    st.info("Martingale on Draw:\nDoubling stake on loss,\nResetting stake on Draw.")

# --- Session State Management ---
if 'games' not in st.session_state:
    st.session_state.games = []

# --- Logic: Calculation Function ---
def calculate_status(games, start_stake):
    processed_games = []
    current_stake = start_stake
    total_invested = 0
    total_revenue = 0
    balance_history = []
    
    running_balance = 0 # Starting from 0
    
    for game in games:
        invested = current_stake
        total_invested += invested
        
        is_draw = game['result'] == "Draw (X)"
        odds = game['odds']
        
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
            "Date": game['date'],
            "Opponent": game['opponent'],
            "Odds": odds,
            "Stake": invested,
            "Result": game['result'],
            "Status": status,
            "Game P/L": profit,
            "Total Balance": running_balance
        }
        processed_games.append(processed_game)
        balance_history.append(running_balance)
        
        current_stake = next_stake

    return processed_games, current_stake, total_invested, total_revenue, running_balance if balance_history else 0

# --- MAIN UI ---

# 1. Header
st.markdown(f"<h1>⚽ {team_name} Tracker</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: grey;'>Professional Martingale Strategy Dashboard</p>", unsafe_allow_html=True)
st.write("") # Spacer

# Run calculations
processed_data, next_stake, total_inv, total_rev, total_bal = calculate_status(st.session_state.games, initial_stake)

# 2. Key Stats Area (Top Dashboard)
st.markdown("### 📊 Performance Overview")
col1, col2, col3 = st.columns(3)

with col1:
    st.container(border=True).metric("Total Invested", f"₪{total_inv:,.0f}")
with col2:
    st.container(border=True).metric("Total Returned", f"₪{total_rev:,.0f}")
with col3:
    color = "normal" if total_bal >= 0 else "inverse"
    st.container(border=True).metric("Net Profit", f"₪{total_bal:,.0f}", delta=total_bal, delta_color=color)

# 3. Action Area (Input Form)
st.write("")
st.markdown("### 📝 Match Day Input")

with st.container(border=True):
    # Recommended Stake Highlight
    st.markdown(f"""
        <div style='background-color: #d8f3dc; padding: 15px; border-radius: 10px; border-left: 5px solid #2d6a4f; margin-bottom: 20px;'>
            <strong style='color: #1b4332;'>💡 Next Match Strategy:</strong> 
            Place a bet of <span style='font-size: 1.2em; font-weight: bold;'>₪{next_stake}</span> on X (Draw).
        </div>
    """, unsafe_allow_html=True)

    with st.form("add_game_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            date = st.date_input("Match Date")
            odds = st.number_input("Odds (X)", min_value=1.0, value=3.0, step=0.1)
        with c2:
            opponent = st.text_input("Opponent Name", placeholder="e.g. Maccabi Tel Aviv")
            result = st.radio("Result", ["Draw (X)", "Win/Loss"], horizontal=True)
        
        st.write("")
        submitted = st.form_submit_button("⚽ Add Match Result", use_container_width=True)
        
        if submitted:
            if opponent:
                st.session_state.games.append({
                    "date": date,
                    "opponent": opponent,
                    "odds": odds,
                    "result": result
                })
                st.success("Match logged successfully!")
                st.rerun()
            else:
                st.error("Please enter opponent name.")

# 4. Visualization Area
if st.session_state.games:
    df = pd.DataFrame(processed_data)
    
    st.write("")
    st.markdown("### 📈 Profit Trajectory")
    
    # Custom Plotly Design
    fig = px.area(df, x="Date", y="Total Balance", markers=True)
    fig.update_traces(line_color='#2d6a4f', fillcolor='rgba(45, 106, 79, 0.2)')
    fig.update_layout(
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(family="Helvetica", size=12, color="#333"),
        xaxis_title="",
        yaxis_title="Balance (₪)",
        margin=dict(l=20, r=20, t=30, b=20),
        hovermode="x unified"
    )
    # Add a zero line
    fig.add_hline(y=0, line_dash="dot", line_color="red", opacity=0.5)
    
    st.plotly_chart(fig, use_container_width=True)

    # 5. History Table
    st.markdown("### 📜 Match History")
    
    # Custom formatting for the dataframe
    def color_status(val):
        color = '#d4edda' if val == '✅ Won' else '#f8d7da'
        return f'background-color: {color}; color: black; border-radius: 5px;'

    st.dataframe(
        df.style.applymap(color_status, subset=['Status'])
          .format({"Stake": "₪{:.0f}", "Game P/L": "₪{:.0f}", "Total Balance": "₪{:.0f}", "Odds": "{:.2f}"}),
        use_container_width=True,
        hide_index=True
    )
    
    # Reset
    st.write("")
    if st.button("🔄 Reset All Data", type="primary"):
        st.session_state.games = []
        st.rerun()

else:
    st.write("")
    st.info("Start tracking by adding the first match above.")