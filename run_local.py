"""
Local runner for Elite Football Tracker (Flask version).

SETUP:
1. Create a file called 'credentials.json' in this directory
   with your Google service account JSON key.
   (Download from Google Cloud Console → IAM → Service Accounts → Keys)

2. Set your Google Sheet ID below:
"""
import os
import json

# ============================================
# EDIT THIS: Your Google Sheet ID
# (the part between /d/ and /edit in the Sheet URL)
# ============================================
SHEET_ID = "1pOdsQYcINhjSaSKssRx1VZlKYoqJg2n_oq6-ce7vSck"

# ============================================
# DO NOT EDIT BELOW THIS LINE
# ============================================

# Load credentials from credentials.json file
creds_file = os.path.join(os.path.dirname(__file__), "credentials.json")
if os.path.exists(creds_file):
    with open(creds_file, "r") as f:
        creds = json.load(f)
    os.environ["GOOGLE_CREDENTIALS"] = json.dumps(creds)
    print(f"[OK] Loaded credentials from {creds_file}")
    print(f"[OK] Service account: {creds.get('client_email', 'unknown')}")
else:
    print(f"[ERROR] credentials.json not found!")
    print(f"        Create it at: {creds_file}")
    print(f"        Download from: Google Cloud Console > IAM > Service Accounts > Keys")
    exit(1)

os.environ["SHEET_ID"] = SHEET_ID
if SHEET_ID == "PUT_YOUR_SHEET_ID_HERE":
    print("[ERROR] You need to set your SHEET_ID in this file!")
    print("        Open run_local.py and replace PUT_YOUR_SHEET_ID_HERE")
    exit(1)

print(f"[OK] Sheet ID: {SHEET_ID[:10]}...")
print(f"[OK] Starting Flask app on http://localhost:5000")
print()

from flask_app import app
app.run(debug=True, port=5000, host="0.0.0.0")
