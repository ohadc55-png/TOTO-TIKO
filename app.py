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

# --- NEW BACKGROUND & HIGH CONTRAST CSS ---
bg_img_url = "https://i.postimg.cc/GmFZ4KS7/Gemini-Generated-Image-k1h11zk1h11zk1h1.png"

st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@700;900&display=swap');
    
    /* Background Image - Fixed position */
    [data-testid="stAppViewContainer"] {{
        background-image: linear-gradient(rgba(0, 0, 0, 0.3), rgba(0, 0, 0, 0.5)), url("{bg_img_url}");
        background-attachment: fixed;
        background-size: cover;
        background-position: center center;
    }}

    [data-testid="stHeader"] {{ background: rgba(0,0,0,0); }}

    /* Main glass containers - Darker for contrast against new image */
    .main .block-container {{
        background-color: rgba(0, 0, 0, 0.5); /* Darker tint */
        backdrop-filter: blur(20px); /* Stronger blur */
        border-radius: 25px;
        padding: 40px;
        color: white;
        margin-top: 20px;
        border: 1px solid rgba(255, 255, 255, 0.15);
        box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    }}

    /* Header Styling - Strong Shadows for Readability */
    .pro-header-container {{
        padding: 20px;
        border-radius: 20px;
        text-align: center;
        margin-bottom: 30px;
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
    }}
    .pro-header-text {{
        font-family: 'Montserrat', sans-serif;
        font-weight: 900;
        font-size: 3.8rem;
        color: #ffffff;
        text-transform: uppercase;
        /* Strong shadow to make text pop out */
        text-shadow: 4px 4px 15px rgba(0,0,0,1); 
    }}

    /* Metric Cards */
    .metric-card {{ 
        background-color: rgba(255, 255, 255, 0.95); 
        padding: 25px; 
        border-radius: 18px; 
        text-align: center;
        box-shadow: 0 8px 20px rgba(0,0,0,0.3);
    }}
    .metric-label {{ 
        font-size: 1.1rem; 
        color: #000000; /* Pure black for contrast on white card */
        font-weight: 900; 
        text-transform: uppercase; 
    }}
    .metric-value {{ font-size: 2.2rem; font-weight: 900; color: #1b4332; }}

    /* Sidebar */
    [data-testid="stSidebar"] {{
        background-color: rgba(0, 0, 0, 0.6) !important;
        backdrop-filter: blur(15px);
        border-right: 1px solid rgba(255,255,255,0.1);
    }}
    
    /* Forms & Tables */
    div[data-testid="stForm"] {{ background-color: rgba(255, 255, 255, 0.95); border-radius: 20px; padding: 30px; color: black; }}
    .stDataFrame {{ background-color: rgba(255, 255, 255, 0.95) !important; border-radius: 15px; }}
    
    /* General Text Contrast ensure white text has shadow */
    h1, h2, h3, .stMarkdown p {{
        text-shadow: 2px 2px 8px rgba(0,0,0,0.8);
    }}
    /* Reset shadow for text inside white cards/forms */
    .metric-card p, div[data-testid="stForm"] p, div[data-testid="stForm"] h1, div[data-testid="stForm"] h2, div[data-testid="stForm"] h3 {{
        text-shadow: none;
        color: black !important;
    }}
    </style>
""", unsafe_allow_html=True)

# --- Google Sheets Logic ---
def get_data_from_sheets():
    try:
        gc = gspread.service_account_from_dict(st.secrets["service_account"])
        sh = gc.open_by_url(st.secrets["sheet_url"])
        worksheet = sh.get_worksheet(0)
        data = worksheet.get_all_records()
        try:
            val = worksheet.cell(1, 10).value
            initial_bankroll = float(val) if val else 5000.0
        except:
            initial_bankroll = 5000.0
        return data, worksheet, initial_bankroll
    except Exception as e:
        st.error(f"Sync Error: {e}")
        return [], None, 5000.0

def update_bankroll(worksheet, val):
    try:
        worksheet.update_cell(1, 10, val)
        return True
    except: return False

# --- Core Logic ---
def calculate_logic(raw_data, br_base, af_base):
    processed = []
    next_bets = {"Brighton": float(br_base), "Africa Cup of Nations": float(af_base)}
    cycle_invest = {"Brighton": 0.0, "Africa Cup of Nations": 0.0}

    for i, row in enumerate(raw_data):
        try:
            comp = str(row.get('Competition', 'Brighton')).strip()
            odds = float(str(row.get('Odds', 1)).replace(',', '.'))
            res = str(row.get('Result', '')).strip()
            exp = float(row.get('Stake', next_bets[comp]))
            cycle_invest[comp] += exp
            is_win = "Draw (X)" in res
            
            if is_win:
                inc = exp * odds
                net = inc - cycle_invest[comp]
                roi = f"{(net / cycle_invest[comp]) * 100:.1f}%"
                next_bets[comp] = float(br_base if "Brighton" in comp else af_base)
                cycle_invest[comp] = 0.0
                status = "✅ Won"
            else:
                inc, net, roi = 0.0, -exp, "N/A"
                next_bets[comp] = exp * 2.0
                status = "❌ Lost"
            
            processed.append({
                "Date": row.get('Date', ''), "Comp": comp, "Match": f"{row.get('Home Team', '')} vs {row.get('Away Team', '')}",
                "Odds": odds, "Expense": exp, "Income": inc, "Net Profit": net, "Status": status, "ROI": roi
            })
        except: continue
    return processed, next_bets

# --- Execution ---
raw_data, worksheet, saved_br = get_data_from_sheets()
processed, next_stakes = calculate_logic(raw_data, 30.0, 20.0)

if processed:
    df = pd.DataFrame(processed)
    current_bal = saved_br + (df['Income'].sum() - df['Expense'].sum())
else:
    current_bal, df = saved_br, pd.DataFrame()

# --- Sidebar ---
with st.sidebar:
    st.header("Wallet")
    st.metric("Base Bankroll", f"₪{saved_br:,.0f}")
    amt = st.number_input("Transaction", min_value=0.0, value=100.0)
    c1, c2 = st.columns(2)
    if c1.button("Deposit"):
        if update_bankroll(worksheet, saved_br + amt): st.rerun()
    if c2.button("Withdraw"):
        if update_bankroll(worksheet, saved_br - amt): st.rerun()
    st.divider()
    track = st.selectbox("Current Track", ["Brighton", "Africa Cup of Nations"])
    if st.button("🔄 Sync"): st.rerun()

# --- Dashboard UI ---
st.markdown(f"<div class='pro-header-container'><h1 class='pro-header-text'>{track}</h1></div>", unsafe_allow_html=True)

# High contrast live balance style
st.markdown(f"<h1 style='text-align: center; font-size: 4.5rem; font-weight: 900; color: white; text-shadow: 4px 4px 20px #000000;'>₪{current_bal:,.2f}</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; letter-spacing: 3px; font-weight: bold; color: white; text-shadow: 2px 2px 10px #000;'>LIVE BANKROLL</p>", unsafe_allow_html=True)

# Metrics Cards
f_df = df[df['Comp'] == track] if not df.empty else pd.DataFrame()
t_exp = f_df['Expense'].sum() if not f_df.empty else 0.0
t_inc = f_df['Income'].sum() if not f_df.empty else 0.0
t_net = t_inc - t_exp

col1, col2, col3 = st.columns(3)
with col1: st.markdown(f"<div class='metric-card'><p class='metric-label'>Total Out</p><p class='metric-value'>₪{t_exp:,.0f}</p></div>", unsafe_allow_html=True)
with col2: st.markdown(f"<div class='metric-card'><p class='metric-label'>Total In</p><p class='metric-value'>₪{t_inc:,.0f}</p></div>", unsafe_allow_html=True)
with col3: st.markdown(f"<div class='metric-card' style='border-bottom: 5px solid {'#2d6a4f' if t_net >= 0 else '#ce1126'}'><p class='metric-label'>Net Profit</p><p class='metric-value'>₪{t_net:,.0f}</p></div>", unsafe_allow_html=True)

# Forms and History
st.write("---")
col_form, col_viz = st.columns([1, 1.2])
with col_form:
    with st.form("match_entry"):
        st.subheader("New Entry")
        h = st.text_input("Home", value="Brighton" if track == "Brighton" else "")
        a = st.text_input("Away")
        o = st.number_input("Odds", value=3.2)
        s = st.number_input("Stake", value=float(next_stakes[track]))
        r = st.radio("Result", ["Draw (X)", "No Draw"], horizontal=True)
        if st.form_submit_button("Sync Game 🚀"):
            worksheet.append_row([str(datetime.date.today()), track, h, a, o, r, s, 0.0])
            st.rerun()

with col_viz:
    if not f_df.empty:
        f_df['Growth'] = saved_br + (f_df['Income'].cumsum() - f_df['Expense'].cumsum())
        fig = px.area(f_df, y='Growth', title="Bankroll Curve")
        # Ensure chart text is readable
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white", title_font_size=20, margin=dict(l=0,r=0,t=40,b=0))
        fig.update_traces(line_color='#2d6a4f', fillcolor='rgba(45, 106, 79, 0.4)')
        st.plotly_chart(fig, use_container_width=True)

st.subheader("📜 Activity Log")
if not f_df.empty:
    # Table needs to be opaque to be readable
    st.dataframe(f_df[['Date', 'Match', 'Odds', 'Expense', 'Income', 'Status', 'ROI']].sort_index(ascending=False), use_container_width=True, hide_index=True)

with st.expander("Admin"):
    if st.button("Delete Last Entry"):
        worksheet.delete_rows(len(raw_data) + 1)
        st.rerun()