import streamlit as st
import pandas as pd
from datetime import datetime

# ==========================================
# --- CONFIGURATION & PRO UI STYLING ---
# ==========================================
st.set_page_config(page_title="ProTrade Journal", layout="wide", page_icon="📈")

# לינק לתמונה שלך
BG_IMAGE_URL = "https://i.postimg.cc/DzpDHPfJ/Gemini-Generated-Image-k2czqtk2czqtk2cz.png"

# CSS מעודכן עם הטיפ הטכני - רקע תמונה + שכבת כהות (Overlay)
st.markdown(f"""
<style>
    .stApp {{
        background: linear-gradient(rgba(14, 17, 23, 0.85), rgba(14, 17, 23, 0.85)), 
                    url('{BG_IMAGE_URL}');
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
        font-family: 'Roboto', sans-serif;
    }}
    
    /* עיצוב כרטיסי KPI */
    .metric-card {{
        background: rgba(31, 41, 55, 0.7); /* שקיפות עדינה לכרטיסים */
        backdrop-filter: blur(10px);
        border: 1px solid rgba(55, 65, 81, 0.5);
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 10px;
    }}
    .metric-label {{ color: #9CA3AF; font-size: 0.85rem; font-weight: 600; text-transform: uppercase; }}
    .metric-value {{ color: #F3F4F6; font-size: 1.8rem; font-weight: 700; }}
    .text-green {{ color: #34D399 !important; }}
    .text-red {{ color: #F87171 !important; }}
    
    /* עיצוב רשימת הטריידים וההיסטוריה */
    .trade-container {{ 
        background-color: rgba(17, 24, 39, 0.8); 
        border: 1px solid #374151; 
        border-radius: 10px; 
        padding: 15px; 
        margin-bottom: 15px; 
    }}
    
    .history-card {{
        background-color: rgba(31, 41, 55, 0.9);
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 15px;
        border-right: 8px solid #374151;
    }}
    .history-win {{ border-right: 8px solid #34D399; }}
    .history-loss {{ border-right: 8px solid #F87171; }}
    
    .detail-label {{ color: #9CA3AF; font-size: 0.75rem; text-transform: uppercase; margin-bottom: 2px; }}
    .detail-value {{ color: #E5E7EB; font-weight: 600; font-size: 1rem; }}
    .divider {{ border-top: 1px solid #374151; margin: 10px 0; }}
</style>
""", unsafe_allow_html=True)

# --- INITIALIZE STATE ---
if 'trades' not in st.session_state:
    st.session_state.trades = []
if 'initial_capital' not in st.session_state:
    st.session_state.initial_capital = 10000.0

# --- CONSTANTS ---
FUTURE_MULTIPLIERS = { "ES (S&P 500)": 50, "MES (Micro S&P)": 5, "NQ (Nasdaq 100)": 20, "MNQ (Micro Nasdaq)": 2, "GC (Gold)": 100, "CL (Crude Oil)": 1000 }

# ==========================================
# --- MODAL: NEW TRADE ENTRY ---
# ==========================================
@st.dialog("🚀 New Trade Entry")
def open_trade_modal():
    asset_class = st.selectbox("Asset Class", ["Stock", "Future", "Option"])
    symbol = ""
    multiplier = 1.0
    if asset_class == "Stock": symbol = st.text_input("Ticker Symbol").upper()
    elif asset_class == "Future":
        fut = st.selectbox("Contract", list(FUTURE_MULTIPLIERS.keys()))
        symbol = fut.split(" ")[0]
        multiplier = FUTURE_MULTIPLIERS[fut]
    else: # Option
        und = st.text_input("Underlying").upper()
        o_type = st.selectbox("Type", ["Call", "Put"])
        strike = st.text_input("Strike")
        symbol = f"{und} {o_type} {strike}"
        multiplier = 100.0

    col1, col2 = st.columns(2)
    with col1: direction = st.radio("Direction", ["Long", "Short"], horizontal=True)
    with col2: qty = st.number_input("Size / Quantity", min_value=1, value=1)
    
    c_date, c_price = st.columns(2)
    with c_date: entry_date = st.date_input("Entry Date", datetime.today())
    with c_price: entry_price = st.number_input("Entry Price ($)", min_value=0.00, format="%.2f")
    
    if st.button("Open Position", type="primary", use_container_width=True):
        new_trade = {
            "ID": len(st.session_state.trades) + 1, "Asset Class": asset_class, "Symbol": symbol,
            "Direction": direction, "Entry Date": entry_date.strftime("%Y-%m-%d"), 
            "Entry Price": entry_price, "Original Qty": qty, "Remaining Qty": qty, 
            "Multiplier": multiplier, "Exits": [], "Total Realized P&L": 0.0,
            "Status": "Open"
        }
        st.session_state.trades.append(new_trade)
        st.rerun()

# ==========================================
# --- SIDEBAR & CALCULATIONS ---
# ==========================================
with st.sidebar:
    st.title("⚙️ Controls")
    if st.button("➕ NEW TRADE", type="primary", use_container_width=True): open_trade_modal()
    st.markdown("---")
    st.session_state.initial_capital = st.number_input("Account Start ($)", value=st.session_state.initial_capital)
    if st.button("⚠️ CLEAR DATA", use_container_width=True):
        st.session_state.trades = []
        st.rerun()

# חישובים מאובטחים
total_pnl = sum(t.get('Total Realized P&L', 0.0) for t in st.session_state.trades)
curr_equity = st.session_state.initial_capital + total_pnl
roi = (total_pnl / st.session_state.initial_capital * 100) if st.session_state.initial_capital > 0 else 0.0

# ==========================================
# --- DASHBOARD UI ---
# ==========================================
st.markdown("## 📊 Portfolio Dashboard")
c1, c2, c3, c4 = st.columns(4)

def kpi_box(t, v, m=True, c=False, p=False):
    cl = ("text-green" if v > 0 else "text-red") if c else ""
    val = f"${v:,.2f}" if m else (f"{v:+.2f}%" if p else str(v))
    return f'<div class="metric-card"><div class="metric-label">{t}</div><div class="metric-value {cl}">{val}</div></div>'

with c1: st.markdown(kpi_box("Current Equity", curr_equity), unsafe_allow_html=True)
with c2: st.markdown(kpi_box("Total Realized P&L", total_pnl, True, True), unsafe_allow_html=True)
with c3: st.markdown(kpi_box("Account ROI", roi, False, True, True), unsafe_allow_html=True)
with c4: st.markdown(kpi_box("Open Trades", len([t for t in st.session_state.trades if t.get('Status') == 'Open']), False), unsafe_allow_html=True)

# ==========================================
# --- TABS: ACTIVE & HISTORY ---
# ==========================================
st.markdown("---")
t_act, t_hist = st.tabs(["📂 Active Trades", "📜 Detailed History"])

with t_act:
    active = [t for t in st.session_state.trades if t.get('Status') == 'Open']
    if not active: st.info("No active trades.")
    else:
        for i, trade in enumerate(st.session_state.trades):
            if trade.get('Status') == 'Open':
                st.markdown(f'<div class="trade-container"><b>{trade["Symbol"]}</b> ({trade["Direction"]}) | Entry: ${trade["Entry Price"]}</div>', unsafe_allow_html=True)
                with st.expander(f"Manage {trade['Symbol']}"):
                    cq, cp, cc = st.columns(3)
                    sq = cq.number_input("Qty to Sell", 1, trade['Remaining Qty'], key=f"q_{i}")
                    sp = cp.number_input("Exit Price", 0.0, format="%.2f", key=f"p_{i}")
                    sc = cc.number_input("Comm ($)", 0.0, key=f"c_{i}")
                    if st.button("Execute Partial Sale", key=f"b_{i}", use_container_width=True):
                        mult = trade.get('Multiplier', 1.0)
                        pnl = ((sp - trade['Entry Price']) if trade['Direction'] == "Long" else (trade['Entry Price'] - sp)) * sq * mult - sc
                        trade.setdefault('Exits', []).append({"qty": sq, "price": sp, "pnl": pnl, "date": datetime.now().strftime("%Y-%m-%d %H:%M")})
                        trade['Remaining Qty'] -= sq
                        trade['Total Realized P&L'] += pnl
                        if trade['Remaining Qty'] <= 0: trade['Status'] = "Closed"
                        st.rerun()

with t_hist:
    closed = [t for t in st.session_state.trades if t.get('Status') == 'Closed']
    if not closed: st.write("History is empty.")
    else:
        for t in closed:
            mult = t.get('Multiplier', 1.0)
            invested = t['Original Qty'] * t['Entry Price'] * mult
            exits = t.get('Exits', [])
            sold_val = sum(e['qty'] * e['price'] * mult for e in exits)
            sold_qty = sum(e['qty'] for e in exits)
            avg_exit = (sold_val / (sold_qty * mult))