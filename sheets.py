"""Google Sheets CRUD module for Elite Football Tracker."""
import os
import json
import gspread
from google.oauth2.service_account import Credentials

# Constants
DEFAULT_BANKROLL = 5000.0
BANKROLL_CELL_ROW = 1
BANKROLL_CELL_COL = 10
MATCHES_SHEET = 0  # First sheet (index 0)
COMPETITIONS_SHEET = "Competitions"
RESULT_COL = 6

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]


def get_credentials():
    """Load Google service account credentials from env var or file."""
    # Try environment variable first (for Render/production)
    creds_json = os.environ.get("GOOGLE_CREDENTIALS")
    if creds_json:
        info = json.loads(creds_json)
        return Credentials.from_service_account_info(info, scopes=SCOPES)

    # Try credentials file (for local development)
    creds_file = os.path.join(os.path.dirname(__file__), "credentials.json")
    if os.path.exists(creds_file):
        return Credentials.from_service_account_file(creds_file, scopes=SCOPES)

    raise RuntimeError("No Google credentials found. Set GOOGLE_CREDENTIALS env var or provide credentials.json")


def get_sheet_id():
    """Get Google Sheet ID from env var."""
    sheet_id = os.environ.get("SHEET_ID")
    if not sheet_id:
        raise RuntimeError("No SHEET_ID found. Set SHEET_ID env var.")
    return sheet_id


def get_spreadsheet():
    """Get authorized spreadsheet connection."""
    creds = get_credentials()
    gc = gspread.authorize(creds)
    return gc.open_by_key(get_sheet_id())


def get_matches_worksheet():
    """Get matches worksheet (first sheet)."""
    sh = get_spreadsheet()
    return sh.get_worksheet(MATCHES_SHEET)


def get_competitions_worksheet():
    """Get competitions worksheet."""
    sh = get_spreadsheet()
    return sh.worksheet(COMPETITIONS_SHEET)


# --- READ OPERATIONS ---

def get_all_data():
    """Read all data from Google Sheets. Returns (matches_data, bankroll, competitions_data, error)."""
    try:
        sh = get_spreadsheet()
    except Exception as e:
        return [], DEFAULT_BANKROLL, [], str(e)

    # Read matches
    try:
        matches_ws = sh.get_worksheet(MATCHES_SHEET)
        raw_values = matches_ws.get_all_values()
        if len(raw_values) > 1:
            headers = [h.strip() for h in raw_values[0]]
            matches_data = [
                dict(zip(headers, row))
                for row in raw_values[1:]
                if any(cell.strip() for cell in row)
            ]
        else:
            matches_data = []
    except Exception as e:
        matches_data = []

    # Read competitions
    try:
        comp_ws = sh.worksheet(COMPETITIONS_SHEET)
        comp_values = comp_ws.get_all_values()
        if len(comp_values) > 1:
            comp_headers = [h.strip() for h in comp_values[0]]
            competitions_data = [
                dict(zip(comp_headers, row))
                for row in comp_values[1:]
                if any(cell.strip() for cell in row)
            ]
        else:
            competitions_data = []
    except Exception as e:
        competitions_data = []

    # Read bankroll
    try:
        val = matches_ws.cell(BANKROLL_CELL_ROW, BANKROLL_CELL_COL).value
        bankroll = float(str(val).replace(',', '').replace('₪', '').strip()) if val else DEFAULT_BANKROLL
    except Exception:
        bankroll = DEFAULT_BANKROLL

    return matches_data, bankroll, competitions_data, None


# --- WRITE OPERATIONS ---

def update_bankroll(new_amount):
    """Update bankroll cell value."""
    ws = get_matches_worksheet()
    ws.update_cell(BANKROLL_CELL_ROW, BANKROLL_CELL_COL, new_amount)


def add_match(date, competition, home, away, odds, result, stake):
    """Append a new match row to the matches sheet."""
    ws = get_matches_worksheet()
    new_row = [date, competition, home, away, odds, result, stake, 0]
    ws.append_row(new_row)


def update_match_result(row, result):
    """Update the result column for a specific match row."""
    ws = get_matches_worksheet()
    ws.update_cell(row, RESULT_COL, result)


def update_match(row, date, home, away, odds, result, stake):
    """Update all fields of a match row."""
    ws = get_matches_worksheet()
    ws.update_cell(row, 1, date)
    ws.update_cell(row, 3, home)
    ws.update_cell(row, 4, away)
    ws.update_cell(row, 5, odds)
    ws.update_cell(row, 6, result)
    ws.update_cell(row, 7, stake)


def delete_match(row):
    """Delete a match row from the sheet."""
    ws = get_matches_worksheet()
    ws.delete_rows(row)


def add_competition(name, description, default_stake, color1, color2, text_color, logo_url):
    """Add a new competition to the Competitions sheet."""
    ws = get_competitions_worksheet()
    import datetime
    new_row = [
        name, description, default_stake,
        color1, color2, text_color,
        logo_url, "Active",
        str(datetime.date.today()), ""
    ]
    ws.append_row(new_row)


def update_competition_stake(row, new_stake):
    """Update the default stake for a competition."""
    ws = get_competitions_worksheet()
    ws.update_cell(row, 3, new_stake)


def close_competition(row):
    """Close a competition (set status to Closed + add closed date)."""
    import datetime
    ws = get_competitions_worksheet()
    ws.update_cell(row, 8, "Closed")
    ws.update_cell(row, 10, str(datetime.date.today()))
