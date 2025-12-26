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

# --- GLOBAL STYLES & BACKGROUND ---
bg_img_url = "https://i.postimg.cc/GmFZ4KS7/Gemini-Generated-Image-k1h11zk1h11zk1h1.png"

st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;700;900&family=Inter:wght@400;700&display=swap');
    
    /* 1. Main Background with Dark Overlay */
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

    /* 3. Global Text Visibility - White with Black Shadow (CRITICAL) */
    h1, h2, h3, h4, h5, h6, p, label, 
    .stMarkdown, 
    div[data-testid="stMetricLabel"],
    div[data-testid="stMetricValue"],
    .stSubheader,
    .stText {{
        color: #ffffff !important;
        text-shadow: 3px 3px 6px #000000, 1px 1px 2px #000000 !important;
        font-family: 'Montserrat', sans-serif;
        font-weight: 700 !important;
    }}
    
    /* Exception: Text inside white forms and metric cards - BLACK (CRITICAL FIX) */
    div[data-testid="stForm"],
    div[data-testid="stForm"] *,
    div[data-testid="stForm"] label,
    div[data-testid="stForm"] p,
    div[data-testid="stForm"] input,
    div[data-testid="stForm"] .stTextInput,
    div[data-testid="stForm"] .stTextInput *,
    div[data-testid="stForm"] .stTextInput label,
    div[data-testid="stForm"] .stNumberInput,
    div[data-testid="stForm"] .stNumberInput *,
    div[data-testid="stForm"] .stNumberInput label,
    div[data-testid="stForm"] .stRadio,
    div[data-testid="stForm"] .stRadio *,
    div[data-testid="stForm"] .stRadio label,
    div[data-testid="stForm"] h3,
    div[data-testid="stForm"] h4,
    div[data-testid="stForm"] h5,
    div[data-testid="stForm"] h6,
    .custom-metric-box,
    .custom-metric-box *,
    .custom-metric-box div,
    .metric-card-label,
    .metric-card-value,
    div[data-testid="stDataFrame"],
    div[data-testid="stDataFrame"] *,
    div[data-testid="stDataFrame"] table,
    div[data-testid="stDataFrame"] th,
    div[data-testid="stDataFrame"] td {{
        color: #111111 !important;
        text-shadow: none !important;
    }}

    /* 4. Sidebar Styling */
    [data-testid="stSidebar"] {{
        background-color: rgba(0, 0, 0, 0.75) !important;
        backdrop-filter: blur(10px);
        border-right: 1px solid rgba(255,255,255,0.2);
    }}
    
    [data-testid="stSidebar"] * {{
        color: #ffffff !important;
        text-shadow: 2px 2px 4px #000000 !important;
    }}
    
    [data-testid="stSidebar"] label {{
        color: #ffffff !important;
        text-shadow: 2px 2px 4px #000000 !important;
    }}

    /* 5. Custom Metric Cards (White Box) */
    .custom-metric-box {{
        background-color: rgba(255, 255, 255, 0.95);
        border-radius: 15px;
        padding: 25px;
        text-align: center;
        box-shadow: 0 6px 20px rgba(0,0,0,0.6);
        margin-bottom: 20px;
        border: 2px solid rgba(255,255,255,0.3);
    }}
    .metric-card-label {{
        font-size: 14px;
        font-weight: bold;
        text-transform: uppercase;
        color: #555 !important;
        letter-spacing: 1px;
        margin-bottom: 10px;
    }}
    .metric-card-value {{
        font-size: 28px;
        font-weight: 900;
        color: #1b4332 !important;
        line-height: 1.2;
    }}

    /* 6. Form Styling - White Background */
    div[data-testid="stForm"] {{
        background-color: rgba(255, 255, 255, 0.95) !important;
        border-radius: 20px;
        padding: 30px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.6);
        border: 2px solid rgba(255,255,255,0.3);
    }}
    
    /* 7. Streamlit Metric Component Override */
    div[data-testid="stMetric"] {{
        background-color: rgba(255, 255, 255, 0.1);
        padding: 15px;
        border-radius: 10px;
        border: 1px solid rgba(255,255,255,0.2);
    }}
    
    /* 8. Button Styling */
    div[data-testid="stButton"] > button {{
        background-color: rgba(45, 106, 79, 0.9);
        color: white;
        font-weight: bold;
        border: none;
        border-radius: 8px;
        padding: 10px 20px;
        transition: all 0.3s;
    }}
    
    div[data-testid="stButton"] > button:hover {{
        background-color: rgba(27, 67, 50, 1);
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.3);
    }}
    
    /* 9. Input Fields in Forms */
    div[data-testid="stForm"] input,
    div[data-testid="stForm"] .stTextInput > div > div > input {{
        background-color: #ffffff;
        color: #000000;
        border: 2px solid #ddd;
    }}
    
    /* 10. Table Styling - White Background with Black Text */
    .stDataFrame,
    div[data-testid="stDataFrame"],
    div[data-testid="stDataFrame"] *,
    div[data-testid="stDataFrame"] table,
    div[data-testid="stDataFrame"] thead,
    div[data-testid="stDataFrame"] tbody,
    div[data-testid="stDataFrame"] tr,
    div[data-testid="stDataFrame"] th,
    div[data-testid="stDataFrame"] td {{
        background-color: rgba(255, 255, 255, 0.95) !important;
        border-radius: 10px;
        padding: 10px;
        color: #111111 !important;
        text-shadow: none !important;
    }}
    
    /* 11. Additional White Container Text Fix */
    div[style*="background-color: rgba(255, 255, 255"],
    div[style*="background-color: white"],
    div[style*="background: rgba(255, 255, 255"],
    div[style*="background: white"] {{
        color: #111111 !important;
    }}
    
    div[style*="background-color: rgba(255, 255, 255"] *,
    div[style*="background-color: white"] *,
    div[style*="background: rgba(255, 255, 255"] *,
    div[style*="background: white"] * {{
        color: #111111 !important;
        text-shadow: none !important;
    }}
    </style>
""", unsafe_allow_html=True)

# --- LOGIC (UNCHANGED) ---
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

# --- DATA LOADING ---
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
    st.markdown("## WALLET CONTROL")
    st.metric("Base Bankroll", f"₪{saved_br:,.0f}")
    amt = st.number_input("Transaction Amount", min_value=0.0, value=100.0)
    c1, c2 = st.columns(2)
    if c1.button("Deposit"):
        if update_bankroll(worksheet, saved_br + amt): st.rerun()
    if c2.button("Withdraw"):
        if update_bankroll(worksheet, saved_br - amt): st.rerun()
    st.divider()
    track = st.selectbox("Current Track", ["Brighton", "Africa Cup of Nations"])
    if st.button("🔄 Sync Cloud"): st.rerun()

# --- CUSTOM BRANDED BANNER (HTML/CSS Injection) ---
brighton_logo = "https://i.postimg.cc/x8kdQh5H/Brighton_Hove_Albion_logo.png"
afcon_logo = "https://i.postimg.cc/5yHtJTgz/2025_Africa_Cup_of_Nations_logo.png"

if track == "Brighton":
    banner_bg = "linear-gradient(90deg, #4CABFF 0%, #FFFFFF 50%, #4CABFF 100%)"
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

# --- LIVE BALANCE HERO ---
st.markdown(f"""
    <div style="text-align: center; margin-bottom: 40px;">
        <div style="font-size: 3rem; font-weight: 500; color: white; text-shadow: 2px 2px 6px rgba(0,0,0,0.4), 1px 1px 3px rgba(0,0,0,0.3); line-height: 1.2; margin-bottom: 12px; letter-spacing: 1px;">
            ₪{current_bal:,.2f}
        </div>
        <div style="font-size: 0.9rem; font-weight: 500; color: rgba(255,255,255,0.9); letter-spacing: 4px; text-shadow: 1px 1px 3px rgba(0,0,0,0.4);">
            LIVE BANKROLL
        </div>
    </div>
""", unsafe_allow_html=True)

# --- METRIC CARDS (3 Columns) ---
f_df = df[df['Comp'] == track] if not df.empty else pd.DataFrame()
t_exp = f_df['Expense'].sum() if not f_df.empty else 0.0
t_inc = f_df['Income'].sum() if not f_df.empty else 0.0
t_net = t_inc - t_exp

c1, c2, c3 = st.columns(3)
with c1:
    st.markdown(f"""
        <div class="custom-metric-box">
            <div class="metric-card-label">TOTAL EXPENSES</div>
            <div class="metric-card-value">₪{total_expenses:,.0f}</div>
        </div>
    """, unsafe_allow_html=True)
with c2:
    st.markdown(f"""
        <div class="custom-metric-box">
            <div class="metric-card-label">TOTAL REVENUE</div>
            <div class="metric-card-value">₪{total_revenue:,.0f}</div>
        </div>
    """, unsafe_allow_html=True)
with c3:
    st.markdown(f"""
        <div class="custom-metric-box">
            <div class="metric-card-label">NET PROFIT</div>
            <div class="metric-card-value" style="color: {'#2d6a4f' if net_profit >= 0 else '#d32f2f'} !important;">₪{net_profit:,.0f}</div>
        </div>
    """, unsafe_allow_html=True)

# --- NEXT BET DISPLAY ---
st.markdown(f"""
    <div style="text-align: center; margin: 30px 0;">
        <p style="font-size: 1.5rem; font-weight: bold; color: white; text-shadow: 3px 3px 6px #000;">
            Next Bet: <span style="color: #4CAF50; text-shadow: 2px 2px 4px #000;">₪{next_stakes.get(track, 30.0):,.0f}</span>
        </p>
    </div>
""", unsafe_allow_html=True)

# --- ENTRY FORM & STATS ---
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
                st.warning("Please fill in both Home and Away teams")

with col_intel:
    st.subheader("Strategy & Stats")
    if not df.empty:
        f_df = df[df['Comp'] == track].copy()
        if not f_df.empty:
            f_df['Chart'] = saved_br + (f_df['Income'].cumsum() - f_df['Expense'].cumsum())
            fig = px.line(f_df, y='Chart', title="Track Performance", labels={'Chart': 'Balance (₪)', 'index': 'Match'})
            fig.update_traces(line_color='#2d6a4f', line_width=3)
            fig.update_layout(
                height=300,
                margin=dict(l=0, r=0, t=30, b=0),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='white', size=12),
                title_font=dict(color='white', size=16)
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
if not df.empty:
    f_df = df[df['Comp'] == track].copy()
    if not f_df.empty:
        def highlight_results(row):
            color = '#d4edda' if 'Won' in str(row['Status']) else '#f8d7da'
            return [f'background-color: {color}'] * len(row)
        
        display_df = f_df[['Date', 'Match', 'Odds', 'Expense', 'Income', 'Net Profit', 'Status', 'ROI']].copy()
        display_df = display_df.sort_index(ascending=False)
        
        st.dataframe(
            display_df.style.apply(highlight_results, axis=1),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No matches recorded yet for this competition")
else:
    st.info("No data available")

with st.expander("🛠️ Admin"):
    if st.button("Undo Last"):
        if len(raw_data) > 0:
            try:
                worksheet.delete_rows(len(raw_data) + 1)
                st.toast("Last entry removed", icon="🗑️")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")
        else:
            st.warning("No entries to remove")
