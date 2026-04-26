# build_stocks_by_date.py
#
# Reads:
#   functions/transactions.json    — [{date, type, ticker, shares, price, ...}]
#   functions/prices_dates.json    — {date: [{ticker, raw_price, shares_in, shares_out, dividend}]}
#   functions/mkt_dates.json       — [date_str, ...]  sorted ascending
#
# Writes:
#   functions/stocks_by_date.json  — {date: [{ticker, shares, average_cost}]}
#
# For each market date:
# 1. carry forward prior positions
# 2. apply splits for that date
# 3. apply stock transactions for that date
# 4. store snapshot
#
# Invariants:
#   - stocks_by_date[d] reflects all buys, sells, and splits through date d
#   - average_cost is the share-weighted average of all purchase prices,
#     adjusted downward by any splits
#   - zero (or negative) share positions are removed from the snapshot
#   - output rows are sorted by ticker

import json
from pathlib import Path

# ── paths ──────────────────────────────────────────────────────────────────────

SCRIPT_DIR          = Path(__file__).parent
FUNCTIONS           = SCRIPT_DIR / "functions"

TRANSACTIONS_FILE   = FUNCTIONS / "transactions.json"
PRICES_DATES_FILE   = FUNCTIONS / "prices_dates.json"
MKT_DATES_FILE      = FUNCTIONS / "mkt_dates.json"
STOCKS_BY_DATE_FILE = FUNCTIONS / "stocks_by_date.json"

# ── loaders ────────────────────────────────────────────────────────────────────

def load_json(path):
    with open(path, "r") as f:
        return json.load(f)

# ── groupers ───────────────────────────────────────────────────────────────────

def group_transactions_by_date(transactions, mkt_date_set):
    """
    Index buy/sell transactions by date.
    Skips any transaction whose date is not in mkt_date_set (silent skip).
    Skips any transaction whose type is not 'buy' or 'sell'.
    Returns {date: [tx, ...]}
    """
    by_date = {}
    for tx in transactions:
        if tx["date"] not in mkt_date_set:
            continue
        if tx.get("type", "").lower() not in ("buy", "sell"):
            continue
        by_date.setdefault(tx["date"], []).append(tx)
    return by_date


def build_split_lookup(prices_dates):
    """
    Build a lookup of real splits only (shares_in != shares_out).
    Skips records where shares_in or shares_out is zero.
    Returns {date: {ticker: {shares_in, shares_out}}}
    """
    lookup = {}
    for date, records in prices_dates.items():
        for record in records:
            shares_in  = record.get("shares_in",  1)
            shares_out = record.get("shares_out", 1)
            if shares_in == 0 or shares_out == 0:
                continue
            if shares_in == shares_out:
                continue
            ticker = record["ticker"]
            lookup.setdefault(date, {})[ticker] = {
                "shares_in":  shares_in,
                "shares_out": shares_out,
            }
    return lookup

# ── position mutators ──────────────────────────────────────────────────────────

def apply_split(position, split_record):
    """
    Apply a split to a single position in place.
    factor        = shares_out / shares_in
    new shares    = old shares * factor
    new avg cost  = old avg cost / factor

    position:     {"shares": float, "average_cost": float}
    split_record: {"shares_in": float, "shares_out": float}
    """
    factor                   = split_record["shares_out"] / split_record["shares_in"]
    position["shares"]       = position["shares"] * factor
    position["average_cost"] = position["average_cost"] / factor


def apply_transaction(position, tx):
    """
    Apply a single buy or sell transaction to a position in place.

    Buy:
        new_shares    = old_shares + tx_shares
        new_avg_cost  = (old_shares * old_avg + tx_shares * tx_price) / new_shares

    Sell (partial or full):
        new_shares    = old_shares - tx_shares
        average_cost  unchanged

    Crossing-zero rule:
        A sell that would push shares below zero is applied as-is.
        The position will be caught and removed by the zero-position filter
        in make_snapshot(). This should not occur with clean transaction data.

    position: {"shares": float, "average_cost": float}  (mutated in place)
    tx:       {"type": str, "shares": float, "price": float}
    """
    tx_type   = tx["type"].lower()
    tx_shares = float(tx["shares"])
    tx_price  = float(tx["price"])

    if tx_type == "buy":
        old_shares               = position["shares"]
        old_avg                  = position["average_cost"]
        new_shares               = old_shares + tx_shares
        position["shares"]       = new_shares
        position["average_cost"] = (old_shares * old_avg + tx_shares * tx_price) / new_shares

    elif tx_type == "sell":
        position["shares"] -= tx_shares
        # average_cost is unchanged on a sell

# ── snapshot ───────────────────────────────────────────────────────────────────

def make_snapshot(positions):
    """
    Return a sorted list of position dicts for storage.
    Excludes any ticker with zero or negative shares.
    Output rows are sorted by ticker.

    positions: {ticker: {"shares": float, "average_cost": float}}
    Returns:   [{ticker, shares, average_cost}, ...]
    """
    return [
        {
            "ticker":       ticker,
            "shares":       positions[ticker]["shares"],
            "average_cost": positions[ticker]["average_cost"],
        }
        for ticker in sorted(positions)
        if positions[ticker]["shares"] > 0
    ]

# ── main ───────────────────────────────────────────────────────────────────────

def build_stocks_by_date():
    mkt_dates    = load_json(MKT_DATES_FILE)
    prices_dates = load_json(PRICES_DATES_FILE)
    transactions = load_json(TRANSACTIONS_FILE)

    mkt_date_set  = set(mkt_dates)
    txns_by_date  = group_transactions_by_date(transactions, mkt_date_set)
    split_lookup  = build_split_lookup(prices_dates)

    # find first market date that has a buy transaction
    buy_dates      = sorted(d for d in txns_by_date if any(
        t["type"].lower() == "buy" for t in txns_by_date[d]
    ))
    first_buy_date = buy_dates[0] if buy_dates else None

    stocks_by_date = {}
    # positions: {ticker: {"shares": float, "average_cost": float}}
    positions = {}

    for date in mkt_dates:

        # dates before first buy → empty snapshot, no processing
        if first_buy_date is None or date < first_buy_date:
            stocks_by_date[date] = []
            continue

        # 1. carry forward prior positions (deep copy to avoid mutation across dates)
        positions = {ticker: dict(pos) for ticker, pos in positions.items()}

        # 2. apply splits for this date
        splits_today = split_lookup.get(date, {})
        for ticker, split_record in splits_today.items():
            if ticker in positions:
                apply_split(positions[ticker], split_record)

        # 3. apply stock transactions for this date
        for tx in txns_by_date.get(date, []):
            ticker = tx["ticker"]
            if tx["type"].lower() == "buy" and ticker not in positions:
                # opening a new position
                positions[ticker] = {"shares": 0.0, "average_cost": 0.0}
            if ticker in positions:
                apply_transaction(positions[ticker], tx)

        # 4. store snapshot (removes zero/negative positions)
        stocks_by_date[date] = make_snapshot(positions)

        # keep positions dict in sync with snapshot (drop zeroes)
        positions = {
            ticker: positions[ticker]
            for ticker in positions
            if positions[ticker]["shares"] > 0
        }

    # write output
    FUNCTIONS.mkdir(parents=True, exist_ok=True)
    with open(STOCKS_BY_DATE_FILE, "w") as f:
        json.dump(stocks_by_date, f, indent=2)

    print(f"Wrote {len(stocks_by_date)} dates to {STOCKS_BY_DATE_FILE}")


if __name__ == "__main__":
    build_stocks_by_date()