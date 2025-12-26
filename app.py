import streamlit as st
import pandas as pd
import plotly.express as px
import gspread
import datetime

# --- Page Configuration ---
st.set_page_config(page_title="Elite Football Tracker", layout="wide", page_icon="🏟️")

# --- CSS (Branding) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@700;900&display=swap');
    .stApp { background-color: #f0f2f6; }
    .pro-header-container { padding: 30px 20px; border-radius: 16px; box-shadow: 0 8px 32px rgba(0,0,0,0.1); text-align: center; margin-bottom: 35px; display: flex; align-items: center; justify-content: center; border-left: 10px solid #2d6a4f; }
    .pro-header-text { margin: 0; font-family: 'Montserrat', sans-serif; font-weight: 900; font-size: 3rem; text-transform: uppercase; color: white; }
    .brighton-header { background: linear-gradient(135deg, #0057B8 0%, #0077C8 50%, #4CABFF 100%); }
    .afcon-header { background: linear-gradient(120deg, #CE1126 25%, #FCD116 50%, #007A33 85%); }
    .metric-card { background-color: white; padding: 20px; border-radius: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); border-left: 5px solid #2d6a4f; text-align: center; }
    div.stButton > button { width: 100%; border-radius: 12px; height: 3.2em; background-color: #2d6a4f; color: white; font-weight: bold; }
    .strategy-box { background-color: #e8f5e9; padding: 20px; border-radius: 12px; border: 1px solid #c8e6c9; color: #1b5e20; }
    </style>
""", unsafe_allow_html=True)

# --- Google Sheets Logic ---
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
        st.error(f"Error: {e}")
        return [], None, 5000.0

def update_bankroll_value(worksheet, new_val):
    try:
        worksheet.update_cell(1, 10, new_val)
        return True
    except: return False

# --- Core Logic: The Calculation Fix ---
def calculate_tracker_logic(raw_data, br_base, af_base):
    processed = []
    # מעקב אחרי כמה כסף הושקע בסיבוב הנוכחי (כולל הפסדים קודמים)
    comp_cycle_invest = {"Brighton": 0.0, "Africa Cup of Nations": 0.0}
    # מה ההימור הבא שצריך לשלוח
    next_bet_amount = {"Brighton": float(br_base), "Africa Cup of Nations": float(af_base)}

    for i, row in enumerate(raw_data):
        try:
            comp = str(row.get('Competition', 'Brighton')).strip()
            odds = float(str(row.get('Odds', 1)).replace(',', '.'))
            res_str = str(row.get('Result', '')).strip()
            # הסכום ששלחת בפועל (כפי שרשום בשיטס)
            actual_stake = float(row.get('Stake', next_bet_amount[comp]))

            # הוספת ההימור הנוכחי להשקעה הכוללת של הסיבוב
            comp_cycle_invest[comp] += actual_stake
            is_win = "Draw (X)" in res_str
            
            if is_win:
                gross_revenue = actual_stake * odds
                # רווח נקי מהסיבוב = מה שנכנס פחות כל מה שהושקע מתחילת הרצף
                cycle_net = gross_revenue - comp_cycle_invest[comp]
                chain_roi = (cycle_net / comp_cycle_invest[comp]) * 100
                status = "✅ Won"
                
                # איפוס סבב
                comp_cycle_invest[comp] = 0.0
                next_bet_amount[comp] = float(br_base if "Brighton" in comp else af_base)
            else:
                gross_revenue = 0.0
                cycle_net = -actual_stake # בשורה של הפסד, הנטו הוא פשוט ההפסד של אותו רגע
                chain_roi = 0.0
                status = "❌ Lost"
                # ההימור הבא יהיה הכפלה של מה ששלחנו עכשיו
                next_bet_amount[comp] = actual_stake * 2.0
            
            processed.append({
                "Date": row.get('Date', ''),
                "Comp": comp,
                "Match": f"{row.get('Home Team', '')} vs {row.get('Away Team', '')}",
                "Odds": odds,
                "Stake": actual_stake,
                "Gross Revenue": gross_revenue,
                "Cycle Net Profit": cycle_net if is_win else 0.0, # מציג רווח רק בשורת ניצחון
                "Status": status,
                "ROI": f"{chain_roi:.1f}%" if is_win else ""
            })
        except: continue
    return processed, next_bet_amount

# --- Data Execution ---
raw_data, worksheet, saved_bankroll = get_data_from_sheets()
processed_data, next_stakes = calculate_tracker_logic(raw_data, 30.0, 20.0)

# --- Financial Totals ---
if processed_data:
    df = pd.DataFrame(processed_data)
    # יתרה = בנקרול בסיס + (סך כל ההכנסות ברוטו) - (סך כל ההשקעות)
    total_revenue = df['Gross Revenue'].sum()
    total_stakes = df['Stake'].sum()
    current_balance = saved_bankroll + (total_revenue - total_stakes)
    global_p_l = total_revenue - total_stakes
else:
    current_balance, global_p_l = saved_bankroll, 0.0
    df = pd.DataFrame()

# --- Sidebar ---
with st.sidebar:
    st.title("💰 Finance")
    st.metric("Base Bankroll", f"₪{saved_bankroll:,.0f}")
    trans = st.number_input("Amount", min_value=0.0, value=100.0, step=50.0)
    ca, cb = st.columns(2)
    if ca.button("Deposit"):
        if update_bankroll_value(worksheet, saved_bankroll + trans): st.rerun()
    if cb.button("Withdraw"):
        if update_bankroll_value(worksheet, saved_bankroll - trans): st.rerun()
    st.divider()
    selected_comp = st.selectbox("Track", ["Brighton", "Africa Cup of Nations"])
    if st.button("🔄 Refresh"): st.rerun()

# --- Main UI ---
h_style = "brighton-header" if selected_comp == "Brighton" else "afcon-header"
st.markdown(f"<div class='pro-header-container {h_style}'><h1 class='pro-header-text'>{selected_comp.upper()}</h1></div>", unsafe_allow_html=True)

# --- Dashboard ---
c1, c2, c3 = st.columns(3)
c1.metric("Live Balance", f"₪{current_balance:,.0f}")
c2.metric("Total P/L", f"₪{global_p_l:,.0f}", delta=f"{global_p_l:,.0f}")
c3.metric("Next Bet", f"₪{next_stakes[selected_comp]}")

# --- Entry Form ---
st.write("---")
col_form, col_intel = st.columns([1, 1])
with col_form:
    with st.form("match_entry"):
        st.subheader("Add Match")
        h = st.text_input("Home", value="Brighton" if selected_comp == "Brighton" else "")
        a = st.text_input("Away")
        od = st.number_input("Odds", value=3.2)
        # כאן האופציה לשינוי ידני של הסכום
        stk = st.number_input("Stake to Bet", value=float(next_stakes[selected_comp]))
        res = st.radio("Result", ["Draw (X)", "No Draw"], horizontal=True)
        if st.form_submit_button("Sync Game"):
            worksheet.append_row([str(datetime.date.today()), selected_comp, h, a, od, res, stk, 0.0])
            st.rerun()

with col_intel:
    st.subheader("Strategy & Stats")
    if not df.empty:
        f_df = df[df['Comp'] == selected_comp]
        if not f_df.empty:
            f_df['Chart'] = saved_bankroll + (f_df['Gross Revenue'].cumsum() - f_df['Stake'].cumsum())
            st.plotly_chart(px.line(f_df, y='Chart', title="Track Performance"), use_container_width=True)

# --- Activity Log ---
st.subheader("📜 Activity Log")
if not df.empty:
    f_df = df[df['Comp'] == selected_comp]
    # עיצוב והצגת הטבלה
    st.dataframe(f_df[['Date', 'Match', 'Odds', 'Stake', 'Gross Revenue', 'Cycle Net Profit', 'Status', 'ROI']].sort_index(ascending=False), use_container_width=True, hide_index=True)

with st.expander("Admin"):
    if st.button("Undo Last"):
        worksheet.delete_rows(len(raw_data) + 1)
        st.rerun()