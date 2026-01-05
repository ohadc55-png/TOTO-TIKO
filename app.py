import streamlit as st
import pandas as pd
import gspread
import datetime
import plotly.express as px

# --- 1. CONFIGURATION ---
APP_LOGO_URL = "https://i.postimg.cc/8Cr6SypK/yzwb-ll-sm.png"
BG_IMAGE_URL = "https://i.postimg.cc/GmFZ4KS7/Gemini-Generated-Image-k1h11zk1h11zk1h1.png"
# המזהה הישיר של הגיליון שלך (הכי בטוח)
SHEET_ID = "1o7OO2nyqAEqRgUq5makKZKR7ZtFyeh2JcJlzXnEmsv8"

st.set_page_config(page_title="Elite Football Tracker", layout="wide", page_icon=APP_LOGO_URL)

# --- 2. CSS STYLING ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;600;900&display=swap');
    [data-testid="stAppViewContainer"] {{
        background-image: linear-gradient(rgba(0,0,0,0.7), rgba(0,0,0,0.7)), url("{BG_IMAGE_URL}");
        background-attachment: fixed; background-size: cover;
    }}
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
    .comp-banner-logo {{ height: 55px; margin-right: 20px; }}
    .comp-banner-text {{ margin: 0; font-size: 1.8rem; font-weight: 900; text-transform: uppercase; color: white; }}
    </style>
""", unsafe_allow_html=True)

# --- 3. CONNECTION MANAGER ---
@st.cache_data(ttl=15)
def connect_to_sheets():
    try:
        if "service_account" not in st.secrets:
            return None, None, 5000.0, "Missing Secrets"
            
        # התחברות
        gc = gspread.service_account_from_dict(st.secrets["service_account"])
        
        # פתיחה לפי ID (יותר יציב מ-URL)
        try:
            sh = gc.open_by_key(SHEET_ID)
        except Exception as e:
            return None, None, 5000.0, f"Cannot find sheet with ID {SHEET_ID}. Error: {e}"

        worksheet = sh.get_worksheet(0)
        
        # ניסיון למשוך נתונים
        try:
            data = worksheet.get_all_records()
        except:
            data = [] # במקרה של גיליון ריק לגמרי
            
        # משיכת יתרה
        try:
            val = worksheet.cell(1, 10).value
            bankroll = float(str(val).replace(',', '')) if val else 5000.0
        except:
            bankroll = 5000.0
            
        return data, worksheet, bankroll, None
        
    except Exception as e:
        return None, None, 5000.0, str(e)

raw_data, worksheet, saved_br, error_msg = connect_to_sheets()

# --- 4. LOGIC ---
def process_data(raw):
    if not raw: return pd.DataFrame(), {"Brighton": 30.0, "Africa Cup of Nations": 30.0}
    
    processed = []
    cycles = {"Brighton": 0.0, "Africa Cup of Nations": 0.0}
    next_bets = {"Brighton": 30.0, "Africa Cup of Nations": 30.0}
    
    for i, row in enumerate(raw):
        # המרה בטוחה למילון
        if not isinstance(row, dict): continue
        
        try:
            comp = str(row.get('Competition', 'Brighton')).strip() or 'Brighton'
            home = str(row.get('Home Team', '')).strip()
            away = str(row.get('Away Team', '')).strip()
            odds = float(str(row.get('Odds', 1)).replace(',', '.'))
            stake = float(str(row.get('Stake', 0)).replace(',', '.'))
            res = str(row.get('Result', '')).strip()
            date = str(row.get('Date', ''))
            
            if stake == 0: stake = next_bets.get(comp, 30.0)
            
            # לוגיקה
            if res == "Pending" or not res:
                processed.append({"Row": i+2, "Comp": comp, "Match": f"{home} vs {away}", "Date": date, "Profit": 0, "Status": "Pending", "Stake": stake, "Odds": odds})
                continue
                
            cycles[comp] = cycles.get(comp, 0.0) + stake
            if "Draw (X)" in res:
                net = (stake * odds) - cycles[comp]
                cycles[comp] = 0.0
                next_bets[comp] = 30.0
                status = "Won"
            else:
                net = -stake
                next_bets[comp] = stake * 2.0
                status = "Lost"
                
            processed.append({"Row": i+2, "Comp": comp, "Match": f"{home} vs {away}", "Date": date, "Profit": net, "Status": status, "Stake": stake, "Odds": odds})
        except: continue
        
    return pd.DataFrame(processed), next_bets

df, next_stakes = process_data(raw_data)
current_bal = saved_br + (df['Profit'].sum() if not df.empty else 0)

# --- 5. UI & SIDEBAR ---
with st.sidebar:
    st.image(APP_LOGO_URL, use_container_width=True)
    
    # הצגת סטטוס חיבור
    if error_msg:
        st.error("Offline")
    else:
        st.success("Connected")
        
    st.metric("Bankroll", f"₪{saved_br:,.0f}")
    
    amt = st.number_input("Amount", 100.0, step=50.0)
    c1, c2 = st.columns(2)
    if c1.button("Deposit"):
        if worksheet: worksheet.update_cell(1, 10, saved_br + amt); connect_to_sheets.clear(); st.rerun()
    if c2.button("Withdraw"):
        if worksheet: worksheet.update_cell(1, 10, saved_br - amt); connect_to_sheets.clear(); st.rerun()
        
    st.divider()
    track = st.selectbox("Navigate", ["📊 Overview", "Brighton", "Africa Cup of Nations"])
    if st.button("🔄 Sync"): connect_to_sheets.clear(); st.rerun()

# --- 6. MAIN CONTENT ---
if error_msg:
    st.error(f"⚠️ שגיאת התחברות קריטית: {error_msg}")
    st.info("אנא וודא שהמייל של הרובוט מוגדר כ-Editor בגיליון: toto-tiko@toto-tiko.iam.gserviceaccount.com")
    st.stop()

if track == "📊 Overview":
    st.markdown(f'<div class="comp-banner-box" style="background: linear-gradient(90deg, #40916c, #95d5b2);"><h1 class="comp-banner-text">OVERVIEW</h1></div>', unsafe_allow_html=True)
    st.markdown(f"<h1 style='text-align:center; color:white;'>₪{current_bal:,.2f}</h1>", unsafe_allow_html=True)
    
    if not df.empty:
        stats = df.groupby('Comp')['Profit'].sum().reset_index()
        for _, row in stats.iterrows():
            c = "#2d6a4f" if row['Profit'] >= 0 else "#d32f2f"
            st.markdown(f"""<div class='activity-card'><h3>{row['Comp']}</h3><h2 style='color:{c}'>₪{row['Profit']:,.0f}</h2></div>""", unsafe_allow_html=True)
    else:
        st.info("No matches recorded yet.")

else:
    # עמודי תחרות
    if track == "Brighton":
        c1, c2, logo = "#4CABFF", "#E6F7FF", "https://upload.wikimedia.org/wikipedia/en/f/fd/Brighton_&_Hove_Albion_FC_logo.svg"
        txt_col = "#004085"
    else:
        c1, c2, logo = "#007A33", "#FCD116", "https://upload.wikimedia.org/wikipedia/en/f/f9/2023_Africa_Cup_of_Nations_logo.png"
        txt_col = "#FFFFFF"

    st.markdown(f"""
        <div class="comp-banner-box" style="background: linear-gradient(90deg, {c1}, {c2});">
            <img src="{logo}" class="comp-banner-logo">
            <h1 class="comp-banner-text" style="color: {txt_col} !important;">{track.upper()}</h1>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"<h1 style='text-align:center; color:white;'>₪{current_bal:,.2f}</h1>", unsafe_allow_html=True)
    
    nb = next_stakes.get(track, 30.0)
    st.info(f"Next Bet: ₪{nb:,.0f}")

    # --- ADD MATCH FORM (תמיד מוצג) ---
    with st.form("new_match"):
        st.write("### Add Match")
        c1, c2 = st.columns(2)
        h = c1.text_input("Home")
        a = c2.text_input("Away")
        c3, c4 = st.columns(2)
        o = c3.number_input("Odds", 3.2)
        s = c4.number_input("Stake", float(nb))
        res = st.radio("Result", ["Pending", "Draw (X)", "No Draw"], horizontal=True)
        if st.form_submit_button("Submit"):
            if h and a:
                if worksheet:
                    worksheet.append_row([str(datetime.date.today()), track, h, a, o, res, s, 0])
                    st.success("Added!")
                    connect_to_sheets.clear(); st.rerun()
            else:
                st.warning("Enter Team Names")

    # --- ACTIVITY LOG ---
    st.write("### History")
    if not df.empty:
        f_df = df[df['Comp'] == track].sort_index(ascending=False)
        if f_df.empty:
            st.info("No history for this competition.")
        for _, row in f_df.iterrows():
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
                if b1.button("✅ Won", key=f"w{row['Row']}"):
                    if worksheet: worksheet.update_cell(row['Row'], 6, "Draw (X)"); connect_to_sheets.clear(); st.rerun()
                if b2.button("❌ Lost", key=f"l{row['Row']}"):
                    if worksheet: worksheet.update_cell(row['Row'], 6, "No Draw"); connect_to_sheets.clear(); st.rerun()
    else:
        st.info("No data found in sheet.")

    with st.expander("Admin"):
        if st.button("Undo Last"):
            if worksheet and raw_data: worksheet.delete_rows(len(raw_data) + 1); connect_to_sheets.clear(); st.rerun()

# --- DEBUGGER (נמצא למטה כדי שתוכל לראות מה קורה) ---
st.divider()
if st.checkbox("Show Connection Debug info"):
    st.write(f"Sheet ID used: {SHEET_ID}")
    if error_msg:
        st.error(error_msg)
    elif not raw_data:
        st.warning("Connected, but returned 0 rows.")
    else:
        st.success(f"Loaded {len(raw_data)} rows.")
        st.dataframe(pd.DataFrame(raw_data).head())