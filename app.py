import streamlit as st
import pandas as pd
import plotly.express as px
import gspread
import datetime

# גרסת אפליקציה לעדכון Cache: 1.0.4
# --- 1. CONFIGURATION ---
APP_LOGO_URL = "https://i.postimg.cc/8Cr6SypK/yzwb-ll-sm.png"
BG_IMAGE_URL = "https://i.postimg.cc/GmFZ4KS7/Gemini-Generated-Image-k1h11zk1h11zk1h1.png"
SIDEBAR_BG_URL = "https://i.postimg.cc/NfdK3hck/'yzwb-ll'-sm-(1).png"

# חצים כתמונות למניעת טקסט keyb
IMG_ARROW_MAIN = "https://i.postimg.cc/vHQy61dy/Gemini-Generated-Image-dl91ekdl91ekdl91.png"
IMG_ARROW_SIDEBAR = "https://i.postimg.cc/hvVG4Nxz/Gemini-Generated-Image-2tueuy2tueuy2tue.png"

st.set_page_config(
    page_title="Elite Football Tracker",
    layout="wide",
    page_icon=APP_LOGO_URL,
    initial_sidebar_state="expanded"
)

# --- 2. CSS STYLING (UX/UI Optimized) ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;600;900&display=swap');
    
    #MainMenu {{visibility: hidden;}} 
    footer {{visibility: hidden;}}
    [data-testid="stSidebarNav"] {{display: none;}}

    /* תיקון חצים מוחלט */
    [data-testid="stSidebarCollapsedControl"] {{
        background-color: rgba(0, 0, 0, 0.6) !important;
        background-image: url('{IMG_ARROW_MAIN}') !important;
        background-size: 28px !important; background-repeat: no-repeat !important; background-position: center !important;
        width: 45px !important; height: 45px !important; border-radius: 12px !important; color: transparent !important;
    }}
    [data-testid="stSidebarCollapsedControl"] svg {{ display: none !important; }}

    button[kind="header"] {{
        background-image: url('{IMG_ARROW_SIDEBAR}') !important;
        background-size: 24px !important; background-repeat: no-repeat !important; background-position: center !important;
        color: transparent !important;
    }}
    button[kind="header"] svg {{ display: none !important; }}

    [data-testid="stAppViewContainer"] {{
        background-image: linear-gradient(rgba(0, 0, 0, 0.75), rgba(0, 0, 0, 0.75)), url("{BG_IMAGE_URL}");
        background-attachment: fixed; background-size: cover; background-position: center;
    }}

    [data-testid="stSidebar"] {{ background-color: #f8f9fa !important; border-right: 1px solid #ddd; }}
    [data-testid="stSidebar"]::before {{
        content: ""; position: absolute; top: 0; left: 0; width: 100%; height: 100%;
        background-image: url("{SIDEBAR_BG_URL}"); background-size: cover;
        filter: blur(4px); z-index: -1;
    }}
    [data-testid="stSidebar"] * {{ color: #000000 !important; text-shadow: none !important; font-family: 'Montserrat', sans-serif; }}

    .main h1, .main h2, .main h3, .main p {{ color: #ffffff !important; text-shadow: 2px 2px 4px rgba(0,0,0,0.8); }}

    /* באנרים ותגיות */
    .comp-banner {{
        border-radius: 15px; padding: 20px; display: flex; align-items: center; 
        justify-content: center; margin-bottom: 30px; box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    }}
    .comp-logo {{ height: 80px; }}
    .comp-title {{ font-size: 2rem; font-weight: 900; margin-left: 20px; text-transform: uppercase; }}

    .activity-card {{
        border-radius: 15px !important; padding: 20px !important; margin-bottom: 15px !important;
        box-shadow: 0 8px 25px rgba(0,0,0,0.4) !important; position: relative !important; overflow: hidden !important;
    }}
    .activity-card-won {{ background: rgba(40, 167, 69, 0.5) !important; border-left: 6px solid #28a745 !important; }}
    .activity-card-lost {{ background: rgba(220, 53, 69, 0.5) !important; border-left: 6px solid #dc3545 !important; }}

    @media only screen and (max-width: 768px) {{
        .comp-title {{ display: none !important; }}
        .comp-logo {{ height: 70px !important; }}
    }}
    </style>
""", unsafe_allow_html=True)

# --- 3. BACKEND LOGIC ---
def safe_float(v, default=0.0):
    try: return float(str(v).replace(',', '.'))
    except: return default

@st.cache_data(ttl=15)
def get_data_sync():
    try:
        gc = gspread.service_account_from_dict(st.secrets["service_account"])
        sh = gc.open_by_url(st.secrets["sheet_url"])
        ws_m = sh.get_worksheet(0)
        ws_c = sh.get_worksheet(1)
        m_data = ws_m.get_all_records()
        c_data = ws_c.get_all_records()
        try: base_br = float(str(ws_m.cell(1, 10).value).replace(',', ''))
        except: base_br = 5000.0
        return m_data, c_data, ws_m, ws_c, base_br
    except Exception as e:
        st.error(f"Sync Error: {e}"); return [], [], None, None, 5000.0

m_raw, c_raw, sheet_m, sheet_c, initial_br = get_data_sync()

# פונקציית עיבוד משחקים עם לוגיקת סייקלים
def process_matches(raw_matches):
    if not raw_matches: return pd.DataFrame()
    processed = []
    cycle_invest = {}
    for idx, row in enumerate(raw_matches):
        comp = str(row.get('Competition', 'Brighton')).strip() or 'Brighton'
        if comp not in cycle_invest: cycle_invest[comp] = 0.0
        odds = safe_float(row.get('Odds', 1.0))
        stake = safe_float(row.get('Stake', 30.0))
        res = str(row.get('Result', '')).strip()
        
        if res == "Pending":
            processed.append({"Row": idx+2, "Comp": comp, "Match": f"{row.get('Home Team','')} vs {row.get('Away Team','')}", "Net Profit": 0.0, "Status": "⏳ Pending", "Expense": stake, "Income": 0.0, "Date": row.get('Date', '')})
            continue
            
        cycle_invest[comp] += stake
        is_win = "Draw (X)" in res
        if is_win:
            inc = stake * odds
            net = inc - cycle_invest[comp]
            cycle_invest[comp] = 0.0
            status = "✅ Won"
        else:
            inc = 0.0
            net = -stake
            status = "❌ Lost"
        processed.append({"Row": idx+2, "Comp": comp, "Match": f"{row.get('Home Team','')} vs {row.get('Away Team','')}", "Net Profit": net, "Status": status, "Expense": stake, "Income": inc, "Date": row.get('Date', ''), "Odds": odds})
    return pd.DataFrame(processed)

# הגדרת ה-DF הראשי לפני הכל כדי למנוע NameError
df = process_matches(m_raw)
current_bal = initial_br + (df['Income'].sum() - df['Expense'].sum()) if not df.empty else initial_br

# שחזור היסטוריה אוטומטי לרשימת הניווט
legacy_list = df['Comp'].unique().tolist() if not df.empty else []
active_from_sheet = [c['Name'] for c in c_raw if c.get('Status') == 'Active']
archived_from_sheet = [c['Name'] for c in c_raw if c.get('Status') == 'Archived']
# הצגת כל מה שפעיל בשיטס + כל מה שיש לו היסטוריה ועדיין לא הוגדר כ-Archived
full_nav = list(set(active_from_sheet + [c for c in legacy_list if c not in archived_from_sheet]))

# --- 4. SIDEBAR ---
with st.sidebar:
    st.image(APP_LOGO_URL, use_container_width=True)
    st.metric("Base Bankroll", f"₪{initial_br:,.0f}")
    if st.button("➕ New Competition", use_container_width=True, type="primary"):
        st.session_state.show_modal = True

    st.divider()
    track = st.selectbox("Navigation", ["📊 Overview", "📚 History"] + sorted(full_nav))
    if st.button("🔄 Sync Cloud", use_container_width=True):
        get_data_sync.clear(); st.rerun()

# Modal ליצירת תחרות
if st.session_state.get('show_modal', False):
    with st.form("new_comp_form"):
        st.write("### 🆕 New Competition")
        n = st.text_input("Name")
        b = st.number_input("Starting Bet", value=30.0)
        l = st.text_input("Logo URL")
        c1 = st.color_picker("Color 1", "#4CABFF")
        c2 = st.color_picker("Color 2", "#E6F7FF")
        if st.form_submit_button("Launch"):
            if n and sheet_c:
                sheet_c.append_row([n, "Active", b, l, c1, c2])
                get_data_sync.clear(); st.session_state.show_modal = False; st.rerun()

# --- 5. MAIN CONTENT ---
if track == "📊 Overview":
    st.markdown(f'<div class="comp-banner" style="background: linear-gradient(90deg, #40916c, #95d5b2);"><img src="{APP_LOGO_URL}" class="comp-logo"><span class="comp-title" style="color:#081c15">Overview</span></div>', unsafe_allow_html=True)
    st.markdown(f"<h2 style='text-align: center; font-size: 3rem;'>₪{current_bal:,.2f}</h2><p style='text-align: center; opacity: 0.7;'>LIVE BANKROLL</p>", unsafe_allow_html=True)
    
    if not df.empty:
        summary = df.groupby('Comp').agg({'Net Profit': 'sum'}).reset_index()
        for _, row in summary.iterrows():
            st.markdown(f"""
                <div style="background: white; border-radius: 12px; padding: 20px; margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center;">
                    <h3 style="color: black !important; margin:0;">{row['Comp']}</h3>
                    <div style="text-align: right;"><div style="color: #666; font-size: 0.8rem;">PROFIT</div><div style="font-size: 1.5rem; font-weight: 900; color: {'#2d6a4f' if row['Net Profit']>=0 else '#dc3545'};">₪{row['Net Profit']:,.0f}</div></div>
                </div>
            """, unsafe_allow_html=True)

elif track == "📚 History":
    st.markdown("<h1>COMPETITION HISTORY</h1>", unsafe_allow_html=True)
    archived = [c for c in c_raw if c.get('Status') == 'Archived']
    for c in archived:
        st.write(f"### {c['Name']} (Archived)")

else:
    # עמוד תחרות ספציפית
    config = next((c for c in c_raw if c['Name'] == track), None)
    c1, c2, logo = (config['PrimaryColor'], config['SecondaryColor'], config['LogoURL']) if config else ("#4CABFF", "#E6F7FF", APP_LOGO_URL)
    
    st.markdown(f'<div class="comp-banner" style="background: linear-gradient(90deg, {c1}, {c2});"><img src="{logo if logo else APP_LOGO_URL}" class="comp-logo"><span class="comp-title">{track}</span></div>', unsafe_allow_html=True)
    
    # הוספת משחק
    with st.form("add_game"):
        col1, col2, col3 = st.columns(3)
        h, a, o = col1.text_input("Home"), col2.text_input("Away"), col3.number_input("Odds", value=3.2)
        s = st.number_input("Stake", value=30.0)
        res_radio = st.radio("Result", ["Pending", "Draw (X)", "No Draw"], horizontal=True)
        if st.form_submit_button("SUBMIT"):
            sheet_m.append_row([str(datetime.date.today()), track, h, a, o, res_radio, s, 0.0])
            get_data_sync.clear(); st.rerun()

    if st.button("🏁 Close Competition", use_container_width=True):
        if config:
            cell = sheet_c.find(track)
            sheet_c.update_cell(cell.row, 2, "Archived")
        else:
            sheet_c.append_row([track, "Archived", 30.0, "", "#555", "#888"])
        get_data_sync.clear(); st.rerun()

    st.markdown("### 📜 Activity Log")
    f_df = df[df['Comp'] == track].sort_index(ascending=False)
    for _, row in f_df.iterrows():
        c_type = "activity-card-won" if "Won" in row['Status'] else "activity-card-lost"
        st.markdown(f"""<div class="activity-card {c_type}"><div style="display:flex; justify-content:space-between; align-items:center;"><div><div style="font-weight:900; color:black;">{row['Match']}</div><div style="color:#333; font-size:0.8rem;">{row['Date']}</div></div><div style="text-align:right;"><div style="font-weight:900; color:black; font-size:1.2rem;">₪{row['Net Profit']:,.0f}</div></div></div></div>""", unsafe_allow_html=True)