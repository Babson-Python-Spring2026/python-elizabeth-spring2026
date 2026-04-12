"""
build_portfolio(as_of_date).py

State read:
    stocks_by_date.json, cash_by_date.json, prices_dates.json
    (both position files rebuilt fresh from transactions each call)

Transition logic:
    none — assembles a snapshot from rebuilt position data and current prices

Invariant:
    portfolio rows = one cash row ($$$$) + one row per held stock, sorted by ticker
"""

import json
from pathlib import Path
from build_cash_by_date import build_cash_by_date

# ── paths ──────────────────────────────────────────────────────────────────────
LAB_ROOT            = Path(__file__).parent.parent.parent.parent
STOCKS_BY_DATE_FILE = LAB_ROOT / "data/system/positions_by_date/stocks_by_date.json"
CASH_BY_DATE_FILE   = LAB_ROOT / "data/system/positions_by_date/cash_by_date.json"
PRICES_DATES_FILE   = LAB_ROOT / "data/system/prices_dates.json"
MKT_DATES_FILE      = LAB_ROOT / "data/system/mkt_dates.json"
PORTFOLIO_DIR       = LAB_ROOT / "data/system/positions_by_date"


# ── file helpers ───────────────────────────────────────────────────────────────

def load_json(path):
    with open(path, "r") as f:
        return json.load(f)


def save_json(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=4)


# ── validation helper ──────────────────────────────────────────────────────────

def get_valid_date():
    """Prompt until the user enters a date that exists in mkt_dates.json."""
    mkt_dates = set(load_json(MKT_DATES_FILE))
    while True:
        date = input("Enter portfolio date (YYYY-MM-DD): ").strip()
        if date in mkt_dates:
            return date
        print(f"  '{date}' is not a valid market date. Try again.")


# ── lookup helper ──────────────────────────────────────────────────────────────

def build_price_lookup_for_date(date):
    """Return {ticker: raw_price} for every ticker with a price on the given date."""
    prices_by_date = load_json(PRICES_DATES_FILE)
    return {entry["ticker"]: entry["raw_price"] for entry in prices_by_date.get(date, [])}


# ── row builders ───────────────────────────────────────────────────────────────

def make_cash_portfolio_row(cash):
    """
    Build the cash row using ticker '$$$$'.
    Cash is treated as shares at $1.00 per share.
    """
    return {
        "ticker":          "$$$$",
        "shares":          round(cash, 2),
        "average_cost":    1.0,
        "mkt_price":       1.0,
        "total_avg_cost":  round(cash, 2),
        "total_mkt_value": round(cash, 2),
    }


def make_stock_portfolio_rows(stocks, price_lookup):
    """
    Build one enriched row per stock position.
    stocks:       list of {ticker, shares, average_cost} from stocks_by_date
    price_lookup: {ticker: raw_price}
    Returns rows sorted by ticker.
    """
    rows = []
    for pos in stocks:
        ticker    = pos["ticker"]
        shares    = pos["shares"]
        avg_cost  = pos["average_cost"]
        mkt_price = price_lookup.get(ticker, avg_cost)
        rows.append({
            "ticker":          ticker,
            "shares":          shares,
            "average_cost":    round(avg_cost, 2),
            "mkt_price":       round(mkt_price, 2),
            "total_avg_cost":  round(shares * avg_cost, 2),
            "total_mkt_value": round(shares * mkt_price, 2),
        })
    return sorted(rows, key=lambda r: r["ticker"])


# ── display ────────────────────────────────────────────────────────────────────

def print_portfolio_table(date, rows):
    """Print the portfolio as an aligned table with a totals row."""
    cw = {"ticker": 6, "shares": 12, "avg": 10, "mkt": 10, "tcost": 14, "tmkt": 14}

    header = (
        f"{'Ticker':<{cw['ticker']}}  "
        f"{'Shares':>{cw['shares']}}  "
        f"{'Avg Cost':>{cw['avg']}}  "
        f"{'Mkt Price':>{cw['mkt']}}  "
        f"{'Total Cost':>{cw['tcost']}}  "
        f"{'Mkt Value':>{cw['tmkt']}}"
    )
    sep = "-" * len(header)

    print(f"\nPortfolio as of {date}")
    print(sep)
    print(header)
    print(sep)

    total_cost = 0.0
    total_mkt  = 0.0

    for row in rows:
        ticker = row["ticker"]
        shares = row["shares"]
        shares_str = f"{shares:,.2f}" if ticker == "$$$$" else f"{shares:,.0f}"
        print(
            f"{ticker:<{cw['ticker']}}  "
            f"{shares_str:>{cw['shares']}}  "
            f"{row['average_cost']:>{cw['avg']},.2f}  "
            f"{row['mkt_price']:>{cw['mkt']},.2f}  "
            f"{row['total_avg_cost']:>{cw['tcost']},.2f}  "
            f"{row['total_mkt_value']:>{cw['tmkt']},.2f}"
        )
        total_cost += row["total_avg_cost"]
        total_mkt  += row["total_mkt_value"]

    print(sep)
    print(
        f"{'TOTAL':<{cw['ticker']}}  "
        f"{'':>{cw['shares']}}  "
        f"{'':>{cw['avg']}}  "
        f"{'':>{cw['mkt']}}  "
        f"{total_cost:>{cw['tcost']},.2f}  "
        f"{total_mkt:>{cw['tmkt']},.2f}"
    )
    print(sep)


def save_portfolio_for_date(date, rows):
    """Save portfolio rows to portfolio_{date}.json."""
    out_path = PORTFOLIO_DIR / f"portfolio_{date}.json"
    save_json(out_path, rows)
    print(f"\n  Saved to {out_path.name}")


# ── main function ──────────────────────────────────────────────────────────────

def build_portfolio(as_of_date):
    """
    Rebuild position data from transactions, then assemble and display
    the full portfolio snapshot for the given market date.

    State read:    stocks_by_date.json, cash_by_date.json, prices_dates.json
                   (both rebuilt fresh — build_cash_by_date chains to build_stocks)
    Transition:    none — assembles a snapshot from rebuilt data
    Invariant:     every held stock appears exactly once; cash row always present
    """
    build_cash_by_date()

    stocks_by_date = load_json(STOCKS_BY_DATE_FILE)
    cash_by_date   = load_json(CASH_BY_DATE_FILE)

    if as_of_date not in stocks_by_date:
        print(f"  No stock positions recorded for {as_of_date}.")
        return None

    if as_of_date not in cash_by_date:
        print(f"  No cash balance recorded for {as_of_date}.")
        return None

    stocks       = stocks_by_date[as_of_date]
    cash         = cash_by_date[as_of_date]
    price_lookup = build_price_lookup_for_date(as_of_date)

    rows = [make_cash_portfolio_row(cash)] + make_stock_portfolio_rows(stocks, price_lookup)

    print_portfolio_table(as_of_date, rows)
    save_portfolio_for_date(as_of_date, rows)

    return rows


if __name__ == "__main__":
    date = get_valid_date()
    build_portfolio(date)
