import streamlit as st
import pandas as pd
import plotly.express as px
import gspread
import datetime

# --- 1. CONFIGURATION ---
APP_LOGO_URL = "https://i.postimg.cc/8Cr6SypK/yzwb-ll-sm.png"
BG_IMAGE_URL = "https://i.postimg.cc/GmFZ4KS7/Gemini-Generated-Image-k1h11zk1h11zk1h1.png"
SIDEBAR_BG_URL = "https://i.postimg.cc/NfdK3hck/'yzwb-ll'-sm-(1).png"

# Custom Arrow Images (Based on your previous uploads)
ARROW_OPEN_IMG = "https://i.postimg.cc/vHQy61dy/Gemini-Generated-Image-dl91ekdl91ekdl91.png"
ARROW_CLOSE_IMG = "https://i.postimg.cc/hvVG4Nxz/Gemini-Generated-Image-2tueuy2tueuy2tue.png"

st.set_page_config(
    page_title="Elite Football Tracker",
    layout="wide",
    page_icon=APP_LOGO_URL,
    initial_sidebar_state="expanded"
)

# --- 2. ADVANCED CSS (FIXES & MOBILE OPTIMIZATION) ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;600;900&family=Inter:wght@400;600&display=swap');
    
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    [data-testid="stDecoration"] {{display: none;}}
    header[data-testid="stHeader"] {{ background: transparent !important; }}
    
    /* Arrow Images Fix */
    [data-testid="stSidebarCollapsedControl"] {{
        background-color: rgba(0, 0, 0, 0.6) !important;
        border-radius: 12px !important;
        width: 45px !important; height: 45px !important;
        background-image: url('{ARROW_OPEN_IMG}') !important;
        background-size: 24px !important;
        background-repeat: no-repeat !important;
        background-position: center !important;
        color: transparent !important; font-size: 0px !important;
    }}
    [data-testid="stSidebarCollapsedControl"] svg {{ display: none !important; }}

    button[aria-label="Collapse sidebar"] {{
        background-image: url('{ARROW_CLOSE_IMG}') !important;
        background-size: 24px !important;
        background-repeat: no-repeat !important;
        background-position: center !important;
        color: transparent !important; font-size: 0px !important;
    }}
    button[aria-label="Collapse sidebar"] svg {{ display: none !important; }}
    [data-testid="stTooltipContent"], .stTooltipIcon {{ display: none !important; }}

    /* Backgrounds */
    [data-testid="stAppViewContainer"] {{
        background-image: linear-gradient(rgba(0, 0, 0, 0.75), rgba(0, 0, 0, 0.75)), url("{BG_IMAGE_URL}");
        background-attachment: fixed; background-size: cover; background-position: center;
    }}

    /* Sidebar (Force Black Text) */
    [data-testid="stSidebar"] {{
        background-color: rgba(255, 255, 255, 0.95) !important;
    }}
    [data-testid="stSidebar"]::before {{
        content: ""; position: absolute; top: 0; left: 0; width: 100%; height: 100%;
        background-image: url("{SIDEBAR_BG_URL}"); background-size: cover;
        filter: blur(4px); z-index: -1;
    }}
    [data-testid="stSidebar"] *, [data-testid="stSidebar"] p, [data-testid="stSidebar"] label {{
        color: #000000 !important;
        text-shadow: none !important;
        font-weight: 600 !important;
    }}
    [data-testid="stSidebar"] input {{ background-color: white !important; color: black !important; }}

    /* Main Typography */
    .main h1, .main h2, .main h3, .main p, .main span, .main label {{
        color: #ffffff !important;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.8);
        font-family: 'Montserrat', sans-serif;
    }}

    /* Component Styling */
    .custom-metric-box {{
        background-color: rgba(255, 255, 255, 0.95);
        border-radius: 12px; padding: 18px; text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3); margin-bottom: 10px;
    }}
    .metric-card-label {{ color: #555 !important; font-weight: 700; font-size: 11px; text-transform: uppercase; text-shadow: none !important; }}
    .metric-card-value {{ color: #1b4332 !important; font-weight: 900; font-size: 24px; text-shadow: none !important; }}

    [data-testid="stForm"] {{ background-color: rgba(255, 255, 255, 0.95); border-radius: 15px; padding: 20px; }}
    [data-testid="stForm"] * {{ color: black !important; text-shadow: none !important; }}

    /* Activity Banners (50% Opacity) */
    .activity-banner {{
        padding: 15px 25px; border-radius: 12px; margin-bottom: 12px;
        display: flex; justify-content: space-between; align-items: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.4); border-left: 10px solid;
    }}
    .banner-won {{ background-color: rgba(46, 204, 113, 0.5) !important; border-color: #28a745; }}
    .banner-lost {{ background-color: rgba(231, 76, 60, 0.5) !important; border-color: #dc3545; }}
    .banner-pending {{ background-color: rgba(255, 193, 7, 0.5) !important; border-color: #ffc107; }}
    
    .banner-main-text {{ font-size: 1.1rem; font-weight: 900; color: white !important; }}
    .banner-sub-text {{ font-size: 0.85rem; opacity: 0.9; color: white !important; }}
    .banner-profit-text {{ font-size: 1.4rem; font-weight: 900; color: white !important; }}

    /* Competition Banner (Responsive) */
    .comp-banner {{
        border-radius: 15px; padding: 25px; display: flex; align-items: center; 
        justify-content: center; margin-bottom: 30px; box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    }}
    .comp-logo {{ height: 80px; }}
    .comp-title {{ font-size: 2rem; font-weight: 900; margin-left: 20px; text-transform: uppercase; }}

    @media only screen and (max-width: 768px) {{
        .comp-title {{ display: none !important; }}
        .comp-logo {{ height: 70px; }}
        .activity-banner {{ flex-direction: column; text-align: center; gap: 10px; }}
        h1 {{ font-size: 1.6rem !important; }}
        [data-testid="column"] {{ width: 100% !important; flex: 1 1 100% !important; }}
    }}
    </style>
""", unsafe_allow_html=True)

# --- 3. DATA & LOGIC ENGINE (BACKEND) ---
@st.cache_data(ttl=15)
def get_full_sync():
    try:
        gc = gspread.service_account_from_dict(st.secrets["service_account"])
        sh = gc.open_by_url(st.secrets["sheet_url"])
        
        # Matches Sheet
        ws_matches = sh.get_worksheet(0)
        matches_data = ws_matches.get_all_records()
        
        # Competitions Sheet (Sheet 1)
        ws_comps = sh.get_worksheet(1)
        comps_data = ws_comps.get_all_records()
        
        # Bankroll
        try:
            val = ws_matches.cell(1, 10).value
            base_br = float(str(val).replace(',', '')) if val else 5000.0
        except: base_br = 5000.0
        
        return matches_data, comps_data, ws_matches, ws_comps, base_br
    except Exception as e:
        st.error(f"Sync Error: {e}")
        return [], [], None, None, 5000.0

def process_logic(matches, comps_meta, base_br):
    if not matches: return pd.DataFrame(), {}
    
    # Prepare defaults from metadata
    comp_defaults = {c['Name']: float(c['InitialBet']) for c in comps_meta}
    
    processed = []
    cycle_invest = {c['Name']: 0.0 for c in comps_meta}
    current_stakes = {c['Name']: float(c['InitialBet']) for c in comps_meta}

    for idx, row in enumerate(matches):
        try:
            comp = str(row.get('Competition', '')).strip()
            if comp not in cycle_invest: 
                cycle_invest[comp] = 0.0
                current_stakes[comp] = 30.0 # Fallback
            
            odds = float(str(row.get('Odds', 1)).replace(',', '.'))
            stake_input = row.get('Stake')
            exp = float(stake_input) if stake_input and str(stake_input).strip() else current_stakes[comp]
            res = str(row.get('Result', '')).strip()
            
            if res == "Pending":
                processed.append({
                    "Row": idx + 2, "Date": row.get('Date',''), "Comp": comp,
                    "Match": f"{row.get('Home Team','')} vs {row.get('Away Team','')}",
                    "Odds": odds, "Expense": 0.0, "Income": 0.0, "Net": 0.0, "Status": "⏳ Pending"
                })
                continue
            
            cycle_invest[comp] += exp
            is_win = "Draw (X)" in res
            
            if is_win:
                inc = exp * odds
                net = inc - cycle_invest[comp] # Cycle Recovery Logic
                current_stakes[comp] = comp_defaults.get(comp, 30.0)
                cycle_invest[comp] = 0.0
                status = "✅ Won"
            else:
                inc = 0.0
                net = -exp
                current_stakes[comp] = exp * 2.0 # Martingale
                status = "❌ Lost"
            
            processed.append({
                "Row": idx + 2, "Date": row.get('Date',''), "Comp": comp,
                "Match": f"{row.get('Home Team','')} vs {row.get('Away Team','')}",
                "Odds": odds, "Expense": exp, "Income": inc, "Net": net, "Status": status
            })
        except: continue
        
    return pd.DataFrame(processed), current_stakes

# --- 4. EXECUTION ---
m_raw, c_raw, ws_matches, ws_comps, initial_br = get_full_sync()
df, next_stakes = process_logic(m_raw, c_raw, initial_br)

current_bal = initial_br + (df['Income'].sum() - df['Expense'].sum()) if not df.empty else initial_br

# --- 5. SIDEBAR & DIALOGS ---

@st.dialog("➕ Create New Competition")
def create_comp_dialog():
    st.write("Set up your next betting track")
    name = st.text_input("Competition Name")
    init_bet = st.number_input("Starting Stake (₪)", value=30, min_value=10)
    logo = st.text_input("Logo URL (Optional)")
    c1, c2 = st.columns(2)
    p_color = c1.color_picker("Primary Color", "#1b4332")
    s_color = c2.color_picker("Secondary Color", "#40916c")
    
    if st.button("Launch Competition", use_container_width=True):
        if name and ws_comps:
            ws_comps.append_row([name, "Active", init_bet, logo, p_color, s_color])
            get_full_sync.clear()
            st.rerun()

with st.sidebar:
    st.image(APP_LOGO_URL, use_container_width=True)
    st.markdown("## WALLET CONTROL")
    st.metric("Base Bankroll", f"₪{initial_br:,.0f}")
    
    amt = st.number_input("Amount", min_value=0.0, value=100.0, step=50.0, label_visibility="collapsed")
    col1, col2 = st.columns(2)
    if col1.button("Deposit", use_container_width=True):
        ws_matches.update_cell(1, 10, initial_br + amt); get_full_sync.clear(); st.rerun()
    if col2.button("Withdraw", use_container_width=True):
        ws_matches.update_cell(1, 10, initial_br - amt); get_full_sync.clear(); st.rerun()
    
    st.divider()
    if st.button("➕ New Competition", use_container_width=True):
        create_comp_dialog()
    
    st.divider()
    # Dynamic Navigation
    active_names = [c['Name'] for c in c_raw if c['Status'] == 'Active']
    track = st.selectbox("Navigate", ["📊 Overview", "📚 Competition History"] + active_names, label_visibility="collapsed")
    
    if st.button("🔄 Sync Cloud", use_container_width=True):
        get_full_sync.clear(); st.rerun()

# --- 6. MAIN VIEWS ---

if track == "📊 Overview":
    st.markdown(f"""
        <div class="comp-banner" style="background: linear-gradient(90deg, #1b4332, #40916c);">
            <img src="{APP_LOGO_URL}" class="comp-logo">
            <span class="comp-title">Global Overview</span>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"<div style='text-align:center'><div style='font-size:2.5rem; font-weight:900'>₪{current_bal:,.2f}</div><p style='letter-spacing:2px; opacity:0.7'>LIVE BANKROLL</p></div>", unsafe_allow_html=True)
    
    if not df.empty:
        summary = df.groupby('Comp').agg({'Match': 'count', 'Expense': 'sum', 'Income': 'sum', 'Status': lambda x: (x == '✅ Won').sum()}).reset_index()
        summary['Profit'] = summary['Income'] - summary['Expense']
        
        # Merge with status to show ARCHIVED
        c_status = {c['Name']: c['Status'] for c in c_raw}
        summary['State'] = summary['Comp'].map(c_status)
        
        col1, col2, col3 = st.columns(3)
        with col1: st.markdown(f'<div class="custom-metric-box"><div class="metric-card-label">Total Profit</div><div class="metric-card-value">₪{summary["Profit"].sum():,.0f}</div></div>', unsafe_allow_html=True)
        with col2: st.markdown(f'<div class="custom-metric-box"><div class="metric-card-label">Total Games</div><div class="metric-card-value">{summary["Match"].sum()}</div></div>', unsafe_allow_html=True)
        with col3: 
            rate = (summary['Status'].sum()/summary['Match'].sum()*100) if summary['Match'].sum() > 0 else 0
            st.markdown(f'<div class="custom-metric-card"><div class="metric-card-label">Global Health</div><div class="metric-card-value">{rate:.1f}%</div></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        # Table of competitions
        display_df = summary.copy()
        display_df['Track'] = display_df.apply(lambda x: f"{x['Comp']} [ARCHIVED]" if x['State'] == 'Archived' else x['Comp'], axis=1)
        st.dataframe(display_df[['Track', 'Match', 'Status', 'Profit']].rename(columns={'Status': 'Wins'}), use_container_width=True, hide_index=True)

elif track == "📚 Competition History":
    st.markdown("<h1 style='text-align:center'>📚 Competition History</h1>", unsafe_allow_html=True)
    archived_comps = [c for c in c_raw if c['Status'] == 'Archived']
    
    if not archived_comps:
        st.info("No competitions archived yet.")
    else:
        for c in archived_comps:
            comp_df = df[df['Comp'] == c['Name']]
            p = comp_df['Income'].sum() - comp_df['Expense'].sum() if not comp_df.empty else 0
            
            st.markdown(f"""
                <div style="background: rgba(255,255,255,0.1); border-radius:15px; padding:20px; margin-bottom:20px; border-left: 5px solid #555;">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <div style="display:flex; align-items:center;">
                            <img src="{c['LogoURL'] if c['LogoURL'] else APP_LOGO_URL}" style="height:50px; margin-right:15px;">
                            <span style="font-size:1.5rem; font-weight:900;">{c['Name']}</span>
                        </div>
                        <div style="text-align:right;">
                            <div style="font-size:0.8rem; opacity:0.7;">TOTAL PROFIT</div>
                            <div style="font-size:1.8rem; font-weight:900; color:{'#00ff88' if p>=0 else '#ff4b4b'}">₪{p:,.0f}</div>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            # Export Option
            if st.button(f"📥 Export {c['Name']} to CSV", key=f"dl_{c['Name']}"):
                st.download_button("Click to Download", comp_df.to_csv().encode('utf-8'), f"{c['Name']}.csv", "text/csv")

else:
    # SPECIFIC ACTIVE COMPETITION VIEW
    meta = next(c for c in c_raw if c['Name'] == track)
    grad = f"linear-gradient(90deg, {meta['PrimaryColor']}, {meta['SecondaryColor']})"
    logo = meta['LogoURL'] if meta['LogoURL'] else APP_LOGO_URL
    
    st.markdown(f"""
        <div class="comp-banner" style="background: {grad};">
            <img src="{logo}" class="comp-logo">
            <span class="comp-title" style="color: white;">{track}</span>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"<div style='text-align:center'><div style='font-size:2.5rem; font-weight:900'>₪{current_bal:,.2f}</div><p style='letter-spacing:2px; opacity:0.7'>LIVE BANKROLL</p></div>", unsafe_allow_html=True)

    f_df = df[df['Comp'] == track].copy() if not df.empty else pd.DataFrame()
    m_exp, m_inc = (f_df['Expense'].sum(), f_df['Income'].sum()) if not f_df.empty else (0.0, 0.0)
    
    c1, c2, c3 = st.columns(3)
    with c1: st.markdown(f'<div class="custom-metric-box"><div class="metric-card-label">Invested</div><div class="metric-card-value">₪{m_exp:,.0f}</div></div>', unsafe_allow_html=True)
    with c2: st.markdown(f'<div class="custom-metric-box"><div class="metric-card-label">Revenue</div><div class="metric-card-value">₪{m_inc:,.0f}</div></div>', unsafe_allow_html=True)
    with c3: st.markdown(f'<div class="custom-metric-box"><div class="metric-card-label">Net Profit</div><div class="metric-card-value">₪{m_inc-m_exp:,.0f}</div></div>', unsafe_allow_html=True)

    st.markdown(f"<div style='text-align:center; margin:20px'><b>Next Bet:</b> <span style='color:#00ff88; font-size:1.5rem'>₪{next_stakes.get(track, 30.0):,.0f}</span></div>", unsafe_allow_html=True)

    col_f, col_g = st.columns([1, 1.2])
    with col_f:
        with st.form("new_match"):
            st.subheader("Add Match")
            h = st.text_input("Home Team")
            a = st.text_input("Away Team")
            o = st.number_input("Odds", value=3.2)
            s = st.number_input("Stake", value=float(next_stakes.get(track, 30.0)))
            r = st.radio("Result", ["Pending", "Draw (X)", "No Draw"], horizontal=True)
            if st.form_submit_button("SUBMIT GAME", use_container_width=True):
                ws_matches.append_row([str(datetime.date.today()), track, h, a, o, r, s, 0.0])
                get_full_sync.clear(); st.rerun()

    with col_g:
        if not f_df.empty:
            f_df['Equity'] = initial_br + (f_df['Income'].cumsum() - f_df['Expense'].cumsum())
            fig_l = px.line(f_df, y='Equity', x=f_df.index)
            fig_l.update_traces(line_color='#00ff88', line_width=4)
            fig_l.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0.1)', font=dict(color='white'), height=240, margin=dict(l=0,r=0,t=10,b=0))
            st.plotly_chart(fig_l, use_container_width=True)

    # CLOSE COMPETITION
    if st.button("🏁 Close Competition & Archive", use_container_width=True):
        # Update status in Sheet 1
        cell = ws_comps.find(track)
        ws_comps.update_cell(cell.row, 2, "Archived")
        st.balloons()
        st.success(f"Competition '{track}' archived! Final Profit: ₪{m_inc-m_exp:,.0f}")
        get_full_sync.clear(); st.rerun()

    st.markdown("### 📜 Activity Log")
    if not f_df.empty:
        for _, match in f_df.sort_index(ascending=False).iterrows():
            status = str(match['Status'])
            b_class = "banner-won" if "Won" in status else "banner-lost" if "Lost" in status else "banner-pending"
            
            st.markdown(f"""
                <div class="activity-banner {b_class}">
                    <div>
                        <div class="banner-main-text">{match['Match']}</div>
                        <div class="banner-sub-text">{match['Date']} | Odds: {match['Odds']:.2f}</div>
                        <div class="banner-sub-text">Stake: ₪{match['Expense']:,.0f} | Gross: ₪{match['Income']:,.0f}</div>
                    </div>
                    <div style="text-align:right">
                        <div class="banner-sub-text">{"Cycle Profit" if "Won" in status else "Loss"}</div>
                        <div class="banner-profit-text">₪{match['Net']:,.0f}</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

with st.expander("🛠️ Admin Tools"):
    if st.button("Undo Last Entry"):
        ws_matches.delete_rows(len(m_raw) + 1)
        get_full_sync.clear(); st.rerun()