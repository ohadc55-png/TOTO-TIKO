"""Elite Football Tracker — Flask Application."""
import datetime
import os
import time
from flask import Flask, render_template, request, jsonify, redirect, url_for

from sheets import (
    get_all_data, update_bankroll, add_match, update_match_result,
    update_match, delete_match, add_competition, update_competition_stake,
    close_competition, DEFAULT_BANKROLL
)
from data import build_competitions_dict, process_data

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-prod")


@app.template_filter('money')
def money_filter(value, decimals=0):
    """Format number as money with commas. Usage: {{ val|money }} or {{ val|money(2) }}"""
    try:
        val = float(value)
        if decimals > 0:
            return f"{val:,.{decimals}f}"
        return f"{val:,.0f}"
    except (ValueError, TypeError):
        return str(value)

APP_LOGO_URL = "https://i.postimg.cc/8Cr6SypK/yzwb-ll-sm.png"

# --- CACHE ---
_cache = {"data": None, "timestamp": 0}
CACHE_TTL = 30  # seconds

def invalidate_cache():
    """Call after any write operation to force fresh data on next load."""
    _cache["timestamp"] = 0

def load_app_data():
    """Load and process all application data from Google Sheets (cached)."""
    now = time.time()
    if _cache["data"] is not None and (now - _cache["timestamp"]) < CACHE_TTL:
        return _cache["data"]

    matches_data, bankroll, competitions_data, error = get_all_data()

    if error:
        return {
            "error": error,
            "bankroll": DEFAULT_BANKROLL,
            "current_bal": DEFAULT_BANKROLL,
            "active_competitions": {},
            "archived_competitions": {},
            "df": None,
            "next_bets": {},
            "competition_stats": {},
            "logo": APP_LOGO_URL,
        }

    competitions_dict = build_competitions_dict(competitions_data)
    df, next_bets, competition_stats, pending_losses = process_data(matches_data, competitions_dict)

    active = {k: v for k, v in competitions_dict.items() if v['status'] == 'Active'}
    archived = {k: v for k, v in competitions_dict.items() if v['status'] == 'Closed'}

    # Calculate total profits across all competitions
    total_profits = sum(s['net_profit'] for s in competition_stats.values())
    current_bal = bankroll + total_profits - pending_losses

    result = {
        "error": None,
        "bankroll": bankroll,
        "current_bal": current_bal,
        "active_competitions": active,
        "archived_competitions": archived,
        "df": df,
        "next_bets": next_bets,
        "competition_stats": competition_stats,
        "logo": APP_LOGO_URL,
    }
    _cache["data"] = result
    _cache["timestamp"] = time.time()
    return result


# --- PAGE ROUTES ---

@app.route("/")
def overview():
    data = load_app_data()
    if data["error"]:
        return render_template("overview.html", **data)

    # Calculate per-competition profits for overview cards
    comp_profits = {}
    if data["df"] is not None and not data["df"].empty:
        for comp_name in data["active_competitions"]:
            comp_df = data["df"][data["df"]["Comp"] == comp_name]
            comp_profits[comp_name] = comp_df["Profit"].sum() if not comp_df.empty else 0
    else:
        for comp_name in data["active_competitions"]:
            comp_profits[comp_name] = 0

    return render_template("overview.html", comp_profits=comp_profits, **data)


@app.route("/competition/<name>")
def competition(name):
    data = load_app_data()
    if name not in data["active_competitions"]:
        return redirect(url_for("overview"))

    comp_info = data["active_competitions"][name]
    stats = data["competition_stats"].get(name, {"total_staked": 0, "total_income": 0, "net_profit": 0})
    next_bet = data["next_bets"].get(name, comp_info["default_stake"])

    matches = []
    if data["df"] is not None and not data["df"].empty:
        comp_df = data["df"][data["df"]["Comp"] == name]
        matches = comp_df.sort_index(ascending=False).to_dict("records")

    return render_template(
        "competition.html",
        comp_name=name,
        comp_info=comp_info,
        stats=stats,
        next_bet=next_bet,
        matches=matches,
        **data,
    )


@app.route("/new-competition")
def new_competition():
    data = load_app_data()
    return render_template("new_competition.html", **data)


@app.route("/archive")
def archive():
    data = load_app_data()
    archive_profits = {}
    if data["df"] is not None and not data["df"].empty:
        for comp_name in data["archived_competitions"]:
            comp_df = data["df"][data["df"]["Comp"] == comp_name]
            archive_profits[comp_name] = comp_df["Profit"].sum() if not comp_df.empty else 0
    else:
        for comp_name in data["archived_competitions"]:
            archive_profits[comp_name] = 0

    return render_template("archive.html", archive_profits=archive_profits, **data)


@app.route("/manage")
def manage():
    data = load_app_data()
    return render_template("manage.html", **data)


# --- API ENDPOINTS ---

@app.route("/api/match", methods=["POST"])
def api_add_match():
    """Add a new match."""
    d = request.json
    try:
        add_match(
            d.get("date", str(datetime.date.today())),
            d["competition"],
            d["home"],
            d["away"],
            d["odds"],
            d.get("result", "Pending"),
            d["stake"],
        )
        invalidate_cache()
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/match/<int:row>/result", methods=["POST"])
def api_update_result(row):
    """Update match result (win/loss)."""
    d = request.json
    try:
        update_match_result(row, d["result"])
        invalidate_cache()
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/match/<int:row>/edit", methods=["POST"])
def api_edit_match(row):
    """Edit match data."""
    d = request.json
    try:
        update_match(row, d["date"], d["home"], d["away"], d["odds"], d["result"], d["stake"])
        invalidate_cache()
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/match/<int:row>/delete", methods=["POST"])
def api_delete_match(row):
    """Delete a match."""
    try:
        delete_match(row)
        invalidate_cache()
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/bankroll/deposit", methods=["POST"])
def api_deposit():
    """Deposit to bankroll."""
    d = request.json
    try:
        data = load_app_data()
        new_amount = data["bankroll"] + float(d["amount"])
        update_bankroll(new_amount)
        invalidate_cache()
        return jsonify({"ok": True, "new_bankroll": new_amount})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/bankroll/withdraw", methods=["POST"])
def api_withdraw():
    """Withdraw from bankroll."""
    d = request.json
    try:
        data = load_app_data()
        new_amount = data["bankroll"] - float(d["amount"])
        update_bankroll(new_amount)
        invalidate_cache()
        return jsonify({"ok": True, "new_bankroll": new_amount})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/competition", methods=["POST"])
def api_create_competition():
    """Create a new competition."""
    d = request.json
    try:
        add_competition(
            d["name"],
            d.get("description", ""),
            d.get("default_stake", 30.0),
            d.get("color1", "#4CABFF"),
            d.get("color2", "#E6F7FF"),
            d.get("text_color", "#004085"),
            d.get("logo_url", ""),
        )
        invalidate_cache()
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/competition/<int:row>/stake", methods=["POST"])
def api_update_stake(row):
    """Update competition default stake."""
    d = request.json
    try:
        update_competition_stake(row, d["stake"])
        invalidate_cache()
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/competition/<int:row>/close", methods=["POST"])
def api_close_competition(row):
    """Close a competition."""
    try:
        close_competition(row)
        invalidate_cache()
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)
