import streamlit as st
import pandas as pd
import plotly.express as px
import gspread
import datetime

# --- LOGO URL ---
# מוודא שהכתובת קיימת
APP_LOGO_URL = "https://i.postimg.cc/65DbKPtp/Gemini-Generated-Image-hg9cahhg9cahhg9c.png"

# --- Page Configuration ---
st.set_page_config(
    page_title="Elite Football Tracker",
    layout="wide",
    page_icon=APP_LOGO_URL, # הלוגו בטאב של הדפדפן
    initial_sidebar_state="expanded"
)

# --- GLOBAL STYLES & BACKGROUND ---
bg_img_url = "https://i.postimg.cc/GmFZ4KS7/Gemini-Generated-Image-k1h11zk1h11zk1h1.png"

st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;700;900&family=Inter:wght@400;700&display=swap');
    
    /* 1. Main Background */
    [data-testid="stAppViewContainer"] {{
        background-image: linear-gradient(rgba(0, 0, 0, 0.5), rgba(0, 0, 0, 0.5)), url("{bg_img_url}");
        background-attachment: fixed;
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
    }}
    
    /* 2. Header Transparency */
    [data-testid="stHeader"] {{ 
        background: rgba(0,0,0,0) !important; 
    }}

    /* --- SMART CONTRAST STRATEGY --- */

    /* ZONE A: DARK BACKGROUNDS (Main Page Text, Headers, Sidebar) -> WHITE TEXT */
    h1, h2, h3, h4, h5, h6, 
    .stMarkdown, .stText, 
    [data-testid="stMetricLabel"], 
    [data-testid="stMetricValue"],
    [data-testid="stSidebar"] {{
        color: #ffffff !important;
        text-shadow: 2px 2px 4px #000000;
        font-family: 'Montserrat', sans-serif;
    }}

    /* ZONE B: LIGHT BACKGROUNDS -> BLACK TEXT */
    
    /* 1. Forms */
    [data-testid="stForm"] {{
        background-color: rgba(255, 255, 255, 0.95);
        border-radius: 20px;
        padding: 30px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.6);
        border: 2px solid rgba(255,255,255,0.3);
    }}
    [data-testid="stForm"] *, [data-testid="stForm"] label, [data-testid="stForm"] p {{
        color: #111111 !important;
        text-shadow: none !important;
    }}

    /* 2. Activity Log Table (DataFrame) */
    [data-testid="stDataFrame"] {{
        background-color: white;
        border-radius: 10px;
        padding: 10px;
    }}
    [data-testid="stDataFrame"] *, [data-testid="stDataFrame"] th, [data-testid="stDataFrame"] td {{
        color: #111111 !important; /* Force Black Text inside tables */
        text-shadow: none !important;
    }}

    /* 3. Custom Metric Cards */
    .custom-metric-box {{
        background-color: rgba(255, 255, 255, 0.95);
        border-radius: 15px;
        padding: 25px;
        text-align: center;
        box-shadow: 0 6px 20px rgba(0,0,0,0.6);
        margin-bottom: 20px;
        border: 2px solid rgba(255,255,255,0.3);
    }}
    .custom-metric-box * {{
        color: #111111 !important;
        text-shadow: none !important;
    }}
    .metric-card-label {{
        font-size: 14px;
        font-weight: bold;
        text-transform: uppercase;
        color: #555 !important;
        margin-bottom: 10px;
    }}
    .metric-card-value {{
        font-size: 28px;
        font-weight: 900;
        color: #1b4332 !important;
        line-height: 1.2;
    }}
    
    /* 4. Expander (Admin Section) Fix */
    .streamlit-expanderContent, .streamlit-expanderContent * {{
        color: #111111 !important;
        text-shadow: none !important;
        background-color: rgba(255, 255, 255, 0.95); /* Ensure light background */
    }}

    /* 5. Sidebar Buttons */
    [data-testid="stSidebar"] div[data-testid="stButton"] button {{
        background-color: rgba(45, 106, 79, 0.9) !important;
        color: white !important;
        font-weight: 600 !important;
        font-size: 12px !important;
        border: none !important;
        border-radius: 6px !important;
        padding: 0px 2px !important;
        min-height: 40px !important;
        width: 100% !important;
        white-space: nowrap !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        text-shadow: none !important;
    }}
    
    [data-testid="stSidebar"] div[data-testid="stButton"] button:hover {{
        background-color: rgba(27, 67, 50, 1) !important;
        transform: scale(1.02);
    }}
    
    /* 6. Inputs */
    input {{
        color: #000000 !important;
    }}

    </style>
""", unsafe_allow_html=True)

# --- LOGIC & DATA PARSING ---
def get_data_from_sheets():
    try:
        gc = gspread.service_account_from_dict(st.secrets["service_account"])
        sh = gc.open_by_url(st.secrets["sheet_url"])
        worksheet = sh.get_worksheet(0)
        data = worksheet.get_all_records()
        try:
            val = worksheet.cell(1, 10).value
            initial_bankroll = float(val) if val else 5000.0
        except: initial_bankroll = 5000.0
        return data, worksheet, initial_bankroll
    except Exception as e:
        st.error(f"Sync Error: {e}")
        return [], None, 5000.0

def update_bankroll(worksheet, val):
    try:
        worksheet.update_cell(1, 10, val)
        return True
    except: return False

def calculate_logic(raw_data, br_base, af_base):
    processed = []
    next_bets = {"Brighton": float(br_base), "Africa Cup of Nations": float(af_base)}
    cycle_invest = {"Brighton": 0.0, "Africa Cup of Nations": 0.0}

    for i, row in enumerate(raw_data):
        try:
            comp = str(row.get('Competition', 'Brighton')).strip()
            
            try:
                odds = float(str(row.get('Odds', 1)).replace(',', '.'))
            except:
                odds = 1.0

            res = str(row.get('Result', '')).strip()

            raw_stake = row.get('Stake')
            if raw_stake == '' or raw_stake is None:
                exp = next_bets[comp]
            else:
                try:
                    exp = float(str(raw_stake).replace(',', ''))
                except:
                    exp = next_bets[comp]

            cycle_invest[comp] += exp
            is_win = "Draw (X)" in res
            
            if is_win:
                inc = exp * odds
                net = inc - cycle_invest[comp]
                try:
                    roi_val = (net / cycle_invest[comp]) * 100
                    roi = f"{roi_val:.1f}%"
                except:
                    roi = "0.0%"
                
                next_bets[comp] = float(br_base if "Brighton" in comp else af_base)
                cycle_invest[comp] = 0.0
                status = "✅ Won"
            else:
                inc, net, roi = 0.0, -exp, "N/A"
                next_bets[comp] = exp * 2.0
                status = "❌ Lost"
            
            processed.append({
                "Date": row.get('Date', ''), 
                "Comp": comp, 
                "Match": f"{row.get('Home Team', '')} vs {row.get('Away Team', '')}",
                "Odds": odds, 
                "Expense": exp, 
                "Income": inc, 
                "Net Profit": net, 
                "Status": status, 
                "ROI": roi
            })
        except:
            continue
            
    return processed, next_bets

# --- MAIN EXECUTION ---
raw_data, worksheet, saved_br = get_data_from_sheets()
processed, next_stakes = calculate_logic(raw_data, 30.0, 20.0)

if processed:
    df = pd.DataFrame(processed)
    current_bal = saved_br + (df['Income'].sum() - df['Expense'].sum())
    total_expenses = df['Expense'].sum()
    total_revenue = df['Income'].sum()
    net_profit = total_revenue - total_expenses
else:
    current_bal, df = saved_br, pd.DataFrame()
    total_expenses, total_revenue, net_profit = 0.0, 0.0, 0.0

# --- SIDEBAR ---
with st.sidebar:
    # כאן מוצג הלוגו בסרגל הצד
    st.image(APP_LOGO_URL, use_container_width=True)
    
    st.markdown("## WALLET CONTROL")
    st.metric("Base Bankroll", f"₪{saved_br:,.0f}")
    amt = st.number_input("Transaction Amount", min_value=0.0, value=100.0)
    
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Deposit"):
            if update_bankroll(worksheet, saved_br + amt): st.rerun()
    with c2:
        if st.button("Withdraw"):
            if update_bankroll(worksheet, saved_br - amt): st.rerun()
        
    st.divider()
    track = st.selectbox("Current Track", ["Brighton", "Africa Cup of Nations"])
    if st.button("🔄 Sync Cloud"): st.rerun()

# --- BANNER ---
brighton_logo = "https://i.postimg.cc/x8kdQh5H/Brighton_Hove_Albion_logo.png"
afcon_logo = "https://i.postimg.cc/5yHtJTgz/2025_Africa_Cup_of_Nations_logo.png"

if track == "Brighton":
    # שינוי צבע האמצע ללבן-תכלת בהיר מאוד במקום לבן נקי
    banner_bg = "linear-gradient(90deg, #4CABFF 0%, #E6F7FF 50%, #4CABFF 100%)"
    text_color = "#0057B8"
    logo_src = brighton_logo
    shadow_style = "none"
else:
    banner_bg = "linear-gradient(90deg, #CE1126 0%, #FCD116 50%, #007A33 100%)"
    text_color = "#FFFFFF"
    logo_src = afcon_logo
    shadow_style = "3px 3px 6px #000000, 1px 1px 2px #000000"

st.markdown(f"""
    <div style="
        background: {banner_bg};
        border-radius: 20px;
        padding: 25px 40px;
        display: flex;
        align-items: center;
        justify-content: flex-start;
        margin-bottom: 40px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.6);
        border: 2px solid rgba(255,255,255,0.3);
    ">
        <img src="{logo_src}" style="height: 80px; margin-right: 30px; filter: drop-shadow(0 5px 10px rgba(0,0,0,0.4));">
        <h1 style="
            margin: 0;
            font-size: 2.5rem;
            font-weight: 900;
            text-transform: uppercase;
            color: {text_color} !important;
            text-shadow: {shadow_style};
            font-family: 'Montserrat', sans-serif;
            letter-spacing: 3px;
            flex: 1;
            text-align: left;
        ">{track.upper()}</h1>
    </div>
""", unsafe_allow_html=True)

# --- LIVE BALANCE (SIZE 2.3rem) ---
st.markdown(f"""
    <div style="text-align: center; margin-bottom: 40px;">
        <div style="
            font-size: 2.3rem !important; 
            font-weight: 300 !important; 
            color: #ffffff !important; 
            text-shadow: 0px 0px 15px rgba(255,255,255,0.2) !important; 
            line-height: 1.2; 
            margin-bottom: 5px; 
            letter-spacing: 2px;
            font-family: 'Montserrat', sans-serif;">
            ₪{current_bal:,.2f}
        </div>
        <div style="
            font-size: 0.8rem !important; 
            font-weight: 400 !important; 
            color: rgba(255,255,255,0.7) !important; 
            letter-spacing: 3px; 
            text-shadow: none !important;
            text-transform: uppercase;">
            LIVE BANKROLL
        </div>
    </div>
""", unsafe_allow_html=True)

# --- METRIC CARDS ---
f_df = df[df['Comp'] == track] if not df.empty else pd.DataFrame()

if not f_df.empty:
    m_exp = f_df['Expense'].sum()
    m_inc = f_df['Income'].sum()
    m_net = m_inc - m_exp
else:
    m_exp, m_inc, m_net = 0.0, 0.0, 0.0

c1, c2, c3 = st.columns(3)
with c1:
    st.markdown(f"""
        <div class="custom-metric-box">
            <div class="metric-card-label">TOTAL EXPENSES</div>
            <div class="metric-card-value">₪{m_exp:,.0f}</div>
        </div>
    """, unsafe_allow_html=True)
with c2:
    st.markdown(f"""
        <div class="custom-metric-box">
            <div class="metric-card-label">TOTAL REVENUE</div>
            <div class="metric-card-value">₪{m_inc:,.0f}</div>
        </div>
    """, unsafe_allow_html=True)
with c3:
    st.markdown(f"""
        <div class="custom-metric-box">
            <div class="metric-card-label">NET PROFIT</div>
            <div class="metric-card-value" style="color: {'#2d6a4f' if m_net >= 0 else '#d32f2f'} !important;">₪{m_net:,.0f}</div>
        </div>
    """, unsafe_allow_html=True)

# --- NEXT BET ---
st.markdown(f"""
    <div style="text-align: center; margin: 30px 0;">
        <p style="font-size: 1.5rem; font-weight: bold; color: white; text-shadow: 3px 3px 6px #000;">
            Next Bet: <span style="color: #4CAF50; text-shadow: 2px 2px 4px #000;">₪{next_stakes.get(track, 30.0):,.0f}</span>
        </p>
    </div>
""", unsafe_allow_html=True)

# --- FORM ---
col_form, col_intel = st.columns([1, 1])

with col_form:
    with st.form("match_entry"):
        st.subheader("Add Match")
        h = st.text_input("Home", value="Brighton" if track == "Brighton" else "")
        a = st.text_input("Away")
        od = st.number_input("Odds", value=3.2, step=0.1, min_value=1.0)
        suggested_stake = next_stakes.get(track, 30.0)
        stk = st.number_input("Stake to Bet", value=float(suggested_stake), min_value=1.0, step=5.0)
        res = st.radio("Result", ["Draw (X)", "No Draw"], horizontal=True)
        if st.form_submit_button("Sync Game"):
            if h and a:
                worksheet.append_row([str(datetime.date.today()), track, h, a, od, res, stk, 0.0])
                st.toast("Match Saved!", icon="✅")
                st.rerun()
            else:
                st.warning("Enter Team Names")

with col_intel:
    st.subheader("Strategy & Stats")
    if not f_df.empty:
        f_df['Chart'] = saved_br + (f_df['Income'].cumsum() - f_df['Expense'].cumsum())
        fig = px.line(f_df, y='Chart', title="Track Performance", labels={'Chart': 'Balance (₪)', 'index': 'Match'})
        fig.update_traces(line_color='#2d6a4f', line_width=3)
        fig.update_layout(
            height=300, margin=dict(l=0, r=0, t=30, b=0),
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white', size=12), title_font=dict(color='white', size=16)
        )
        st.plotly_chart(fig, use_container_width=True)
        
        wins = len(f_df[f_df['Status'] == "✅ Won"])
        losses = len(f_df[f_df['Status'] == "❌ Lost"])
        win_rate = (wins / len(f_df) * 100) if len(f_df) > 0 else 0
        st.markdown(f"""
            <div style="background-color: rgba(255, 255, 255, 0.95); padding: 20px; border-radius: 12px; color: #1b5e20;">
                <b>Win Rate:</b> {win_rate:.1f}% ({wins}W / {losses}L)
            </div>
        """, unsafe_allow_html=True)

# --- ACTIVITY LOG ---
st.subheader("📜 Activity Log")
if not f_df.empty:
    # Force styling with black text
    def highlight_results(row):
        bg = '#d4edda' if 'Won' in str(row['Status']) else '#f8d7da'
        return [f'background-color: {bg}; color: #000000 !important; font-weight: 500;'] * len(row)
    
    display_df = f_df[['Date', 'Match', 'Odds', 'Expense', 'Income', 'Net Profit', 'Status', 'ROI']].copy()
    display_df = display_df.sort_index(ascending=False)
    
    st.dataframe(
        display_df.style.apply(highlight_results, axis=1),
        use_container_width=True,
        hide_index=True
    )
else:
    st.info("No data available")

with st.expander("🛠️ Admin"):
    if st.button("Undo Last"):
        if len(raw_data) > 0:
            try:
                worksheet.delete_rows(len(raw_data) + 1)
                st.toast("Last entry removed", icon="🗑️")
                st.rerun()
            except:
                st.error("Error deleting")
        else:
            st.warning("No entries")