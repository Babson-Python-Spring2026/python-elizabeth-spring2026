# build_portfolio_by_date.py
#
# Reads:
#   functions/stocks_by_date.json  — {date: [{ticker, shares, average_cost}]}
#   functions/cash_by_date.json    — {date: float}
#   functions/prices_dates.json    — {date: [{ticker, raw_price, ...}]}
#   functions/mkt_dates.json       — [date_str, ...]
#
# Writes:
#   functions/portfolio_by_date.json — {date: [rows]}
#
# Row shape (stocks):
#   {ticker, shares, average_cost, mkt_price, total_avg_cost, total_mkt_value}
#
# Row shape (cash):
#   {ticker: "$$$$", shares: cash_balance, average_cost: 1.0,
#    mkt_price: 1.0, total_avg_cost: cash_balance, total_mkt_value: cash_balance}
#
# Structure:
#   get_valid_date()               — prompt user, validate against mkt_dates
#   build_price_lookup_for_date()  — {ticker: raw_price} for one date
#   make_stock_portfolio_rows()    — enrich positions with market prices
#   make_cash_portfolio_row()      — build the $$$$ row
#   print_portfolio_table()        — display formatted table to console
#   save_portfolio_for_date()      — write snapshot to JSON
#   main()                         — orchestrates all of the above

import json
from pathlib import Path

# ── paths ──────────────────────────────────────────────────────────────────────

SCRIPT_DIR             = Path(__file__).parent
FUNCTIONS              = SCRIPT_DIR / "functions"

STOCKS_BY_DATE_FILE    = FUNCTIONS / "stocks_by_date.json"
CASH_BY_DATE_FILE      = FUNCTIONS / "cash_by_date.json"
PRICES_DATES_FILE      = FUNCTIONS / "prices_dates.json"
MKT_DATES_FILE         = FUNCTIONS / "mkt_dates.json"
PORTFOLIO_BY_DATE_FILE = FUNCTIONS / "portfolio_by_date.json"

# ── loaders ────────────────────────────────────────────────────────────────────

def load_json(path):
    with open(path, "r") as f:
        return json.load(f)

# ── date prompt ────────────────────────────────────────────────────────────────

def get_valid_date(mkt_dates):
    """
    Prompt the user for a market date until a valid one is entered.
    Returns the validated date string.
    """
    mkt_date_set = set(mkt_dates)
    while True:
        date = input("Enter portfolio date (YYYY-MM-DD): ").strip()
        if date in mkt_date_set:
            return date
        print(f"  '{date}' is not a valid market date. Try again.")

# ── price lookup ───────────────────────────────────────────────────────────────

def build_price_lookup_for_date(prices_dates, date):
    """
    Return {ticker: raw_price} for the given date.
    If date not in prices_dates, returns empty dict.
    """
    return {
        record["ticker"]: record["raw_price"]
        for record in prices_dates.get(date, [])
    }

# ── row builders ───────────────────────────────────────────────────────────────

def make_stock_portfolio_rows(positions, price_lookup):
    """
    Enrich each position with market price and totals.
    positions: [{ticker, shares, average_cost}]
    Returns list of rows sorted by ticker.
    """
    rows = []
    for pos in sorted(positions, key=lambda p: p["ticker"]):
        ticker       = pos["ticker"]
        shares       = pos["shares"]
        average_cost = pos["average_cost"]
        mkt_price    = price_lookup.get(ticker, 0.0)

        rows.append({
            "ticker":          ticker,
            "shares":          shares,
            "average_cost":    average_cost,
            "mkt_price":       mkt_price,
            "total_avg_cost":  shares * average_cost,
            "total_mkt_value": shares * mkt_price,
        })
    return rows


def make_cash_portfolio_row(cash_balance):
    """
    Build the $$$$ cash row.
    Cash is modeled as shares of a $1 instrument.
    """
    return {
        "ticker":          "$$$$",
        "shares":          cash_balance,
        "average_cost":    1.0,
        "mkt_price":       1.0,
        "total_avg_cost":  cash_balance,
        "total_mkt_value": cash_balance,
    }

# ── display ────────────────────────────────────────────────────────────────────

def _fmt_shares(shares):
    """
    Format shares: integer display when whole, decimal when fractional.
    """
    if shares == int(shares):
        return f"{int(shares):>12,}"
    return f"{shares:>15,.4f}"


def _fmt_dollars(value):
    """Format a dollar amount with commas and 2 decimal places."""
    return f"{value:>17,.2f}"


def print_portfolio_table(date, rows):
    """Print a formatted portfolio table to the console."""
    header = f"{'Ticker':<8}  {'Shares':>12}  {'Avg Cost':>12}  {'Mkt Price':>12}  {'Total Avg Cost':>17}  {'Total Mkt Value':>17}"
    divider = "-" * len(header)

    print(f"\nPortfolio — {date}")
    print(divider)
    print(header)
    print(divider)

    for row in rows:
        ticker = row["ticker"]
        shares_str    = _fmt_shares(row["shares"])
        avg_cost_str  = _fmt_dollars(row["average_cost"])
        mkt_price_str = _fmt_dollars(row["mkt_price"])
        tot_avg_str   = _fmt_dollars(row["total_avg_cost"])
        tot_mkt_str   = _fmt_dollars(row["total_mkt_value"])

        print(f"{ticker:<8}  {shares_str}  {avg_cost_str}  {mkt_price_str}  {tot_avg_str}  {tot_mkt_str}")

    print(divider)

# ── save ───────────────────────────────────────────────────────────────────────

def save_portfolio_for_date(date, rows):
    """
    Write one date's portfolio snapshot to portfolio_by_date.json.
    Overwrites the file each run (single-date snapshot).
    """
    output = {date: rows}
    FUNCTIONS.mkdir(parents=True, exist_ok=True)
    with open(PORTFOLIO_BY_DATE_FILE, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nSaved portfolio for {date} to {PORTFOLIO_BY_DATE_FILE}")

# ── main ───────────────────────────────────────────────────────────────────────

def main():
    mkt_dates      = load_json(MKT_DATES_FILE)
    stocks_by_date = load_json(STOCKS_BY_DATE_FILE)
    cash_by_date   = load_json(CASH_BY_DATE_FILE)
    prices_dates   = load_json(PRICES_DATES_FILE)

    # 1. get and validate date
    date = get_valid_date(mkt_dates)

    # 2. build price lookup for that date
    price_lookup = build_price_lookup_for_date(prices_dates, date)

    # 3. build stock rows
    positions = stocks_by_date.get(date, [])
    stock_rows = make_stock_portfolio_rows(positions, price_lookup)

    # 4. build cash row
    cash_balance = cash_by_date.get(date, 0.0)
    cash_row = make_cash_portfolio_row(cash_balance)

    # 5. assemble: cash row first, then stocks sorted by ticker
    all_rows = [cash_row] + stock_rows

    # 6. print and save
    print_portfolio_table(date, all_rows)
    save_portfolio_for_date(date, all_rows)


if __name__ == "__main__":
    main()