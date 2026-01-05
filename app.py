import streamlit as st
import pandas as pd
import gspread
import datetime
import plotly.express as px

# --- 1. CONFIGURATION ---
APP_LOGO_URL = "https://i.postimg.cc/8Cr6SypK/yzwb-ll-sm.png"
BG_IMAGE_URL = "https://i.postimg.cc/GmFZ4KS7/Gemini-Generated-Image-k1h11zk1h11zk1h1.png"

st.set_page_config(
    page_title="Elite Football Tracker",
    layout="wide",
    page_icon=APP_LOGO_URL,
    initial_sidebar_state="expanded"
)

# --- 2. CSS STYLING ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;600;900&display=swap');
    #MainMenu {{visibility: hidden;}} footer {{visibility: hidden;}}
    [data-testid="stSidebarNav"] {{display: none;}}
    [data-testid="stAppViewContainer"] {{
        background-image: linear-gradient(rgba(0,0,0,0.7), rgba(0,0,0,0.7)), url("{BG_IMAGE_URL}");
        background-attachment: fixed; background-size: cover;
    }}
    [data-testid="stSidebar"] {{ background-color: #f8f9fa; border-right: 1px solid #ddd; }}
    .comp-banner-box {{
        border-radius: 15px; padding: 20px; display: flex; align-items: center; 
        justify-content: center; margin-bottom: 30px; box-shadow: 0 10px 30px rgba(0,0,0,0.5);
        border: 2px solid rgba(255,255,255,0.4); width: 100%;
    }}
    .comp-banner-logo {{ height: 70px; margin-right: 20px; }}
    .comp-banner-text {{ margin: 0; font-size: 2.5rem; font-weight: 900; text-transform: uppercase; color: white; }}
    
    @media only screen and (max-width: 768px) {{
        .comp-banner-text {{ display: none !important; }}
        .comp-banner-logo {{ margin-right: 0 !important; }}
    }}
    
    .activity-card {{
        background: rgba(255,255,255,0.9); border-radius: 12px; padding: 15px; margin-bottom: 10px;
        border-left: 5px solid #ccc; color: black;
    }}
    .won {{ border-left-color: #28a745; background: #d4edda; }}
    .lost {{ border-left-color: #dc3545; background: #f8d7da; }}
    .pending {{ border-left-color: #ffc107; background: #fff3cd; }}
    </style>
""", unsafe_allow_html=True)

# --- 3. CONNECTION ---
@st.cache_data(ttl=15)
def get_data():
    try:
        # בדיקה שהמפתחות קיימים ב-secrets
        if "service_account" not in st.secrets:
            return [], None, 5000.0, "Missing service_account in secrets"
        if "sheet_url" not in st.secrets:
            return [], None, 5000.0, "Missing sheet_url in secrets"

        gc = gspread.service_account_from_dict(st.secrets["service_account"])
        sh = gc.open_by_url(st.secrets["sheet_url"])
        ws = sh.get_worksheet(0)
        data = ws.get_all_records()
        
        try:
            base = float(str(ws.cell(1, 10).value).replace(',', ''))
        except:
            base = 5000.0
        
        return data, ws, base, None
    except Exception as e:
        return [], None, 5000.0, str(e)

raw_data, worksheet, bankroll, conn_error = get_data()

if conn_error:
    st.error(f"Connection Error Details: {conn_error}")

# --- 4. LOGIC ---
def process_data(data):
    if not data: return pd.DataFrame(), {"Brighton": 30.0, "Africa Cup of Nations": 30.0}
    processed = []
    cycles = {"Brighton": 0.0, "Africa Cup of Nations": 0.0}
    next_bets = {"Brighton": 30.0, "Africa Cup of Nations": 30.0}
    
    for i, row in enumerate(data):
        comp = str(row.get('Competition', 'Brighton')).strip() or 'Brighton'
        odds = float(str(row.get('Odds', 1)).replace(',', '.'))
        stake = float(str(row.get('Stake', 30)).replace(',', '.'))
        res = str(row.get('Result', '')).strip()
        
        if res == "Pending":
            processed.append({"Row": i+2, "Comp": comp, "Match": f"{row.get('Home Team')} vs {row.get('Away Team')}", "Date": row.get('Date'), "Profit": 0, "Status": "Pending", "Stake": stake, "Odds": odds})
            continue
            
        cycles[comp] = cycles.get(comp, 0.0) + stake
        if "Draw (X)" in res:
            net = (stake * odds) - cycles[comp]
            cycles[comp] = 0.0
            next_bets[comp] = 30.0
            status = "Won"
        else:
            net = -stake
            next_bets[comp] = stake * 2
            status = "Lost"
            
        processed.append({"Row": i+2, "Comp": comp, "Match": f"{row.get('Home Team')} vs {row.get('Away Team')}", "Date": row.get('Date'), "Profit": net, "Status": status, "Stake": stake, "Odds": odds})
        
    return pd.DataFrame(processed), next_bets

df, next_stakes = process_data(raw_data)
current_bal = bankroll + df['Profit'].sum() if not df.empty else bankroll

# --- 5. SIDEBAR ---
with st.sidebar:
    st.image(APP_LOGO_URL, use_container_width=True)
    st.metric("Base Bankroll", f"₪{bankroll:,.0f}")
    amt = st.number_input("Transaction Amount", 100.0, step=50.0)
    c1, c2 = st.columns(2)
    if c1.button("Deposit"):
        if worksheet: worksheet.update_cell(1, 10, bankroll + amt); st.rerun()
    if c2.button("Withdraw"):
        if worksheet: worksheet.update_cell(1, 10, bankroll - amt); st.rerun()
    st.divider()
    page = st.selectbox("Navigate", ["📊 Overview", "Brighton", "Africa Cup of Nations"])
    if st.button("🔄 Sync Cloud"):
        get_data.clear(); st.rerun()

# --- 6. PAGES ---
if page == "📊 Overview":
    st.markdown(f'<div class="comp-banner-box" style="background:#2ecc71;"><span class="comp-banner-text">Overview</span></div>', unsafe_allow_html=True)
    # כאן היה התיקון לשגיאת ה-Syntax (שורה אחת נקייה)
    st.markdown(f"<h1 style='text-align:center; color:white;'>₪{current_bal:,.2f}</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:#ccc;'>LIVE BANKROLL</p>", unsafe_allow_html=True)
    
    if not df.empty:
        stats = df.groupby('Comp')['Profit'].sum().reset_index()
        for _, row in stats.iterrows():
            st.markdown(f"<div class='activity-card'><b>{row['Comp']}</b>: ₪{row['Profit']:,.0f}</div>", unsafe_allow_html=True)

else:
    logo = "https://upload.wikimedia.org/wikipedia/en/f/fd/Brighton_&_Hove_Albion_FC_logo.svg" if page == "Brighton" else "https://upload.wikimedia.org/wikipedia/en/f/f9/2023_Africa_Cup_of_Nations_logo.png"
    bg = "linear-gradient(90deg, #4CABFF, #E6F7FF)" if page == "Brighton" else "linear-gradient(90deg, #007A33, #FCD116)"
    
    st.markdown(f'<div class="comp-banner-box" style="background:{bg};"><img src="{logo}" class="comp-banner-logo"><span class="comp-banner-text" style="color:black;">{page}</span></div>', unsafe_allow_html=True)
    
    nb = next_stakes.get(page, 30.0)
    st.info(f"Next Bet: ₪{nb:,.0f}")
    
    with st.form("add"):
        c1, c2 = st.columns(2)
        h, a = c1.text_input("Home"), c2.text_input("Away")
        c3, c4 = st.columns(2)
        o, s = c3.number_input("Odds", 3.2), c4.number_input("Stake", float(nb))
        if st.form_submit_button("Submit"):
            if worksheet: worksheet.append_row([str(datetime.date.today()), page, h, a, o, "Pending", s, 0]); get_data.clear(); st.rerun()

    st.subheader("Activity Log")
    if not df.empty:
        sub = df[df['Comp'] == page].sort_index(ascending=False)
        for _, r in sub.iterrows():
            st.markdown(f'<div class="activity-card {r["Status"].lower()}"><b>{r["Match"]}</b> | Profit: ₪{r["Profit"]:,.0f} ({r["Status"]})</div>', unsafe_allow_html=True)
            if r["Status"] == "Pending":
                col1, col2 = st.columns(2)
                if col1.button("✅ WON", key=f"w{r['Row']}"):
                    if worksheet: worksheet.update_cell(r['Row'], 6, "Draw (X)"); get_data.clear(); st.rerun()
                if col2.button("❌ LOST", key=f"l{r['Row']}"):
                    if worksheet: worksheet.update_cell(r['Row'], 6, "Loss"); get_data.clear(); st.rerun()