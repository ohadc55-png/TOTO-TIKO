import streamlit as st
import pandas as pd
import gspread
import datetime
import traceback # כלי לניתוח שגיאות עומק

# --- 1. הגדרות ---
APP_LOGO_URL = "https://i.postimg.cc/8Cr6SypK/yzwb-ll-sm.png"
BG_IMAGE_URL = "https://i.postimg.cc/GmFZ4KS7/Gemini-Generated-Image-k1h11zk1h11zk1h1.png"

# אנחנו צורבים את ה-ID כאן כדי לעקוף בעיות ב-Secrets
# זה ה-ID שחילצתי מהלינק ששלחת
DIRECT_SHEET_ID = "1pOdsQYcINhjSaSKssRx1VZlKYoqJg2n_oq6-ce7vSck"

st.set_page_config(page_title="Elite Football Tracker", layout="wide", page_icon=APP_LOGO_URL)

# --- 2. עיצוב ---
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
    .comp-banner-box {{
        border-radius: 15px; padding: 20px; display: flex; align-items: center; 
        justify-content: center; margin-bottom: 30px; box-shadow: 0 10px 30px rgba(0,0,0,0.5);
        border: 2px solid rgba(255,255,255,0.4); width: 100%;
    }}
    </style>
""", unsafe_allow_html=True)

# --- 3. חיבור "חכם" וחושפני ---
@st.cache_data(ttl=15)
def connect_to_sheets():
    try:
        # שלב 1: בדיקת המפתח בסיקרטס
        if "service_account" not in st.secrets:
            return None, None, 5000.0, "Critical Error: [service_account] not found in Secrets!"
            
        # שלב 2: התחברות לחשבון
        gc = gspread.service_account_from_dict(st.secrets["service_account"])
        
        # שלב 3: פתיחה לפי ID ישיר (עוקף בעיות טקסט)
        sh = gc.open_by_key(DIRECT_SHEET_ID)

        # שלב 4: בחירת גיליון וקריאה
        worksheet = sh.get_worksheet(0)
        raw_values = worksheet.get_all_values()
        
        # שלב 5: עיבוד ראשוני
        if len(raw_values) > 1:
            headers = [h.strip() for h in raw_values[0]]
            data = [dict(zip(headers, row)) for row in raw_values[1:] if any(row)]
        else:
            data = []
            
        # שלב 6: משיכת בנקרול
        try:
            val = worksheet.cell(1, 10).value
            bankroll = float(str(val).replace(',', '')) if val else 5000.0
        except:
            bankroll = 5000.0
            
        return data, worksheet, bankroll, None
        
    except Exception as e:
        # כאן הסוד: אנחנו מדפיסים את השגיאה המלאה
        error_details = traceback.format_exc()
        return None, None, 5000.0, error_details

raw_data, worksheet, initial_bankroll, error_trace = connect_to_sheets()

# --- 4. לוגיקה ---
def process_data(raw):
    if not raw: return pd.DataFrame(), {"Brighton": 30.0, "Africa Cup of Nations": 30.0}
    processed = []
    cycles = {"Brighton": 0.0, "Africa Cup of Nations": 0.0}
    next_bets = {"Brighton": 30.0, "Africa Cup of Nations": 30.0}
    
    for i, row in enumerate(raw):
        if not isinstance(row, dict): continue
        try:
            comp = str(row.get('Competition', 'Brighton')).strip() or 'Brighton'
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
            
            if res == "Pending" or not res:
                processed.append({"Row": i+2, "Comp": comp, "Match": match, "Date": date, "Profit": 0, "Status": "Pending", "Stake": stake, "Odds": odds, "Income":0, "Expense":0})
                continue
                
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

# --- 5. ממשק משתמש ---
with st.sidebar:
    st.image(APP_LOGO_URL, use_container_width=True)
    
    if error_trace:
        st.error("⚠️ Connection Failed")
    else:
        st.success("✅ System Online")
        
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

# --- 6. תצוגה ראשית וטיפול בשגיאות ---
if error_trace:
    st.title("🚨 דיאגנוסטיקה בזמן אמת")
    st.markdown("הרובוט נכשל בהתחברות. הנה הסיבה המדויקת:")
    
    # הצגת השגיאה הגולמית
    st.code(error_trace, language="python")
    
    st.warning("""
    **מה לחפש בקוד למעלה?**
    1. **APIError: 403**: אין הרשאות. (האם שיתפת את ה-Email הנכון?)
    2. **APIError: 404**: לא נמצא. (האם ה-ID נכון? בקוד הזה הוא צרוב בפנים)
    3. **GSpreadException**: בעיה בפורמט הנתונים.
    """)
    st.stop()

# === תוכן רגיל (אם אין שגיאה) ===
if track == "📊 Overview":
    st.markdown(f'<div class="comp-banner-box" style="background: linear-gradient(90deg, #40916c, #95d5b2);"><h1 class="comp-banner-text">OVERVIEW</h1></div>', unsafe_allow_html=True)
    st.markdown(f"<h1 style='text-align:center; color:white;'>₪{current_bal:,.2f}</h1>", unsafe_allow_html=True)
    if not df.empty:
        stats = df.groupby('Comp')['Profit'].sum().reset_index()
        for _, row in stats.iterrows():
            c = "#2d6a4f" if row['Profit'] >= 0 else "#d32f2f"
            st.markdown(f"""<div class="activity-card"><h3 style="margin:0;">{row['Comp']}</h3><h3 style="color:{c}; margin:0;">₪{row['Profit']:,.0f}</h3></div>""", unsafe_allow_html=True)
    else:
        st.info("No data yet.")

else:
    if track == "Brighton":
        c1, c2, logo = "#4CABFF", "#E6F7FF", "https://upload.wikimedia.org/wikipedia/en/f/fd/Brighton_&_Hove_Albion_FC_logo.svg"
    else:
        c1, c2, logo = "#007A33", "#FCD116", "https://upload.wikimedia.org/wikipedia/en/f/f9/2023_Africa_Cup_of_Nations_logo.png"

    st.markdown(f"""<div class="comp-banner-box" style="background: linear-gradient(90deg, {c1}, {c2});"><img src="{logo}" style="height:50px; margin-right:15px;"><h1 style="color:white; margin:0;">{track.upper()}</h1></div>""", unsafe_allow_html=True)
    st.markdown(f"<h1 style='text-align:center; color:white;'>₪{current_bal:,.2f}</h1>", unsafe_allow_html=True)
    
    f_df = df[df['Comp'] == track].copy() if not df.empty else pd.DataFrame()
    nb = next_stakes.get(track, 30.0)
    st.markdown(f"<div style='text-align:center; margin:20px; font-size:1.3rem; color:white;'>Next Bet: <b style='color:#4CAF50;'>₪{nb:,.0f}</b></div>", unsafe_allow_html=True)

    with st.form("new"):
        st.write("Add Match")
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
                connect_to_sheets.clear(); st.rerun()

    st.write("History")
    if not f_df.empty:
        for _, row in f_df.sort_index(ascending=False).iterrows():
            cls = "activity-card-won" if row['Status']=="Won" else "activity-card-pending" if row['Status']=="Pending" else "activity-card-lost"
            st.markdown(f"""<div class="activity-card {cls}"><b>{row['Match']}</b> | ₪{row['Profit']:,.0f}<br><small>{row['Date']} | {row['Status']}</small></div>""", unsafe_allow_html=True)
            if row['Status'] == "Pending":
                b1, b2 = st.columns(2)
                if b1.button("WIN", key=f"w{row['Row']}"): worksheet.update_cell(row['Row'], 6, "Draw (X)"); connect_to_sheets.clear(); st.rerun()
                if b2.button("LOSS", key=f"l{row['Row']}"): worksheet.update_cell(row['Row'], 6, "No Draw"); connect_to_sheets.clear(); st.rerun()