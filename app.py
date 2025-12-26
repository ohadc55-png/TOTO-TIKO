import streamlit as st
import pandas as pd
import plotly.express as px
import gspread
import datetime

# --- Page Configuration ---
st.set_page_config(
    page_title="Elite Football Tracker",
    layout="wide",
    page_icon="🏟️",
    initial_sidebar_state="expanded"
)

# --- CSS (Branding) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@700;900&display=swap');
    .stApp { background-color: #f0f2f6; }
    .pro-header-container { 
        padding: 30px 20px; 
        border-radius: 16px; 
        box-shadow: 0 8px 32px rgba(0,0,0,0.1); 
        text-align: center; 
        margin-bottom: 35px; 
        display: flex; 
        align-items: center; 
        justify-content: center; 
        border-left: 10px solid #2d6a4f; 
    }
    .pro-header-text { 
        margin: 0; 
        font-family: 'Montserrat', sans-serif; 
        font-weight: 900; 
        font-size: 3rem; 
        text-transform: uppercase; 
        color: white; 
    }
    .brighton-header { background: linear-gradient(135deg, #0057B8 0%, #0077C8 50%, #4CABFF 100%); }
    .afcon-header { background: linear-gradient(120deg, #CE1126 25%, #FCD116 50%, #007A33 85%); }
    .metric-card { 
        background-color: white; 
        padding: 20px; 
        border-radius: 15px; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.1); 
        border-left: 5px solid #2d6a4f; 
        text-align: center; 
    }
    div.stButton > button { 
        width: 100%; 
        border-radius: 12px; 
        height: 3.2em; 
        background-color: #2d6a4f; 
        color: white; 
        font-weight: bold; 
        border: none; 
        transition: 0.3s; 
    }
    div.stButton > button:hover { 
        background-color: #1b4332; 
        transform: translateY(-2px); 
    }
    .strategy-box { 
        background-color: #e8f5e9; 
        padding: 20px; 
        border-radius: 12px; 
        border: 1px solid #c8e6c9; 
        color: #1b5e20; 
    }
    div[data-testid="stForm"] { 
        background-color: white; 
        border-radius: 15px; 
        padding: 30px; 
        box-shadow: 0 10px 25px rgba(0,0,0,0.05); 
    }
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
    except:
        return False

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
            # הוספת תמיכה בתחרויות חדשות
            if comp not in comp_cycle_invest:
                comp_cycle_invest[comp] = 0.0
                next_bet_amount[comp] = float(br_base if "Brighton" in comp else af_base)
            
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
                chain_roi = (cycle_net / comp_cycle_invest[comp]) * 100 if comp_cycle_invest[comp] > 0 else 0.0
                status = "✅ Won"
                
                # איפוס סבב
                comp_cycle_invest[comp] = 0.0
                next_bet_amount[comp] = float(br_base if "Brighton" in comp else af_base)
            else:
                gross_revenue = 0.0
                cycle_net = 0.0  # לא מציגים רווח שלילי, רק 0.0
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
                "Cycle Net Profit": cycle_net,  # מציג רווח רק בשורת ניצחון
                "Status": status,
                "ROI": f"{chain_roi:.1f}%" if is_win and chain_roi > 0 else ""
            })
        except Exception as e:
            continue
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
    total_revenue, total_stakes = 0.0, 0.0
    df = pd.DataFrame()

# --- Sidebar ---
with st.sidebar:
    st.title("💰 Finance")
    st.metric("Base Bankroll", f"₪{saved_bankroll:,.0f}")
    trans = st.number_input("Amount", min_value=0.0, value=100.0, step=50.0)
    ca, cb = st.columns(2)
    if ca.button("Deposit"):
        new_val = saved_bankroll + trans
        if update_bankroll_value(worksheet, new_val):
            st.toast(f"Deposited ₪{trans:,.0f}", icon="💰")
            st.rerun()
    if cb.button("Withdraw"):
        new_val = saved_bankroll - trans
        if update_bankroll_value(worksheet, new_val):
            st.toast(f"Withdrew ₪{trans:,.0f}", icon="💸")
            st.rerun()
    st.divider()
    selected_comp = st.selectbox("Track", ["Brighton", "Africa Cup of Nations"])
    if st.button("🔄 Refresh"):
        st.rerun()

# --- Main UI ---
h_style = "brighton-header" if selected_comp == "Brighton" else "afcon-header"
st.markdown(f"<div class='pro-header-container {h_style}'><h1 class='pro-header-text'>{selected_comp.upper()}</h1></div>", unsafe_allow_html=True)

# --- Dashboard ---
# Live Balance at the top
st.markdown(f"<h2 style='text-align: center; margin-bottom: 30px;'>Live Balance: ₪{current_balance:,.0f}</h2>", unsafe_allow_html=True)

# Financial metrics in 3 columns
c1, c2, c3 = st.columns(3)
c1.metric("Total Expenses", f"₪{total_stakes:,.0f}")
c2.metric("Total Revenue", f"₪{total_revenue:,.0f}")
delta_value = f"₪{global_p_l:,.0f}" if global_p_l >= 0 else f"-₪{abs(global_p_l):,.0f}"
c3.metric("Net Profit", f"₪{global_p_l:,.0f}", delta=delta_value)

# Next Bet below
st.markdown(f"<p style='text-align: center; margin-top: 20px;'><b>Next Bet:</b> ₪{next_stakes.get(selected_comp, 30.0):,.0f}</p>", unsafe_allow_html=True)

# --- Entry Form ---
st.write("---")
col_form, col_intel = st.columns([1, 1])
with col_form:
    with st.form("match_entry"):
        st.subheader("Add Match")
        h = st.text_input("Home", value="Brighton" if selected_comp == "Brighton" else "")
        a = st.text_input("Away")
        od = st.number_input("Odds", value=3.2, step=0.1, min_value=1.0)
        # כאן האופציה לשינוי ידני של הסכום
        suggested_stake = next_stakes.get(selected_comp, 30.0)
        stk = st.number_input("Stake to Bet", value=float(suggested_stake), min_value=1.0, step=5.0)
        res = st.radio("Result", ["Draw (X)", "No Draw"], horizontal=True)
        if st.form_submit_button("Sync Game"):
            if h and a:
                worksheet.append_row([str(datetime.date.today()), selected_comp, h, a, od, res, stk, 0.0])
                st.toast("Match Saved!", icon="✅")
                st.rerun()
            else:
                st.warning("Please fill in both Home and Away teams")

with col_intel:
    st.subheader("Strategy & Stats")
    if not df.empty:
        f_df = df[df['Comp'] == selected_comp].copy()
        if not f_df.empty:
            # חישוב מצטבר של היתרה
            f_df['Chart'] = saved_bankroll + (f_df['Gross Revenue'].cumsum() - f_df['Stake'].cumsum())
            fig = px.line(f_df, y='Chart', title="Track Performance", labels={'Chart': 'Balance (₪)', 'index': 'Match'})
            fig.update_traces(line_color='#2d6a4f', line_width=3)
            fig.update_layout(
                height=300,
                margin=dict(l=0, r=0, t=30, b=0),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # סטטיסטיקות נוספות
            wins = len(f_df[f_df['Status'] == "✅ Won"])
            losses = len(f_df[f_df['Status'] == "❌ Lost"])
            win_rate = (wins / len(f_df) * 100) if len(f_df) > 0 else 0
            st.markdown(f"<div class='strategy-box'><b>Win Rate:</b> {win_rate:.1f}% ({wins}W / {losses}L)</div>", unsafe_allow_html=True)

# --- Activity Log ---
st.subheader("📜 Activity Log")
if not df.empty:
    f_df = df[df['Comp'] == selected_comp].copy()
    if not f_df.empty:
        # עיצוב טבלה - צבעים לפי סטטוס
        def highlight_results(row):
            color = '#d4edda' if 'Won' in str(row['Status']) else '#f8d7da'
            return [f'background-color: {color}'] * len(row)
        
        # מיון לפי תאריך (החדש ביותר ראשון)
        display_df = f_df[['Date', 'Match', 'Odds', 'Stake', 'Gross Revenue', 'Cycle Net Profit', 'Status', 'ROI']].copy()
        display_df = display_df.sort_index(ascending=False)
        
        # הצגת הטבלה
        st.dataframe(
            display_df.style.apply(highlight_results, axis=1),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No matches recorded yet for this competition")
else:
    st.info("No data available")

with st.expander("🛠️ Admin"):
    if st.button("Undo Last"):
        if len(raw_data) > 0:
            try:
                worksheet.delete_rows(len(raw_data) + 1)
                st.toast("Last entry removed", icon="🗑️")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")
        else:
            st.warning("No entries to remove")
