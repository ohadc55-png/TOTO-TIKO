import streamlit as st
import pandas as pd
import gspread
import datetime
import plotly.express as px

# --- 1. CONFIGURATION ---
APP_LOGO_URL = "https://i.postimg.cc/8Cr6SypK/yzwb-ll-sm.png"
BG_IMAGE_URL = "https://i.postimg.cc/GmFZ4KS7/Gemini-Generated-Image-k1h11zk1h11zk1h1.png"

st.set_page_config(page_title="Elite Football Tracker", layout="wide", page_icon=APP_LOGO_URL)

# --- 2. CSS STYLING ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;600;900&display=swap');
    [data-testid="stAppViewContainer"] {{
        background-image: linear-gradient(rgba(0,0,0,0.7), rgba(0,0,0,0.7)), url("{BG_IMAGE_URL}");
        background-attachment: fixed; background-size: cover;
    }}
    .metric-box {{
        background: rgba(255, 255, 255, 0.9); border-radius: 10px; padding: 15px; 
        text-align: center; box-shadow: 0 2px 5px rgba(0,0,0,0.2); margin-bottom: 10px;
    }}
    .metric-label {{ font-size: 0.8rem; color: #555; font-weight: bold; text-transform: uppercase; }}
    .metric-value {{ font-size: 1.4rem; font-weight: 900; color: #000; }}
    .activity-card {{
        background: rgba(255,255,255,0.95); border-radius: 12px; padding: 15px; margin-bottom: 10px;
        border-left: 6px solid #ccc; color: black !important;
    }}
    .activity-card-won {{ border-left-color: #28a745 !important; }}
    .activity-card-lost {{ border-left-color: #dc3545 !important; }}
    .activity-card-pending {{ border-left-color: #ffc107 !important; }}
    .comp-banner-box {{
        border-radius: 15px; padding: 20px; display: flex; align-items: center; 
        justify-content: center; margin-bottom: 30px; box-shadow: 0 10px 30px rgba(0,0,0,0.5);
        border: 2px solid rgba(255,255,255,0.4); width: 100%;
    }}
    </style>
""", unsafe_allow_html=True)

# --- 3. SMART CONNECTION MANAGER ---
def find_sheet_identifier():
    """פונקציה חכמה שמחפשת את הלינק או ה-ID בכל מקום אפשרי בסיקרטס"""
    # 1. חיפוש ישיר בראשי
    if "sheet_url" in st.secrets: return st.secrets["sheet_url"]
    if "sheet_id" in st.secrets: return st.secrets["sheet_id"]
    
    # 2. חיפוש בתוך הבלוק של service_account (למקרה שהסדר התבלבל)
    if "service_account" in st.secrets:
        if "sheet_url" in st.secrets["service_account"]: return st.secrets["service_account"]["sheet_url"]
        if "sheet_id" in st.secrets["service_account"]: return st.secrets["service_account"]["sheet_id"]
    
    return None

@st.cache_data(ttl=15)
def connect_to_sheets():
    try:
        if "service_account" not in st.secrets:
            return None, None, 5000.0, "Critical: [service_account] section is completely missing from Secrets."
            
        # שימוש בפונקציית החיפוש החכמה
        sheet_target = find_sheet_identifier()
        
        if not sheet_target:
            return None, None, 5000.0, "Could not find 'sheet_url' or 'sheet_id' in Secrets (checked all locations)."

        # התחברות לחשבון
        gc = gspread.service_account_from_dict(st.secrets["service_account"])
        
        # ניסיון פתיחה חכם (עובד גם עם לינק וגם עם ID)
        try:
            if "docs.google.com" in sheet_target:
                sh = gc.open_by_url(sheet_target)
            else:
                sh = gc.open_by_key(sheet_target)
        except Exception as e:
            return None, None, 5000.0, f"Google rejected the connection. Did you share the sheet with the bot email? Error: {e}"

        worksheet = sh.get_worksheet(0)
        
        # קריאת נתונים בטוחה
        try:
            raw_values = worksheet.get_all_values()
            if len(raw_values) > 1:
                headers = [h.strip() for h in raw_values[0]]
                data = [dict(zip(headers, row)) for row in raw_values[1:] if any(row)]
            else:
                data = []
        except:
            data = [] 
            
        # משיכת בנקרול (ברירת מחדל 5000 אם לא נמצא)
        try:
            val = worksheet.cell(1, 10).value
            bankroll = float(str(val).replace(',', '')) if val else 5000.0
        except:
            bankroll = 5000.0
            
        return data, worksheet, bankroll, None
        
    except Exception as e:
        return None, None, 5000.0, f"Unexpected Error: {str(e)}"

raw_data, worksheet, initial_bankroll, error_msg = connect_to_sheets()

# --- 4. LOGIC ENGINE ---
def process_data(raw):
    if not raw: return pd.DataFrame(), {"Brighton": 30.0, "Africa Cup of Nations": 30.0}
    
    processed = []
    cycles = {"Brighton": 0.0, "Africa Cup of Nations": 0.0}
    next_bets = {"Brighton": 30.0, "Africa Cup of Nations": 30.0}
    
    for i, row in enumerate(raw):
        if not isinstance(row, dict): continue
        
        try:
            comp = str(row.get('Competition', 'Brighton')).strip()
            if not comp: comp = 'Brighton'
            
            home = str(row.get('Home Team', '')).strip()
            away = str(row.get('Away Team', '')).strip()
            match = f"{home} vs {away}"
            
            try: odds = float(str(row.get('Odds', 1)).replace(',', '.'))
            except: odds = 1.0
            
            try: stake = float(str(row.get('Stake', 0)).replace(',', '.'))
            except: stake = 0.0
            
            res = str(row.get('Result', '')).strip()
            date = str(row.get('Date', ''))
            
            if stake == 0: stake = next_bets.get(comp, 30.0)
            
            # PENDING
            if res == "Pending" or not res:
                processed.append({"Row": i+2, "Comp": comp, "Match": match, "Date": date, "Profit": 0, "Status": "Pending", "Stake": stake, "Odds": odds, "Income":0, "Expense":0})
                continue
                
            # COMPLETED
            cycles[comp] = cycles.get(comp, 0.0) + stake
            if "Draw (X)" in res:
                income = stake * odds
                net = income - cycles[comp]
                cycles[comp] = 0.0
                next_bets[comp] = 30.0
                status = "Won"
            else:
                income = 0.0
                net = -stake
                next_bets[comp] = stake * 2.0
                status = "Lost"
                
            processed.append({"Row": i+2, "Comp": comp, "Match": match, "Date": date, "Profit": net, "Status": status, "Stake": stake, "Odds": odds, "Income": income, "Expense": stake})
        except: continue
        
    return pd.DataFrame(processed), next_bets

df, next_stakes = process_data(raw_data)
current_bal = initial_bankroll + (df['Profit'].sum() if not df.empty else 0)

# --- 5. SIDEBAR ---
with st.sidebar:
    try: st.image(APP_LOGO_URL, use_container_width=True)
    except: pass
    
    # תצוגת סטטוס נקייה
    if error_msg:
        st.error("System Offline")
    else:
        st.success("System Online")
        
    st.metric("Bankroll", f"₪{initial_bankroll:,.0f}")
    
    amt = st.number_input("Amount", 100.0, step=50.0)
    c1, c2 = st.columns(2)
    if c1.button("Deposit"):
        if worksheet: worksheet.update_cell(1, 10, initial_bankroll + amt); connect_to_sheets.clear(); st.rerun()
    if c2.button("Withdraw"):
        if worksheet: worksheet.update_cell(1, 10, initial_bankroll - amt); connect_to_sheets.clear(); st.rerun()
        
    st.divider()
    track = st.selectbox("Navigate", ["📊 Overview", "Brighton", "Africa Cup of Nations"])
    if st.button("🔄 Sync"): connect_to_sheets.clear(); st.rerun()

# --- 6. MAIN CONTENT ---
if error_msg:
    st.error(f"⚠️ {error_msg}")
    with st.expander("Help - What happened?"):
        st.write("The app couldn't find your Sheet link in the Secrets.")
        st.write("1. Check if 'sheet_url' is correct in Secrets.")
        st.write("2. Ensure the sheet is shared with the bot email.")
    st.stop()

# === OVERVIEW PAGE ===
if track == "📊 Overview":
    st.markdown(f'<div class="comp-banner-box" style="background: linear-gradient(90deg, #40916c, #95d5b2);"><h1 class="comp-banner-text">OVERVIEW</h1></div>', unsafe_allow_html=True)
    st.markdown(f"<h1 style='text-align:center; color:white;'>₪{current_bal:,.2f}</h1>", unsafe_allow_html=True)
    
    if not df.empty:
        stats = df.groupby('Comp')['Profit'].sum().reset_index()
        for _, row in stats.iterrows():
            c = "#2d6a4f" if row['Profit'] >= 0 else "#d32f2f"
            comp_df = df[df['Comp'] == row['Comp']]
            wins = len(comp_df[comp_df['Status'] == 'Won'])
            matches = len(comp_df)
            roi = (row['Profit'] / initial_bankroll) * 100
            
            st.markdown(f"""
            <div class="activity-card">
                <div style="display:flex; justify-content:space-between;">
                    <h3 style="margin:0;">{row['Comp']}</h3>
                    <h3 style="color:{c}; margin:0;">₪{row['Profit']:,.0f}</h3>
                </div>
                <hr style="margin:5px 0;">
                <div style="display:flex; justify-content:space-around; font-size:0.9rem;">
                    <span>Matches: <b>{matches}</b></span>
                    <span>Wins: <b>{wins}</b></span>
                    <span>ROI: <b>{roi:.1f}%</b></span>
                </div>
            </div>""", unsafe_allow_html=True)
    else:
        st.info("No matches found. Go to competition pages to add data.")

# === COMPETITION PAGES ===
else:
    if track == "Brighton":
        c1, c2, logo = "#4CABFF", "#E6F7FF", "https://upload.wikimedia.org/wikipedia/en/f/fd/Brighton_&_Hove_Albion_FC_logo.svg"
        txt = "#004085"
    else:
        c1, c2, logo = "#007A33", "#FCD116", "https://upload.wikimedia.org/wikipedia/en/f/f9/2023_Africa_Cup_of_Nations_logo.png"
        txt = "#FFFFFF"

    st.markdown(f"""
        <div class="comp-banner-box" style="background: linear-gradient(90deg, {c1}, {c2});">
            <img src="{logo}" style="height:50px; margin-right:15px;">
            <h1 style="color:{txt}; margin:0;">{track.upper()}</h1>
        </div>
    """, unsafe_allow_html=True)

    st.markdown(f"<h1 style='text-align:center; color:white;'>₪{current_bal:,.2f}</h1>", unsafe_allow_html=True)

    f_df = df[df['Comp'] == track].copy() if not df.empty else pd.DataFrame()
    nb = next_stakes.get(track, 30.0)
    
    total_staked = f_df['Expense'].sum() if not f_df.empty else 0
    total_revenue = f_df['Income'].sum() if not f_df.empty else 0
    total_profit = f_df['Profit'].sum() if not f_df.empty else 0
    
    col1, col2, col3 = st.columns(3)
    col1.markdown(f"""<div class="metric-box"><div class="metric-label">STAKED</div><div class="metric-value">₪{total_staked:,.0f}</div></div>""", unsafe_allow_html=True)
    col2.markdown(f"""<div class="metric-box"><div class="metric-label">REVENUE</div><div class="metric-value">₪{total_revenue:,.0f}</div></div>""", unsafe_allow_html=True)
    p_color = "#2d6a4f" if total_profit >= 0 else "#d32f2f"
    col3.markdown(f"""<div class="metric-box"><div class="metric-label">NET PROFIT</div><div class="metric-value" style="color:{p_color}">₪{total_profit:,.0f}</div></div>""", unsafe_allow_html=True)

    st.markdown(f"<div style='text-align:center; margin:20px; font-size:1.3rem; color:white;'>Next Bet: <b style='color:#4CAF50;'>₪{nb:,.0f}</b></div>", unsafe_allow_html=True)

    with st.form("new"):
        st.write("### Add Match")
        c1, c2 = st.columns(2)
        h = c1.text_input("Home")
        a = c2.text_input("Away")
        c3, c4 = st.columns(2)
        o = c3.number_input("Odds", 3.2)
        s = c4.number_input("Stake", float(nb))
        res = st.radio("Result", ["Pending", "Draw (X)", "No Draw"], horizontal=True)
        if st.form_submit_button("Submit"):
            if h and a and worksheet:
                worksheet.append_row([str(datetime.date.today()), track, h, a, o, res, s, 0])
                st.success("Added!")
                connect_to_sheets.clear(); st.rerun()
            else:
                st.warning("Enter Team Names")

    st.write("### History")
    if not f_df.empty:
        for _, row in f_df.sort_index(ascending=False).iterrows():
            cls = "activity-card-won" if row['Status']=="Won" else "activity-card-pending" if row['Status']=="Pending" else "activity-card-lost"
            st.markdown(f"""
                <div class="activity-card {cls}">
                    <div style="display:flex; justify-content:space-between;">
                        <b>{row['Match']}</b>
                        <b>₪{row['Profit']:,.0f}</b>
                    </div>
                    <div style="font-size:0.8rem; color:#555;">{row['Date']} | {row['Status']}</div>
                </div>
            """, unsafe_allow_html=True)
            
            if row['Status'] == "Pending":
                b1, b2 = st.columns(2)
                if b1.button("✅ WIN", key=f"w{row['Row']}"):
                    if worksheet: worksheet.update_cell(row['Row'], 6, "Draw (X)"); connect_to_sheets.clear(); st.rerun()
                if b2.button("❌ LOSS", key=f"l{row['Row']}"):
                    if worksheet: worksheet.update_cell(row['Row'], 6, "No Draw"); connect_to_sheets.clear(); st.rerun()
    else:
        st.info("No matches yet.")

    with st.expander("Admin"):
        if st.button("Undo Last"):
             if len(raw_data) > 0: worksheet.delete_rows(len(raw_data) + 1); connect_to_sheets.clear(); st.rerun()