"""
build_stocks_by_date.py

State read:
    transactions.json, prices_dates.json, mkt_dates.json

Transition logic:
    For each market date:
        1. carry forward prior positions
        2. apply splits for that date
        3. apply stock transactions (buy/sell) for that date
        4. store snapshot

Invariant:
    stocks_by_date[d] reflects all buys, sells, and splits through date d;
    average_cost is the share-weighted average of all purchase prices,
    adjusted downward by any splits
"""

import json
from pathlib import Path

# ── paths ──────────────────────────────────────────────────────────────────────
LAB_ROOT             = Path(__file__).parent.parent.parent.parent
TRANSACTIONS_FILE    = LAB_ROOT / "data/system/transactions/transactions.json"
PRICES_DATES_FILE    = LAB_ROOT / "data/system/prices_dates.json"
MKT_DATES_FILE       = LAB_ROOT / "data/system/mkt_dates.json"
STOCKS_BY_DATE_FILE  = LAB_ROOT / "data/system/positions_by_date/stocks_by_date.json"


# ── file helpers ───────────────────────────────────────────────────────────────

def load_json(path):
    with open(path, "r") as f:
        return json.load(f)


def save_json(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=4)


# ── group helpers ──────────────────────────────────────────────────────────────

def group_transactions_by_date(transactions):
    """
    Return {date: [tx, ...]} for buy/sell transactions only.
    Contribution and withdrawal records are excluded (cash-only events).
    The cash ticker '$$$$' is also excluded.
    """
    result = {}
    for tx in transactions:
        if tx["type"] not in ("buy", "sell"):
            continue
        if tx.get("ticker") == "$$$$":
            continue
        result.setdefault(tx["date"], []).append(tx)
    return result


def build_split_lookup(prices_by_date):
    """
    Return {date: {ticker: split_factor}} for every date that has a split.
    split_factor = shares_out / shares_in  (e.g., 2.0 for a 2-for-1 split).
    """
    result = {}
    for date, entries in prices_by_date.items():
        for entry in entries:
            if entry["shares_in"] != entry["shares_out"]:
                factor = entry["shares_out"] / entry["shares_in"]
                result.setdefault(date, {})[entry["ticker"]] = factor
    return result


# ── position update helpers ────────────────────────────────────────────────────

def apply_split(position, split_factor):
    """
    Return a new position dict after applying a split.
    Shares multiply by split_factor; average_cost divides by split_factor
    so total cost basis is preserved.
    """
    return {
        "shares":   position["shares"] * split_factor,
        "avg_cost": position["avg_cost"] / split_factor,
    }


def apply_transaction(positions, tx):
    """
    Apply one buy or sell transaction to the positions dict in place.

    Buy:  increase shares; recalculate average cost using weighted average.
    Sell: decrease shares; average cost is unchanged.
          If shares reach zero, the position is removed.

    Crossing-zero rule: selling more shares than held is not validated here;
    the caller is responsible for ensuring the ledger is clean.
    """
    ticker = tx["ticker"]
    shares = tx["shares"]
    price  = tx["price"]

    if tx["type"] == "buy":
        if ticker not in positions:
            positions[ticker] = {"shares": 0.0, "avg_cost": 0.0}
        old_shares = positions[ticker]["shares"]
        old_cost   = positions[ticker]["avg_cost"]
        new_shares = old_shares + shares
        if new_shares > 0:
            new_avg_cost = (old_shares * old_cost + shares * price) / new_shares
        else:
            new_avg_cost = 0.0
        positions[ticker] = {"shares": new_shares, "avg_cost": new_avg_cost}

    elif tx["type"] == "sell":
        if ticker in positions:
            positions[ticker]["shares"] -= shares
            if positions[ticker]["shares"] <= 1e-9:
                del positions[ticker]

    return positions


# ── snapshot helper ────────────────────────────────────────────────────────────

def make_snapshot(positions):
    """
    Convert {ticker: {shares, avg_cost}} to a sorted list of
    {ticker, shares, average_cost} dicts. Zero positions are excluded.
    """
    return [
        {
            "ticker":       ticker,
            "shares":       pos["shares"],
            "average_cost": round(pos["avg_cost"], 6),
        }
        for ticker, pos in sorted(positions.items())
        if pos["shares"] > 1e-9
    ]


# ── main builder ───────────────────────────────────────────────────────────────

def build_stocks_by_date():
    """
    Rebuild stocks_by_date.json from scratch using transactions and price data.

    State read:    transactions.json, prices_dates.json, mkt_dates.json
    Transition:    for each market date: carry forward → splits → trades → snapshot
    Invariant:     stocks_by_date[d] reflects all activity through date d
    """
    transactions   = load_json(TRANSACTIONS_FILE) if TRANSACTIONS_FILE.exists() else []
    prices_by_date = load_json(PRICES_DATES_FILE)
    mkt_dates      = load_json(MKT_DATES_FILE)

    stock_txns_by_date = group_transactions_by_date(transactions)
    split_lookup       = build_split_lookup(prices_by_date)

    positions      = {}
    stocks_by_date = {}

    for date in mkt_dates:
        # 1. carry forward — work on a fresh copy so prior snapshot is unaffected
        positions = {ticker: dict(pos) for ticker, pos in positions.items()}

        # 2. apply splits for this date
        for ticker, factor in split_lookup.get(date, {}).items():
            if ticker in positions:
                positions[ticker] = apply_split(positions[ticker], factor)

        # 3. apply stock transactions for this date
        for tx in stock_txns_by_date.get(date, []):
            apply_transaction(positions, tx)

        # 4. store snapshot
        stocks_by_date[date] = make_snapshot(positions)

    save_json(STOCKS_BY_DATE_FILE, stocks_by_date)
    print(f"  Built stocks_by_date for {len(stocks_by_date)} dates.")
    return stocks_by_date


if __name__ == "__main__":
    build_stocks_by_date()
