import streamlit as st
import pandas as pd
import gspread
import datetime
import plotly.express as px

# --- 1. CONFIGURATION ---
APP_LOGO_URL = "https://i.postimg.cc/8Cr6SypK/yzwb-ll-sm.png"
BG_IMAGE_URL = "https://i.postimg.cc/GmFZ4KS7/Gemini-Generated-Image-k1h11zk1h11zk1h1.png"
# Backup URL
SHEET_URL = "https://docs.google.com/spreadsheets/d/1o7OO2nyqAEqRgUq5makKZKR7ZtFyeh2JcJlzXnEmsv8/edit?gid=0#gid=0"

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
    .activity-card {{
        background: rgba(255,255,255,0.95); border-radius: 12px; padding: 15px; margin-bottom: 10px;
        border-left: 6px solid #ccc; color: black !important;
    }}
    .activity-card-won {{ border-left-color: #28a745 !important; }}
    .activity-card-lost {{ border-left-color: #dc3545 !important; }}
    .activity-card-pending {{ border-left-color: #ffc107 !important; }}
    </style>
""", unsafe_allow_html=True)

# --- 3. DATA FETCHING (Robust Mode) ---
@st.cache_data(ttl=15)
def get_data_from_sheets():
    try:
        if "service_account" not in st.secrets:
            return [], None, 5000.0, "Missing Secrets", "None"
            
        gc = gspread.service_account_from_dict(st.secrets["service_account"])
        url = st.secrets.get("sheet_url", SHEET_URL)
        sh = gc.open_by_url(url)
        
        # משיכת הלשונית הראשונה
        worksheet = sh.get_worksheet(0)
        sheet_name = worksheet.title  # שם הלשונית לבדיקה
        
        # שימוש ב-get_all_records
        # הערה: זה עלול להיכשל אם יש עמודות בלי כותרת
        try:
            data = worksheet.get_all_records()
        except:
            # גיבוי: אם נכשל, נחזיר רשימה ריקה כדי לא לקרוס
            data = []

        # משיכת בנקרול
        try:
            val = worksheet.cell(1, 10).value # תא J1
            initial_bankroll = float(str(val).replace(',', '')) if val else 5000.0
        except:
            initial_bankroll = 5000.0
            
        return data, worksheet, initial_bankroll, None, sheet_name
        
    except Exception as e:
        return [], None, 5000.0, str(e), "Error"

# שימוש בפונקציה החדשה שמחזירה גם את שם הגיליון
raw_data, worksheet, saved_br, error_msg, sheet_name_found = get_data_from_sheets()

# --- 4. LOGIC ---
def process_data(raw):
    if not raw: return pd.DataFrame(), {}
    
    processed = []
    cycles = {"Brighton": 0.0, "Africa Cup of Nations": 0.0}
    next_bets = {"Brighton": 30.0, "Africa Cup of Nations": 30.0}
    
    for i, row in enumerate(raw):
        try:
            # המרה בטוחה למילון אם זה לא מילון
            if not isinstance(row, dict): continue

            comp = str(row.get('Competition', 'Brighton')).strip()
            if not comp: comp = 'Brighton'
            
            home = str(row.get('Home Team', '')).strip()
            away = str(row.get('Away Team', '')).strip()
            
            try: odds = float(str(row.get('Odds', 1)).replace(',', '.'))
            except: odds = 1.0
            
            try: stake = float(str(row.get('Stake', 0)).replace(',', '.'))
            except: stake = 0.0
            
            res = str(row.get('Result', '')).strip()
            date = str(row.get('Date', ''))
            
            if stake == 0: stake = next_bets.get(comp, 30.0)
            
            if res == "Pending" or not res:
                processed.append({"Row": i+2, "Comp": comp, "Match": f"{home} vs {away}", "Date": date, "Profit": 0.0, "Status": "Pending", "Stake": stake, "Odds": odds, "Income":0, "Expense":0})
                continue
            
            if comp not in cycles: cycles[comp] = 0.0
            cycles[comp] += stake
            
            if "Draw (X)" in res:
                inc = stake * odds
                net = inc - cycles[comp]
                cycles[comp] = 0.0
                next_bets[comp] = 30.0
                status = "Won"
            else:
                inc = 0.0
                net = -stake
                next_bets[comp] = stake * 2.0
                status = "Lost"
            
            processed.append({"Row": i+2, "Comp": comp, "Match": f"{home} vs {away}", "Date": date, "Profit": net, "Status": status, "Stake": stake, "Odds": odds, "Income": inc, "Expense": stake})
        except: continue
        
    return pd.DataFrame(processed), next_bets

df, next_stakes = process_data(raw_data)
current_bal = saved_br + (df['Income'].sum() - df['Expense'].sum()) if not df.empty else saved_br

# --- 5. UI ---
with st.sidebar:
    st.image(APP_LOGO_URL, use_container_width=True)
    st.metric("Live Bankroll", f"₪{current_bal:,.2f}")
    st.divider()
    track = st.selectbox("Navigate", ["📊 Overview", "Brighton", "Africa Cup of Nations"])
    if st.button("🔄 Sync"): get_data_from_sheets.clear(); st.rerun()

# --- MAIN ---
if track == "📊 Overview":
    st.markdown("<h1 style='text-align:center; color:white;'>SUMMARY OVERVIEW</h1>", unsafe_allow_html=True)
    st.markdown(f"<h2 style='text-align:center; color:white;'>₪{current_bal:,.2f}</h2>", unsafe_allow_html=True)
    if not df.empty:
        stats = df.groupby('Comp')['Profit'].sum().reset_index()
        for _, row in stats.iterrows():
            c = "#2d6a4f" if row['Profit'] >= 0 else "#d32f2f"
            st.markdown(f"<div class='activity-card'><h3>{row['Comp']}</h3><h2 style='color:{c}'>₪{row['Profit']:,.0f}</h2></div>", unsafe_allow_html=True)
else:
    st.markdown(f"<h1 style='text-align:center; color:white;'>{track.upper()}</h1>", unsafe_allow_html=True)
    nb = next_stakes.get(track, 30.0)
    st.success(f"Next Bet: ₪{nb:,.0f}")
    
    if not df.empty:
        sub = df[df['Comp'] == track].sort_index(ascending=False)
        for _, r in sub.iterrows():
            cls = "activity-card-won" if r['Status']=="Won" else "activity-card-lost" if r['Status']=="Lost" else "activity-card-pending"
            st.markdown(f"<div class='activity-card {cls}'><b>{r['Match']}</b> | ₪{r['Profit']:,.0f}</div>", unsafe_allow_html=True)

# --- DEBUGGER (קריטי לפתרון הבעיה) ---
st.divider()
with st.expander("🛠️ Debugger - לחץ כאן לבדיקה", expanded=True):
    if error_msg:
        st.error(f"שגיאת חיבור: {error_msg}")
    else:
        st.success(f"מחובר בהצלחה ללשונית בשם: '{sheet_name_found}'")
        
        if not raw_data:
            st.warning("החיבור הצליח, אבל לא זוהו נתונים תקינים.")
            st.write("מנסה למשוך נתונים גולמיים (בלי כותרות) לבדיקה:")
            # נסיון אחרון להציג משהו
            try:
                raw_values = worksheet.get_all_values()
                st.dataframe(raw_values)
            except:
                st.error("לא ניתן לקרוא נתונים כלל.")
        else:
            st.write(f"נמצאו {len(raw_data)} שורות תקינות:")
            st.dataframe(pd.DataFrame(raw_data).head())