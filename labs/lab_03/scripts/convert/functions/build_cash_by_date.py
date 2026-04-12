"""
build_cash_by_date.py

State read:
    transactions.json, prices_dates.json, mkt_dates.json, stocks_by_date.json

Transition logic:
    For each market date:
        cash = prior_cash
        cash += transaction_cash_flow   (contributions, withdrawals, buys, sells)
        cash += dividend_cash_flow      (per-share dividends × shares held)

    Dividend ordering rule:
        Dividends on date d are applied using the stock positions at the START
        of date d (i.e., the snapshot from the prior market date).
        This follows standard ex-dividend date logic: you earn the dividend
        if you held the shares before the dividend date.

    Round only at storage, not at every intermediate step, to avoid drift.

Invariant:
    cash_by_date[d] equals the cumulative cash balance through date d,
    including all contributions, withdrawals, trade settlements, and dividends
"""

import json
from pathlib import Path
from build_stocks_by_date import build_stocks_by_date

# ── paths ──────────────────────────────────────────────────────────────────────
LAB_ROOT            = Path(__file__).parent.parent.parent.parent
TRANSACTIONS_FILE   = LAB_ROOT / "data/system/transactions/transactions.json"
PRICES_DATES_FILE   = LAB_ROOT / "data/system/prices_dates.json"
MKT_DATES_FILE      = LAB_ROOT / "data/system/mkt_dates.json"
STOCKS_BY_DATE_FILE = LAB_ROOT / "data/system/positions_by_date/stocks_by_date.json"
CASH_BY_DATE_FILE   = LAB_ROOT / "data/system/positions_by_date/cash_by_date.json"


# ── file helpers ───────────────────────────────────────────────────────────────

def load_json(path):
    with open(path, "r") as f:
        return json.load(f)


def save_json(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=4)


# ── group helper ───────────────────────────────────────────────────────────────

def group_transactions_by_date(transactions):
    """Return {date: [tx, ...]} for all transaction types."""
    result = {}
    for tx in transactions:
        result.setdefault(tx["date"], []).append(tx)
    return result


# ── daily flow helpers ─────────────────────────────────────────────────────────

def get_transaction_cash_flow_for_date(day_transactions):
    """
    Return the net cash change from all transactions on one date.

    contribution: +shares * price  (shares field holds dollar amount when price=1)
    withdrawal:   -shares * price
    buy:          -shares * price
    sell:         +shares * price
    """
    flow = 0.0
    for tx in day_transactions:
        tx_type = tx["type"]
        if tx_type == "contribution":
            flow += tx.get("shares", tx.get("amount", 0)) * tx.get("price", 1.0)
        elif tx_type == "withdrawal":
            flow -= tx.get("shares", tx.get("amount", 0)) * tx.get("price", 1.0)
        elif tx_type == "buy":
            flow -= tx["shares"] * tx["price"]
        elif tx_type == "sell":
            flow += tx["shares"] * tx["price"]
    return flow


def build_position_lookup_for_date(stocks_by_date, date, mkt_dates):
    """
    Return {ticker: shares} for positions held at the START of date
    (prior market date's snapshot).
    Returns an empty dict for the first market date.
    """
    idx = mkt_dates.index(date)
    if idx == 0:
        return {}
    prior_date = mkt_dates[idx - 1]
    return {pos["ticker"]: pos["shares"] for pos in stocks_by_date.get(prior_date, [])}


def get_dividend_cash_flow_for_date(day_prices, position_lookup):
    """
    Return total dividend income for one date.
    For each ticker with a dividend > 0, earn: shares_held × dividend_per_share.
    """
    flow = 0.0
    for entry in day_prices:
        if entry["dividend"] > 0:
            shares_held = position_lookup.get(entry["ticker"], 0.0)
            flow += shares_held * entry["dividend"]
    return flow


# ── main builder ───────────────────────────────────────────────────────────────

def build_cash_by_date():
    """
    Rebuild cash_by_date.json from scratch.

    Calls build_stocks_by_date() first so dividend calculations use
    up-to-date share counts.

    State read:    transactions.json, prices_dates.json, mkt_dates.json,
                   stocks_by_date.json (rebuilt fresh before use)
    Transition:    cash += transaction_flow + dividend_flow for each market date
    Invariant:     cash_by_date[d] equals cumulative cash through date d
    """
    stocks_by_date = build_stocks_by_date()

    transactions   = load_json(TRANSACTIONS_FILE) if TRANSACTIONS_FILE.exists() else []
    prices_by_date = load_json(PRICES_DATES_FILE)
    mkt_dates      = load_json(MKT_DATES_FILE)

    txns_by_date  = group_transactions_by_date(transactions)
    cash          = 0.0
    cash_by_date  = {}

    for date in mkt_dates:
        cash += get_transaction_cash_flow_for_date(txns_by_date.get(date, []))

        prior_positions = build_position_lookup_for_date(stocks_by_date, date, mkt_dates)
        cash += get_dividend_cash_flow_for_date(
            prices_by_date.get(date, []), prior_positions
        )

        cash_by_date[date] = round(cash, 2)

    save_json(CASH_BY_DATE_FILE, cash_by_date)
    print(f"  Built cash_by_date for {len(cash_by_date)} dates.")
    return cash_by_date


if __name__ == "__main__":
    build_cash_by_date()
