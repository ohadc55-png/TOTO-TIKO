import streamlit as st
import pandas as pd
import gspread
import datetime
import plotly.express as px

# --- 1. CONFIGURATION ---
APP_LOGO_URL = "https://i.postimg.cc/8Cr6SypK/yzwb-ll-sm.png"
BG_IMAGE_URL = "https://i.postimg.cc/GmFZ4KS7/Gemini-Generated-Image-k1h11zk1h11zk1h1.png"
# הלינק לשיטס שלך
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

# --- 3. DATA FETCHING ---
@st.cache_data(ttl=15)
def get_data_from_sheets():
    try:
        # התחברות
        gc = gspread.service_account_from_dict(st.secrets["service_account"])
        sh = gc.open_by_url(SHEET_URL) # שימוש בלינק הקשיח מהקוד
        worksheet = sh.get_worksheet(0)
        data = worksheet.get_all_records()
        
        # קריאת בנקרול מתא J1 (עמודה 10)
        try:
            val = worksheet.cell(1, 10).value
            initial_bankroll = float(str(val).replace(',', '')) if val else 5000.0
        except:
            initial_bankroll = 5000.0
            
        return data, worksheet, initial_bankroll
    except Exception as e:
        return [], None, 5000.0

raw_data, worksheet, saved_br = get_data_from_sheets()

# --- 4. LOGIC ---
def process_data(raw):
    if not raw: return pd.DataFrame(), {}
    
    processed = []
    # אתחול סייקלים
    cycles = {"Brighton": 0.0, "Africa Cup of Nations": 0.0}
    next_bets = {"Brighton": 30.0, "Africa Cup of Nations": 30.0}
    
    for i, row in enumerate(raw):
        try:
            # קריאת נתונים לפי הכותרות בצילום המסך שלך
            # שימוש ב-strip() כדי למנוע בעיות רווחים
            comp = str(row.get('Competition', '')).strip()
            # אם אין תחרות, נניח שזה ברייטון כברירת מחדל
            if not comp: comp = 'Brighton'
            
            home = str(row.get('Home Team', '')).strip()
            away = str(row.get('Away Team', '')).strip()
            match = f"{home} vs {away}"
            date = str(row.get('Date', ''))
            
            # המרת מספרים בטוחה
            try: odds = float(str(row.get('Odds', 1)).replace(',', '.'))
            except: odds = 1.0
            
            try: stake = float(str(row.get('Stake', 0)).replace(',', '.'))
            except: stake = 0.0
            
            res = str(row.get('Result', '')).strip()
            
            # חישוב הימור הבא אם ה-Stake ריק
            if stake == 0: 
                stake = next_bets.get(comp, 30.0)
            
            # לוגיקה למשחק פתוח
            if res == "Pending" or not res:
                processed.append({
                    "Row": i+2, "Comp": comp, "Match": match, 
                    "Date": date, "Profit": 0.0, "Status": "Pending", 
                    "Stake": stake, "Odds": odds, "Income": 0.0, "Expense": 0.0
                })
                continue
            
            # ניהול סייקלים למשחק סגור
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
            
            processed.append({
                "Row": i+2, "Comp": comp, "Match": match, 
                "Date": date, "Profit": net, "Status": status, 
                "Stake": stake, "Odds": odds, "Income": inc, "Expense": stake
            })
        except: continue
        
    return pd.DataFrame(processed), next_bets

df, next_stakes = process_data(raw_data)
# חישוב יתרה נוכחית
current_bal = saved_br + (df['Income'].sum() - df['Expense'].sum()) if not df.empty else saved_br

# --- 5. UI ---
with st.sidebar:
    st.image(APP_LOGO_URL, use_container_width=True)
    st.metric("Live Bankroll", f"₪{current_bal:,.2f}")
    st.divider()
    track = st.selectbox("Navigate", ["📊 Overview", "Brighton", "Africa Cup of Nations"])
    if st.button("🔄 Sync with Google Sheets"):
        get_data_from_sheets.clear(); st.rerun()

# --- MAIN PAGES ---
if track == "📊 Overview":
    st.markdown("<h1 style='text-align:center; color:white;'>SUMMARY OVERVIEW</h1>", unsafe_allow_html=True)
    st.markdown(f"<h2 style='text-align:center; color:white;'>₪{current_bal:,.2f}</h2>", unsafe_allow_html=True)
    
    if not df.empty:
        comp_summary = df.groupby('Comp')['Profit'].sum().reset_index()
        for _, row in comp_summary.iterrows():
            c = "#2d6a4f" if row['Profit'] >= 0 else "#d32f2f"
            st.markdown(f"""
                <div class="activity-card">
                    <h3 style="color:black; margin:0;">{row['Comp']}</h3>
                    <div style="font-size:1.5rem; font-weight:900; color:{c};">₪{row['Profit']:,.0f}</div>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No data available yet.")

else:
    # עמוד תחרות
    st.markdown(f"<h1 style='text-align:center; color:white;'>{track.upper()}</h1>", unsafe_allow_html=True)
    
    nb = next_stakes.get(track, 30.0)
    st.success(f"Next Bet for {track}: ₪{nb:,.0f}")
    
    # סינון נתונים לפי התחרות שנבחרה
    if not df.empty:
        f_df = df[df['Comp'] == track].sort_index(ascending=False)
        
        # הצגת כרטיסיות משחק
        for _, row in f_df.iterrows():
            cls = "activity-card-won" if row['Status'] == "Won" else "activity-card-pending" if row['Status'] == "Pending" else "activity-card-lost"
            
            st.markdown(f"""
                <div class="activity-card {cls}">
                    <div style="display:flex; justify-content:space-between;">
                        <div>
                            <b>{row['Match']}</b><br>
                            <span style="font-size:0.8rem; color:#555;">{row['Date']}</span>
                        </div>
                        <div style="text-align:right;">
                            <b style="font-size:1.1rem;">₪{row['Profit']:,.0f}</b><br>
                            <span style="font-size:0.8rem;">{row['Status']}</span>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.warning(f"No matches found for {track}. Check if 'Competition' column in Sheets matches exactly.")

# --- DEBUGGER (יופיע למטה - יראה לך מה השיטס באמת שולח) ---
st.divider()
with st.expander("🛠️ Debugger (Check Connection Data)"):
    if raw_data:
        st.write("Connection Successful! Here is the raw data from Google Sheets:")
        st.dataframe(pd.DataFrame(raw_data))
    else:
        st.error("Connected to Sheets, but the sheet seems empty or could not be read.")