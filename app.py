import streamlit as st
import pandas as pd
import plotly.express as px
import gspread
import datetime

# --- 1. CONFIGURATION ---
APP_LOGO_URL = "https://i.postimg.cc/8Cr6SypK/yzwb-ll-sm.png"
BG_IMAGE_URL = "https://i.postimg.cc/GmFZ4KS7/Gemini-Generated-Image-k1h11zk1h11zk1h1.png"
SIDEBAR_BG_IMAGE_URL = "https://i.postimg.cc/NfdK3hck/'yzwb-ll'-sm-(1).png"

st.set_page_config(
    page_title="Elite Football Tracker",
    layout="wide",
    page_icon=APP_LOGO_URL,
    initial_sidebar_state="expanded"
)

# --- 2. CSS STYLING (THE FINAL & COMPLETE VERSION) ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;600;900&family=Inter:wght@400;600&display=swap');
    
    /* --- RESET & CLEANUP --- */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    [data-testid="stDecoration"] {{display: none;}}
    
    /* Header Container - Make Transparent */
    header[data-testid="stHeader"] {{
        background: transparent !important;
        backdrop-filter: none !important;
        z-index: 100 !important;
    }}

    /* ================================================================= */
    /* >>> ARROWS CONTRAST STRATEGY <<< */
    /* ================================================================= */

    /* 1. OPEN SIDEBAR BUTTON (Visible on Dark Stadium) */
    [data-testid="stSidebarCollapsedControl"] {{
        background-color: rgba(0, 0, 0, 0.4) !important;
        border-radius: 8px !important;
        padding: 2px !important;
        color: #ffffff !important;
        margin-top: 10px;
        margin-left: 10px;
        z-index: 10000 !important;
    }}
    [data-testid="stSidebarCollapsedControl"] svg,
    [data-testid="stSidebarCollapsedControl"] i {{
        fill: #ffffff !important;
        stroke: #ffffff !important;
        color: #ffffff !important;
    }}

    /* 2. CLOSE SIDEBAR BUTTON (Visible on Light Sidebar) */
    section[data-testid="stSidebar"] button[kind="header"] {{
        background-color: transparent !important;
        border: none !important;
        color: #000000 !important;
    }}
    section[data-testid="stSidebar"] button[kind="header"] svg,
    section[data-testid="stSidebar"] button[kind="header"] svg path {{
        fill: #000000 !important;
        stroke: #000000 !important;
        color: #000000 !important;
    }}

    /* ================================================================= */

    /* --- MAIN BACKGROUND --- */
    [data-testid="stAppViewContainer"] {{
        background-image: linear-gradient(rgba(0, 0, 0, 0.7), rgba(0, 0, 0, 0.7)), url("{BG_IMAGE_URL}");
        background-attachment: fixed;
        background-size: cover;
        background-position: center;
    }}

    /* --- SIDEBAR BACKGROUND --- */
    [data-testid="stSidebar"] {{
        position: relative;
        background-color: rgba(255, 255, 255, 0.8) !important;
        border-right: 1px solid rgba(255,255,255,0.2);
    }}

    [data-testid="stSidebar"]::before {{
        content: "";
        position: absolute;
        top: 0; left: 0; width: 100%; height: 100%;
        background-image: url("{SIDEBAR_BG_IMAGE_URL}");
        background-size: cover;
        background-position: center;
        filter: blur(5px); 
        z-index: -1;
        transform: scale(1.05);
    }}

    /* --- SIDEBAR CONTENT --- */
    [data-testid="stSidebar"] *, 
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] div,
    [data-testid="stSidebar"] label, [data-testid="stSidebar"] .stMarkdown,
    [data-testid="stSidebar"] [data-testid="stMetricValue"] {{
        color: #000000 !important;
        text-shadow: none !important;
        font-family: 'Montserrat', sans-serif;
    }}
    
    /* Sidebar Inputs */
    [data-testid="stSidebar"] input {{
        color: #000000 !important;
        background-color: rgba(255, 255, 255, 0.9) !important;
        border: 1px solid #ccc;
    }}
    
    /* Action Buttons */
    [data-testid="stSidebar"] [data-testid="stButton"] button {{
        color: #ffffff !important;
        background-color: #2E7D32 !important;
        border: none;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
    }}

    /* --- MAIN AREA TEXT --- */
    .main h1, .main h2, .main h3, .main h4, .main p {{
        color: #ffffff !important;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.8);
    }}

    /* --- COMPONENTS --- */
    [data-testid="stDataFrame"] {{ background-color: white !important; border-radius: 8px; }}
    [data-testid="stDataFrame"] * {{ color: #000000 !important; text-shadow: none !important; }}

    [data-testid="stForm"] {{ background-color: rgba(255, 255, 255, 0.95); border-radius: 15px; padding: 25px; }}
    [data-testid="stForm"] * {{ color: #000000 !important; text-shadow: none !important; }}

    .custom-metric-box {{
        background-color: rgba(255, 255, 255, 0.95);
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }}
    .metric-card-label {{ color: #555 !important; font-weight: 700; font-size: 13px; text-shadow: none !important; }}
    .metric-card-value {{ color: #1b4332 !important; font-weight: 900; font-size: 26px; text-shadow: none !important; }}

    /* --- MOBILE RESPONSIVE --- */
    @media only screen and (max-width: 768px) {{
        .banner-text {{ display: none !important; }}
        .banner-container {{ justify-content: center !important; padding: 10px !important; }}
        .banner-img {{ height: 120px !important; margin: 0 !important; filter: drop-shadow(0 0 10px rgba(255,255,255,0.3)) !important; }}
        [data-testid="stDataFrame"] * {{ font-size: 12px !important; }}
        
        [data-testid="stSidebarCollapsedControl"] {{
            margin-top: 5px;
            margin-left: 5px;
        }}
    }}
    </style>
""", unsafe_allow_html=True)

# --- 3. BACKEND LOGIC ---
def get_data_from_sheets():
    try:
        gc = gspread.service_account_from_dict(st.secrets["service_account"])
        sh = gc.open_by_url(st.secrets["sheet_url"])
        worksheet = sh.get_worksheet(0)
        data = worksheet.get_all_records()
        try:
            val = worksheet.cell(1, 10).value
            initial_bankroll = float(str(val).replace(',', '')) if val else 5000.0
        except: initial_bankroll = 5000.0
        return data, worksheet, initial_bankroll
    except Exception as e:
        st.error(f"Connection Error: {e}")
        return [], None, 5000.0

def update_bankroll(worksheet, val):
    try:
        worksheet.update_cell(1, 10, val)
        return True
    except: return False

def calculate_logic(raw_data, br_base, af_base):
    processed = []
    # Initialize defaults
    next_bets = {"Brighton": float(br_base), "Africa Cup of Nations": float(af_base)}
    cycle_invest = {"Brighton": 0.0, "Africa Cup of Nations": 0.0}

    for row in raw_data:
        try:
            comp = str(row.get('Competition', 'Brighton')).strip()
            if not comp: comp = 'Brighton'
            
            # Dynamic init if new track appears
            if comp not in next_bets:
                next_bets[comp] = 30.0 
                cycle_invest[comp] = 0.0

            try: odds = float(str(row.get('Odds', 1)).replace(',', '.'))
            except: odds = 1.0
            try:
                stake_val = row.get('Stake')
                if stake_val in [None, '', ' ']: exp = next_bets[comp]
                else: exp = float(str(stake_val).replace(',', ''))
            except: exp = next_bets[comp]
            
            res = str(row.get('Result', '')).strip()
            cycle_invest[comp] += exp
            is_win = "Draw (X)" in res
            
            if is_win:
                inc = exp * odds
                net = inc - cycle_invest[comp]
                try: roi = f"{(net / cycle_invest[comp]) * 100:.1f}%"
                except: roi = "0.0%"
                # Reset Logic
                base_reset = float(br_base if "Brighton" in comp else (af_base if "Africa" in comp else 30.0))
                next_bets[comp] = base_reset
                cycle_invest[comp] = 0.0
                status = "✅ Won"
            else:
                inc = 0.0
                net = -exp
                roi = "N/A"
                next_bets[comp] = exp * 2.0
                status = "❌ Lost"
            
            processed.append({
                "Date": row.get('Date', ''), "Comp": comp, "Match": f"{row.get('Home Team','')} vs {row.get('Away Team','')}",
                "Odds": odds, "Expense": exp, "Income": inc, "Net Profit": net, "Status": status, "ROI": roi
            })
        except: continue
    return processed, next_bets

# --- 4. EXECUTION ---
raw_data, worksheet, saved_br = get_data_from_sheets()
processed, next_stakes = calculate_logic(raw_data, 30.0, 20.0)

if processed:
    df = pd.DataFrame(processed)
    # Calculate global balance change from Income - Expense (Fail-safe way)
    current_bal = saved_br + (df['Income'].sum() - df['Expense'].sum())
else:
    df = pd.DataFrame(columns=["Comp", "Income", "Expense", "Net Profit", "Status"])
    current_bal = saved_br

# --- 5. UI LAYOUT ---

# SIDEBAR
with st.sidebar:
    try: st.image(APP_LOGO_URL, width=120)
    except: pass
    
    st.markdown("## WALLET CONTROL")
    st.metric("Base Bankroll", f"₪{saved_br:,.0f}")
    
    st.write("Transaction Amount:")
    amt = st.number_input("Amount", min_value=0.0, value=100.0, step=50.0, label_visibility="collapsed")
    
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Deposit", use_container_width=True):
            if update_bankroll(worksheet, saved_br + amt): st.rerun()
    with c2:
        if st.button("Withdraw", use_container_width=True):
            if update_bankroll(worksheet, saved_br - amt): st.rerun()
            
    st.divider()
    st.write("Navigation:")
    track = st.selectbox("View", ["🏆 Overview", "Brighton", "Africa Cup of Nations"], label_visibility="collapsed")
    
    if st.button("🔄 Sync Cloud", use_container_width=True): st.rerun()

# --- LOGIC SWITCH: OVERVIEW vs SPECIFIC TRACK ---

if track == "🏆 Overview":
    # --- DASHBOARD VIEW ---
    st.markdown("""
        <div style="text-align: center; margin-bottom: 20px;">
            <h1 style="font-size: 3rem; font-weight: 900; text-transform: uppercase; letter-spacing: 2px;">
                CENTRAL COMMAND
            </h1>
            <p style="font-size: 1.2rem; color: #ccc;">Cross-Competition Analytics</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
    <div style="text-align: center; margin-bottom: 35px;">
        <div style="font-size: 2.3rem; font-weight: 300; color: #ffffff; text-shadow: 0 0 20px rgba(255,255,255,0.3); line-height: 1; margin-bottom: 8px;">
            ₪{current_bal:,.2f}
        </div>
        <div style="font-size: 0.8rem; font-weight: 600; color: #cccccc; letter-spacing: 3px; text-transform: uppercase;">
            TOTAL BANKROLL
        </div>
    </div>
    """, unsafe_allow_html=True)

    if not df.empty:
        # --- THE CORRECT CALCULATION LOGIC ---
        # 1. Group by Competition
        # 2. Sum Income and Expense separately
        # 3. Derive Net Profit from (Income - Expense), NOT from summing 'Net Profit' column
        summary = df.groupby('Comp').agg({
            'Match': 'count',
            'Expense': 'sum',
            'Income': 'sum',
            'Status': lambda x: (x == '✅ Won').sum()
        }).reset_index()
        
        summary.columns = ['Competition', 'Games', 'Expenses', 'Revenue', 'Wins']
        
        # Calculate Net Profit Correctly Here:
        summary['Net Profit'] = summary['Revenue'] - summary['Expenses']
        
        # Calculate Win Rate
        summary['Win Rate'] = (summary['Wins'] / summary['Games'] * 100).apply(lambda x: f"{x:.1f}%")
        
        # 4. Global Metrics
        total_profit = summary['Net Profit'].sum()
        total_games = summary['Games'].sum()
        total_wins = summary['Wins'].sum()
        global_win_rate = (total_wins / total_games * 100) if total_games > 0 else 0
        
        # Display Cards
        c1, c2, c3 = st.columns(3)
        
        # Color Logic for Total Profit (Fail-safe syntax)
        if total_profit >= 0:
            color_total = "#2d6a4f"
        else:
            color_total = "#d32f2f"

        with c1: 
            st.markdown(f"""<div class="custom-metric-box"><div class="metric-card-label">ALL TIME PROFIT</div><div class="metric-card-value" style="color: {color_total} !important;">₪{total_profit:,.0f}</div></div>""", unsafe_allow_html=True)
        with c2: 
            st.markdown(f"""<div class="custom-metric-box"><div class="metric-card-label">TOTAL GAMES</div><div class="metric-card-value">{total_games}</div></div>""", unsafe_allow_html=True)
        with c3: 
            st.markdown(f"""<div class="custom-metric-box"><div class="metric-card-label">GLOBAL WIN RATE</div><div class="metric-card-value">{global_win_rate:.1f}%</div></div>""", unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)

        # 5. Competition Comparison Chart
        c_chart, c_table = st.columns([1, 1])
        
        with c_chart:
            st.subheader("Profit Distribution")
            fig = px.bar(summary, x='Competition', y='Net Profit', color='Net Profit',
                         color_continuous_scale=['#d32f2f', '#2d6a4f'], text_auto='.2s')
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0.2)',
                font=dict(color='white'), showlegend=False,
                height=350,
                xaxis_title=None, yaxis_title=None
            )
            st.plotly_chart(fig, use_container_width=True)

        with c_table:
            st.subheader("Performance Breakdown")
            
            # Prepare display table
            display_summary = summary[['Competition', 'Games', 'Wins', 'Win Rate', 'Revenue', 'Net Profit']].copy()
            
            # Styling
            def style_summary(row):
                return ['color: #000000; font-weight: 500;'] * len(row)

            st.dataframe(
                display_summary.style.apply(style_summary, axis=1).format({
                    "Revenue": "₪{:,.0f}", 
                    "Net Profit": "₪{:,.0f}"
                }),
                use_container_width=True,
                hide_index=True
            )

    else:
        st.info("No data available yet.")

else:
    # --- SPECIFIC TRACK VIEW (Existing & Correct Logic) ---
    brighton_logo = "https://i.postimg.cc/x8kdQh5H/Brighton_Hove_Albion_logo.png"
    afcon_logo = "https://i.postimg.cc/5yHtJTgz/2025_Africa_Cup_of_Nations_logo.png"

    if track == "Brighton":
        banner_bg = "linear-gradient(90deg, #4CABFF 0%, #E6F7FF 50%, #4CABFF 100%)"
        text_color = "#004085"
        logo_src = brighton_logo
        shadow_style = "none"
    else:
        banner_bg = "linear-gradient(90deg, #CE1126 0%, #FCD116 50%, #007A33 100%)"
        text_color = "#FFFFFF"
        logo_src = afcon_logo
        shadow_style = "2px 2px 4px #000000"

    st.markdown(f"""
        <div class="banner-container" style="
            background: {banner_bg};
            border-radius: 15px;
            padding: 20px;
            display: flex;
            align-items: center;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.5);
            border: 2px solid rgba(255,255,255,0.4);
        ">
            <img class="banner-img" src="{logo_src}" style="height: 70px; margin-right: 25px; filter: drop-shadow(0 4px 6px rgba(0,0,0,0.3)); transition: all 0.3s;">
            <h1 class="banner-text" style="
                margin: 0;
                font-size: 2.2rem;
                font-weight: 900;
                text-transform: uppercase;
                color: {text_color} !important;
                text-shadow: {shadow_style};
                font-family: 'Montserrat', sans-serif;
                letter-spacing: 2px;
                flex: 1;
                text-align: left;
            ">{track.upper()}</h1>
        </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
        <div style="text-align: center; margin-bottom: 35px;">
            <div style="font-size: 2.3rem; font-weight: 300; color: #ffffff; text-shadow: 0 0 20px rgba(255,255,255,0.3); line-height: 1; margin-bottom: 8px;">
                ₪{current_bal:,.2f}
            </div>
            <div style="font-size: 0.8rem; font-weight: 600; color: #cccccc; letter-spacing: 3px; text-transform: uppercase;">
                LIVE BANKROLL
            </div>
        </div>
    """, unsafe_allow_html=True)

    if not df.empty:
        f_df = df[df['Comp'] == track].copy()
    else:
        f_df = pd.DataFrame()
        
    if not f_df.empty:
        m_exp = f_df['Expense'].sum(); m_inc = f_df['Income'].sum(); m_net = m_inc - m_exp
    else: m_exp = 0.0; m_inc = 0.0; m_net = 0.0

    c1, c2,