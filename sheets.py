"""Google Sheets CRUD module for Elite Football Tracker."""
import os
import json
import functools
import threading
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


# --- CONNECTION CACHE ---
# Authorising and opening the spreadsheet costs ~16s (OAuth token exchange +
# metadata fetch), while the actual value reads cost ~1s. Rebuilding it on every
# request was what made pages take 16-25s and hit gunicorn's request timeout, so
# the handles are built once and reused for the process lifetime.
_conn = {"spreadsheet": None, "matches_ws": None, "competitions_ws": None}

# The cached handles share one requests.Session, which isn't thread-safe, and the
# server runs with threads. Re-entrant because the helpers below nest.
_api_lock = threading.RLock()


def reset_connection():
    """Drop the cached handles so the next call re-authenticates from scratch."""
    with _api_lock:
        for key in _conn:
            _conn[key] = None


def sheet_write(fn):
    """Wrap a write op: serialise it against other Sheets access, and make sure a
    stale cached connection can't wedge the app.

    On failure the connection is dropped (the next attempt reconnects) and the
    error is re-raised. Deliberately never auto-retries: a write that failed
    part-way through would otherwise be applied twice.
    """
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        with _api_lock:
            try:
                return fn(*args, **kwargs)
            except Exception:
                reset_connection()
                raise
    return wrapper


def get_spreadsheet():
    """Get authorized spreadsheet connection (cached)."""
    with _api_lock:
        if _conn["spreadsheet"] is None:
            creds = get_credentials()
            gc = gspread.authorize(creds)
            _conn["spreadsheet"] = gc.open_by_key(get_sheet_id())
        return _conn["spreadsheet"]


def get_matches_worksheet():
    """Get matches worksheet (first sheet), cached."""
    with _api_lock:
        if _conn["matches_ws"] is None:
            _conn["matches_ws"] = get_spreadsheet().get_worksheet(MATCHES_SHEET)
        return _conn["matches_ws"]


def get_competitions_worksheet():
    """Get competitions worksheet, cached."""
    with _api_lock:
        if _conn["competitions_ws"] is None:
            _conn["competitions_ws"] = get_spreadsheet().worksheet(COMPETITIONS_SHEET)
        return _conn["competitions_ws"]


# --- READ OPERATIONS ---

def _rows_to_dicts(values):
    """Turn raw sheet values into dicts keyed by the header row."""
    if len(values) < 2:
        return []
    headers = [h.strip() for h in values[0]]
    return [
        dict(zip(headers, row))
        for row in values[1:]
        if any(cell.strip() for cell in row)
    ]


def _read_bankroll(raw_values, matches_ws):
    """Read the bankroll. It sits in the matches header row, so it normally
    comes back with the values already fetched — no extra round-trip."""
    try:
        header = raw_values[BANKROLL_CELL_ROW - 1] if raw_values else []
        val = header[BANKROLL_CELL_COL - 1] if len(header) >= BANKROLL_CELL_COL else ""
        if not str(val).strip():
            val = matches_ws.cell(BANKROLL_CELL_ROW, BANKROLL_CELL_COL).value
        if not val:
            return DEFAULT_BANKROLL
        return float(str(val).replace(',', '').replace('₪', '').strip())
    except Exception:
        return DEFAULT_BANKROLL


def get_all_data():
    """Read all data from Google Sheets. Returns (matches_data, bankroll, competitions_data, error).

    A read failure is reported as an error rather than swallowed, so a transient
    Sheets outage shows a banner instead of an empty dashboard that looks like
    the data was lost.
    """
    with _api_lock:
        try:
            matches_ws = get_matches_worksheet()
            raw_values = matches_ws.get_all_values()
            comp_values = get_competitions_worksheet().get_all_values()
            bankroll = _read_bankroll(raw_values, matches_ws)
        except Exception as e:
            reset_connection()
            return [], DEFAULT_BANKROLL, [], str(e)

    return (
        _rows_to_dicts(raw_values),
        bankroll,
        _rows_to_dicts(comp_values),
        None,
    )


# --- WRITE OPERATIONS ---

@sheet_write
def update_bankroll(new_amount):
    """Update bankroll cell value."""
    ws = get_matches_worksheet()
    ws.update_cell(BANKROLL_CELL_ROW, BANKROLL_CELL_COL, new_amount)


@sheet_write
def add_match(date, competition, home, away, odds, result, stake):
    """Append a new match row to the matches sheet."""
    ws = get_matches_worksheet()
    new_row = [date, competition, home, away, odds, result, stake, 0]
    ws.append_row(new_row)


@sheet_write
def update_match_result(row, result):
    """Update the result column for a specific match row."""
    ws = get_matches_worksheet()
    ws.update_cell(row, RESULT_COL, result)


@sheet_write
def update_match(row, date, home, away, odds, result, stake):
    """Update all editable fields of a match row in one request.

    Column B (Competition) is deliberately left untouched — the ranges skip it.
    """
    ws = get_matches_worksheet()
    ws.batch_update([
        {"range": f"A{row}", "values": [[date]]},
        {"range": f"C{row}:G{row}", "values": [[home, away, odds, result, stake]]},
    ])


@sheet_write
def delete_match(row):
    """Delete a match row from the sheet."""
    ws = get_matches_worksheet()
    ws.delete_rows(row)


@sheet_write
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


@sheet_write
def update_competition_stake(row, new_stake):
    """Update the default stake for a competition."""
    ws = get_competitions_worksheet()
    ws.update_cell(row, 3, new_stake)


@sheet_write
def close_competition(row):
    """Close a competition (set status to Closed + add closed date)."""
    import datetime
    ws = get_competitions_worksheet()
    ws.batch_update([
        {"range": f"H{row}", "values": [["Closed"]]},
        {"range": f"J{row}", "values": [[str(datetime.date.today())]]},
    ])
