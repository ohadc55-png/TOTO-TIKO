import streamlit as st
import pandas as pd
import plotly.express as px
import gspread
import datetime

# --- הגדרות דף ---
st.set_page_config(page_title="Elite Football Tracker", layout="wide", page_icon="🏟️")

# --- עיצוב CSS (מותאם אישית) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@700;900&display=swap');
    .stApp { background-color: #f0f2f6; }
    .pro-header-container { padding: 30px 20px; border-radius: 16px; text-align: center; margin-bottom: 30px; }
    .pro-header-text { margin: 0; font-family: 'Montserrat', sans-serif; font-weight: 900; font-size: 3rem; color: white; text-transform: uppercase; }
    .brighton-header { background: linear-gradient(135deg, #0057B8 0%, #0077C8 50%, #4CABFF 100%); }
    .afcon-header { background: linear-gradient(120deg, #CE1126 25%, #FCD116 50%, #007A33 85%); }
    
    /* עיצוב כרטיסיות המדדים */
    .metric-container { display: flex; justify-content: space-between; gap: 15px; margin-bottom: 20px; }
    .metric-card { 
        background-color: white; 
        padding: 20px; 
        border-radius: 15px; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.1); 
        flex: 1; 
        text-align: center;
        border-bottom: 5px solid #2d6a4f;
    }
    .metric-label { font-size: 1rem; color: #666; font-weight: bold; }
    .metric-value { font-size: 1.8rem; font-weight: 900; color: #1b4332; }
    </style>
""", unsafe_allow_html=True)

# --- חיבור ל-Google Sheets ---
def get_data_from_sheets():
    try:
        gc = gspread.service_account_from_dict(st.secrets["service_account"])
        sh = gc.open_by_url(st.secrets["sheet_url"])
        worksheet = sh.get_worksheet(0)
        data = worksheet.get_all_records()
        try:
            val = worksheet.cell(1, 10).value
            initial_bankroll = float(val) if val else 5000.0
        except:
            initial_bankroll = 5000.0
        return data, worksheet, initial_bankroll
    except Exception as e:
        st.error(f"שגיאת חיבור: {e}")
        return [], None, 5000.0

def update_bankroll_value(worksheet, new_val):
    try:
        worksheet.update_cell(1, 10, new_val)
        return True
    except: return False

# --- לוגיקת חישובים ---
def process_betting_logic(raw_data, br_base, af_base):
    processed = []
    # מעקב אחרי סכום מצטבר להכפלה בסבב הנוכחי
    next_bet_calc = {"Brighton": float(br_base), "Africa Cup of Nations": float(af_base)}
    # מעקב אחרי השקעה בסבב הנוכחי כדי לחשב ROI נכון
    current_cycle_invest = {"Brighton": 0.0, "Africa Cup of Nations": 0.0}

    for i, row in enumerate(raw_data):
        try:
            comp = str(row.get('Competition', 'Brighton')).strip()
            odds = float(str(row.get('Odds', 1)).replace(',', '.'))
            res_str = str(row.get('Result', '')).strip()
            # הוצאה (Stake): מה שכתוב בגיליון
            expense = float(row.get('Stake', next_bet_calc[comp]))
            
            current_cycle_invest[comp] += expense
            is_win = "Draw (X)" in res_str
            
            if is_win:
                income = expense * odds # הכנסה ברוטו
                profit = income - current_cycle_invest[comp] # רווח נקי מהסבב
                roi = (profit / current_cycle_invest[comp]) * 100
                status = "✅ Won"
                
                # איפוס סבב
                next_bet_calc[comp] = float(br_base if "Brighton" in comp else af_base)
                current_cycle_invest[comp] = 0.0
            else:
                income = 0.0 # אין הכנסה בהפסד
                profit = -expense
                roi = 0.0
                status = "❌ Lost"
                # הכפלה להימור הבא
                next_bet_calc[comp] = expense * 2.0
            
            processed.append({
                "Date": row.get('Date', ''),
                "Comp": comp,
                "Match": f"{row.get('Home Team', '')} vs {row.get('Away Team', '')}",
                "Odds": odds,
                "Expense": expense,
                "Income": income,
                "Net Profit": profit if is_win else -expense,
                "Status": status,
                "ROI": f"{roi:.1f}%" if is_win else ""
            })
        except: continue
    return processed, next_bet_calc

# --- טעינת נתונים ---
raw_data, worksheet, saved_bankroll = get_data_from_sheets()
processed_games, next_stakes = process_betting_logic(raw_data, 30.0, 20.0)

# --- חישובים כלליים ---
if processed_games:
    df = pd.DataFrame(processed_games)
    total_expenses = df['Expense'].sum()
    total_income = df['Income'].sum()
    total_profit = total_income - total_expenses
    current_balance = saved_bankroll + total_profit
else:
    total_expenses = total_income = total_profit = 0.0
    current_balance = saved_bankroll
    df = pd.DataFrame()

# --- תפריט צד (פיננסי) ---
with st.sidebar:
    st.title("💰 ניהול קופה")
    st.metric("בנקרול בסיס (J1)", f"₪{saved_bankroll:,.0f}")
    amount = st.number_input("סכום לביצוע (₪)", min_value=0.0, value=100.0, step=50.0)
    c_dep, c_wit = st.columns(2)
    if c_dep.button("הפקדה (+)"):
        if update_bankroll_value(worksheet, saved_bankroll + amount): st.rerun()
    if c_wit.button("משיכה (-)"):
        if update_bankroll_value(worksheet, saved_bankroll - amount): st.rerun()
    st.divider()
    selected_comp = st.selectbox("בחר מסלול", ["Brighton", "Africa Cup of Nations"])
    if st.button("🔄 רענון נתונים"): st.rerun()

# --- כותרת ממותגת ---
h_style = "brighton-header" if selected_comp == "Brighton" else "afcon-header"
st.markdown(f"<div class='pro-header-container {h_style}'><h1 class='pro-header-text'>{selected_comp}</h1></div>", unsafe_allow_html=True)

# --- דאשבורד עליון (היתרה העדכנית) ---
st.markdown(f"<h1 style='text-align: center; color: #1b4332; margin-bottom: 20px;'>יתרה נוכחית: ₪{current_balance:,.2f}</h1>", unsafe_allow_html=True)

# --- שלושת הטאבים (הוצאה, הכנסה, רווח) ---
f_df = df[df['Comp'] == selected_comp] if not df.empty else pd.DataFrame()
exp_track = f_df['Expense'].sum() if not f_df.empty else 0.0
inc_track = f_df['Income'].sum() if not f_df.empty else 0.0
pro_track = inc_track - exp_track

st.markdown(f"""
    <div class='metric-container'>
        <div class='metric-card'>
            <div class='metric-label'>הוצאה כוללת (Track)</div>
            <div class='metric-value'>₪{exp_track:,.2f}</div>
        </div>
        <div class='metric-card'>
            <div class='metric-label'>הכנסה כוללת (Track)</div>
            <div class='metric-value'>₪{inc_track:,.2f}</div>
        </div>
        <div class='metric-card' style='border-bottom-color: {"#2d6a4f" if pro_track >= 0 else "#ce1126"}'>
            <div class='metric-label'>רווח/הפסד נקי</div>
            <div class='metric-value'>₪{pro_track:,.2f}</div>
        </div>
    </div>
""", unsafe_allow_html=True)

# --- טופס הזנה ---
col_form, col_chart = st.columns([1, 1])
with col_form:
    with st.form("new_match"):
        st.subheader("📝 הזנת משחק חדש")
        h = st.text_input("קבוצה ביתית", value="Brighton" if selected_comp == "Brighton" else "")
        a = st.text_input("קבוצת חוץ")
        od = st.number_input("יחס הימור (Odds)", value=3.2, step=0.1)
        # אפשרות לעריכת סכום ההימור - ברירת מחדל היא ההכפלה
        stk = st.number_input("סכום לשליחה (הוצאה)", value=float(next_stakes[selected_comp]))
        res = st.radio("תוצאה", ["Draw (X)", "No Draw"], horizontal=True)
        if st.form_submit_button("שלח לענן 🚀"):
            if h and a:
                worksheet.append_row([str(datetime.date.today()), selected_comp, h, a, od, res, stk, 0.0])
                st.rerun()

with col_chart:
    if not f_df.empty:
        f_df['Balance_Line'] = saved_bankroll + (f_df['Income'].cumsum() - f_df['Expense'].cumsum())
        st.plotly_chart(px.line(f_df, y='Balance_Line', title="גרף צמיחה - יתרה חיה"), use_container_width=True)

# --- יומן פעילות (Activity Log) ---
st.subheader("📜 יומן פעילות מפורט")
if not f_df.empty:
    display_df = f_df[['Date', 'Match', 'Odds', 'Expense', 'Income', 'Net Profit', 'Status', 'ROI']].sort_index(ascending=False)
    
    def color_status(val):
        color = '#d4edda' if 'Won' in str(val) else '#f8d7da'
        return f'background-color: {color}'

    st.dataframe(display_df.style.applymap(color_status, subset=['Status']), use_container_width=True, hide_index=True)

with st.expander("🛠️ כלים למנהל"):
    if st.button("מחק שורה אחרונה"):
        worksheet.delete_rows(len(raw_data) + 1)
        st.rerun()