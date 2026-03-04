"""Data processing module for Elite Football Tracker.
Handles competition dict building and martingale betting cycle logic.
"""
import pandas as pd

DEFAULT_STAKE = 30.0


def build_competitions_dict(competitions_data):
    """Build a dictionary of competitions with their settings."""
    comps = {}
    for comp in competitions_data:
        name = comp.get('Name', '').strip()
        if not name:
            continue

        color1 = comp.get('Color1', '#4CABFF').strip() or '#4CABFF'
        color2 = comp.get('Color2', '#E6F7FF').strip() or '#E6F7FF'
        text_color = comp.get('Text_Color', '#004085').strip() or '#004085'
        gradient = f"linear-gradient(135deg, {color1} 0%, {color2} 100%)"

        try:
            default_stake = float(str(comp.get('Default_Stake', DEFAULT_STAKE)).replace(',', '.'))
        except (ValueError, TypeError):
            default_stake = DEFAULT_STAKE

        comps[name] = {
            'name': name,
            'description': comp.get('Description', ''),
            'default_stake': default_stake,
            'color1': color1,
            'color2': color2,
            'text_color': text_color,
            'gradient': gradient,
            'logo': comp.get('Logo_URL', ''),
            'status': comp.get('Status', 'Active').strip(),
            'created_date': comp.get('Created_Date', ''),
            'closed_date': comp.get('Closed_Date', ''),
            'row': competitions_data.index(comp) + 2  # +2 for header and 0-index
        }

    return comps


def process_data(raw, competitions_dict):
    """Process raw match data and calculate betting cycles (martingale).

    Returns: (DataFrame, next_bets dict, competition_stats dict, pending_losses float)
    """
    if not raw:
        empty_stats = {
            name: {"total_staked": 0, "total_income": 0, "net_profit": 0}
            for name in competitions_dict
        }
        next_bets = {
            name: competitions_dict[name]['default_stake']
            for name in competitions_dict
        }
        return pd.DataFrame(), next_bets, empty_stats, 0.0

    processed = []
    cycle_investment = {name: 0.0 for name in competitions_dict}
    next_bets = {name: competitions_dict[name]['default_stake'] for name in competitions_dict}
    comp_stats = {
        name: {"total_staked": 0.0, "total_income": 0.0, "net_profit": 0.0}
        for name in competitions_dict
    }

    for i, row in enumerate(raw):
        if not isinstance(row, dict):
            continue

        comp = str(row.get('Competition', '')).strip()
        if comp not in competitions_dict:
            continue

        comp_info = competitions_dict[comp]
        home = str(row.get('Home Team', '')).strip()
        away = str(row.get('Away Team', '')).strip()
        match_name = f"{home} vs {away}" if home and away else "Unknown Match"

        try:
            odds = float(str(row.get('Odds', '1')).replace(',', '.').strip())
            if odds <= 0:
                odds = 1.0
        except (ValueError, TypeError):
            odds = 1.0

        try:
            stake_str = str(row.get('Stake', '')).replace(',', '.').replace('₪', '').strip()
            stake = float(stake_str) if stake_str else 0.0
        except (ValueError, TypeError):
            stake = 0.0

        if stake == 0:
            stake = next_bets.get(comp, comp_info['default_stake'])

        result = str(row.get('Result', '')).strip()
        date = str(row.get('Date', '')).strip()

        if result == "Pending" or result == "" or not result:
            processed.append({
                "Row": i + 2,
                "Comp": comp,
                "Match": match_name,
                "Home": home,
                "Away": away,
                "Date": date,
                "Profit": 0,
                "Status": "Pending",
                "Stake": stake,
                "Odds": odds,
                "Income": 0,
                "Expense": stake
            })
            continue

        cycle_investment[comp] += stake
        comp_stats[comp]["total_staked"] += stake

        result_lower = result.lower().strip()
        is_win = (result == "Draw (X)" or result_lower == "draw" or result_lower == "draw (x)")
        if "no draw" in result_lower or "no_draw" in result_lower:
            is_win = False

        if is_win:
            income = stake * odds
            net_profit = income - cycle_investment[comp]
            comp_stats[comp]["total_income"] += income
            comp_stats[comp]["net_profit"] += net_profit
            cycle_investment[comp] = 0.0
            next_bets[comp] = comp_info['default_stake']
            status = "Won"
        else:
            income = 0.0
            net_profit = 0
            next_bets[comp] = stake * 2.0
            status = "Lost"

        processed.append({
            "Row": i + 2,
            "Comp": comp,
            "Match": match_name,
            "Home": home,
            "Away": away,
            "Date": date,
            "Profit": net_profit,
            "Status": status,
            "Stake": stake,
            "Odds": odds,
            "Income": income,
            "Expense": stake
        })

    pending_losses = sum(cycle_investment.values())
    return pd.DataFrame(processed), next_bets, comp_stats, pending_losses
