import streamlit as st
import pandas as pd
import plotly.express as px
import gspread
import datetime

# --- הגדרות דף ---
st.set_page_config(page_title="Pro Football Tracker", layout="centered", page_icon="⚽")

# --- עיצוב CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    h1 { color: #1b4332; text-align: center; }
    .stMetric { background-color: white; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
""", unsafe_allow_html=True)

# --- פונקציית חיבור לגיליון ---
def get_data_from_sheets():
    try:
        gc = gspread.service_account_from_dict(st.secrets["service_account"])
        sh = gc.open_by_url(st.secrets["sheet_url"])
        worksheet = sh.get_worksheet(0)
        data = worksheet.get_all_records()
        return data, worksheet
    except Exception as e:
        st.error(f"שגיאת חיבור ל-Google Sheets: {e}")
        return [], None

# --- לוגיקה: חישוב מקבילי חכם ---
def calculate_parallel_status(raw_data, initial_stake):
    processed_games = []
    comp_states = {"Brighton": initial_stake, "Africa Cup of Nations": initial_stake}
    total_inv, total_rev = 0, 0

    if not raw_data:
        return [], comp_states, 0, 0, 0

    for i, row in enumerate(raw_data):
        try:
            # חילוץ נתונים עם ערכי ברירת מחדל כדי למנוע קריסה
            comp = str(row.get('Competition', 'Brighton')).strip()
            # טיפול ב-Odds: אם ריק או לא מספר, נשתמש ב-1.0
            try:
                odds = float(str(row.get('Odds', 1)).replace(',', '.'))
            except:
                odds = 1.0
            
            res_str = str(row.get('Result', '')).strip()
            
            if comp not in comp_states:
                comp_states[comp] = initial_stake
            
            current_stake = comp_states[comp]
            total_inv += current_stake
            
            # בדיקת תוצאה מדויקת למניעת בלבול עם "No Draw"
            # זה הפתרון לבאג שכל משחק נצבע בירוק
            is_win = (res_str == "Draw (X)")
            
            if is_win:
                revenue = current_stake * odds
                profit = revenue - current_stake
                comp_states[comp] = initial_stake
                status = "✅ Won"
            else:
                revenue = 0
                profit = -current_stake
                comp_states[comp] = current_stake * 2
                status = "❌ Lost"
            
            total_rev += revenue
            processed_games.append({
                "Date": row.get('Date', ''),
                "Comp": comp,
                "Match": f"{row.get('Home Team', '')} vs {row.get('Away Team', '')}",
                "Odds": odds,
                "Stake": current_stake,
                "Status": status,
                "Profit": profit
            })
        except Exception as e:
            # אם שורה ספציפית בעייתית, נדלג עליה ולא נקריס את כל האפליקציה
            continue

    total_bal = total_rev - total_inv
    return processed_games, comp_states, total_inv, total_rev, total_bal

# --- Sidebar ---
with st.sidebar:
    st.title("⚙️ Tactics Board")
    selected_comp = st.selectbox("Current Track", ["Brighton", "Africa Cup of Nations"])
    initial_stake = st.number_input("Base Stake (₪)", min_value=10, value=50, step=10)
    st.divider()
    if st.button("רענן נתונים"):
        st.rerun()

# --- טעינה וחישוב ---
raw_data, worksheet = get_data_from_sheets()
processed_data, next_stakes, total_inv, total_rev, total_bal = calculate_parallel_status(raw_data, initial_stake)

# --- תצוגה ראשית ---
st.markdown(f"<h1>⚽ {selected_comp} Tracker</h1>", unsafe_allow_html=True)

# מדדים כספיים
col1, col2, col3 = st.columns(3)
col1.metric("השקעה כוללת", f"₪{total_inv:,.0f}")
col2.metric("החזר כולל", f"₪{total_rev:,.0f}")
col3.metric("רווח/הפסד נקי", f"₪{total_bal:,.0f}", delta=total_bal)

# טופס הזנה
st.markdown("### 📝 הזנת משחק חדש")
with st.container(border=True):
    rec_stake = next_stakes.get(selected_comp, initial_stake)
    st.success(f"💡 הימור מומלץ לסיבוב הבא ב-{selected_comp}: **₪{rec_stake}**")
    
    with st.form("input_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            d_in = st.date_input("תאריך", datetime.date.today())
            h_t = st.text_input("Home Team", value="Brighton" if selected_comp == "Brighton" else "")
            o_in = st.number_input("Odds (X)", min_value=1.0, value=3.2, step=0.1)
        with c2:
            a_t = st.text_input("Away Team")
            r_in = st.radio("תוצאה", ["Draw (X)", "No Draw"], horizontal=True)
        
        if st.form_submit_button("🚀 שמור לגיליון", use_container_width=True):
            if h_t and a_t:
                # חישוב רווח מהיר לשמירה בגיליון
                p_val = (rec_stake * o_in) - rec_stake if r_in == "Draw (X)" else -rec_stake
                new_row = [str(d_in), selected_comp, h_t, a_t, o_in, r_in, rec_stake, p_val]
                worksheet.append_row(new_row)
                st.balloons()
                st.rerun()
            else:
                st.error("נא למלא את שמות שתי הקבוצות")

# היסטוריה וגרפים
if processed_data:
    df = pd.DataFrame(processed_data)
    
    st.markdown("### 📜 היסטוריית משחקים")
    st.dataframe(
        df.style.map(lambda x: 'background-color: #d4edda' if 'Won' in str(x) else ('background-color: #f8d7da' if 'Lost' in str(x) else ''), subset=['Status']),
        use_container_width=True, hide_index=True
    )
    
    st.markdown("### 📈 גרף רווחיות")
    df['Cumulative'] = df['Profit'].cumsum()
    fig = px.area(df, x=df.index, y='Cumulative', title="מאזן מצטבר")
    fig.update_traces(line_color='#2d6a4f', fillcolor='rgba(45, 106, 79, 0.2)')
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("אין עדיין נתונים בגיליון. הכנס את המשחק הראשון למעלה!")