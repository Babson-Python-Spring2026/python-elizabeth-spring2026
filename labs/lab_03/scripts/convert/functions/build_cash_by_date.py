# build_cash_by_date.py
#
# Reads:
#   functions/transactions.json    — [{date, type, ticker, shares, price, ...}]
#   functions/prices_dates.json    — {date: [{ticker, raw_price, shares_in, shares_out, dividend}]}
#   functions/mkt_dates.json       — [date_str, ...]  sorted ascending
#   functions/stocks_by_date.json  — {date: [{ticker, shares, average_cost}]}
#
# Writes:
#   functions/cash_by_date.json    — {date: float}
#
# Logic per market date:
#   1. Start with prior cash balance (0.0 before first date)
#   2. Apply transaction cash flows for this date:
#        contribution: +amount
#        withdrawal:   -amount
#        buy:          -(shares * price)
#        sell:         +(shares * price)
#   3. Apply dividend cash flows using positions at START of date
#      (i.e. stocks_by_date[prior_date]):
#        dividend_cash += per_share_dividend * shares_held
#   4. Store cumulative cash balance
#
# Notes:
#   - Transactions not on a market date are skipped silently
#   - No rounding at any step
 
import json
from pathlib import Path
 
# ── paths ──────────────────────────────────────────────────────────────────────
 
SCRIPT_DIR          = Path(__file__).parent
FUNCTIONS           = SCRIPT_DIR / "functions"
 
TRANSACTIONS_FILE   = FUNCTIONS / "transactions.json"
PRICES_DATES_FILE   = FUNCTIONS / "prices_dates.json"
MKT_DATES_FILE      = FUNCTIONS / "mkt_dates.json"
STOCKS_BY_DATE_FILE = FUNCTIONS / "stocks_by_date.json"
CASH_BY_DATE_FILE   = FUNCTIONS / "cash_by_date.json"
 
# ── loaders ────────────────────────────────────────────────────────────────────
 
def load_json(path):
    with open(path, "r") as f:
        return json.load(f)
 
# ── helpers ────────────────────────────────────────────────────────────────────
 
def transaction_cash_flow(txns_for_date):
    """
    Return net cash flow from all transactions on this date.
    Only contribution, withdrawal, buy, sell affect cash.
    """
    cash = 0.0
    for tx in txns_for_date:
        tx_type = tx.get("type", "").lower()
        if tx_type == "contribution":
            cash += tx["amount"]
        elif tx_type == "withdrawal":
            cash -= tx["amount"]
        elif tx_type == "buy":
            cash -= tx["shares"] * tx["price"]
        elif tx_type == "sell":
            cash += tx["shares"] * tx["price"]
    return cash
 
 
def dividend_cash_flow(prices_for_date, prior_positions):
    """
    Return dividend cash flow for this date.
    Uses positions at START of date (prior_positions).
    prior_positions: [{ticker, shares, average_cost}]
    prices_for_date: [{ticker, dividend, ...}]
    """
    # index prior positions by ticker for fast lookup
    shares_held = {p["ticker"]: p["shares"] for p in prior_positions}
 
    cash = 0.0
    for record in prices_for_date:
        dividend = record.get("dividend", 0.0)
        if dividend == 0.0:
            continue
        ticker = record["ticker"]
        if ticker in shares_held:
            cash += dividend * shares_held[ticker]
    return cash
 
# ── main ───────────────────────────────────────────────────────────────────────
 
def build_cash_by_date():
    mkt_dates      = load_json(MKT_DATES_FILE)
    prices_dates   = load_json(PRICES_DATES_FILE)
    transactions   = load_json(TRANSACTIONS_FILE)
    stocks_by_date = load_json(STOCKS_BY_DATE_FILE)
 
    mkt_date_set = set(mkt_dates)
 
    # index transactions by date; skip any not on a market date
    txns_by_date = {}
    for tx in transactions:
        d = tx["date"]
        if d not in mkt_date_set:
            continue
        txns_by_date.setdefault(d, []).append(tx)
 
    cash_by_date = {}
    cash         = 0.0
    prior_date   = None
 
    for date in mkt_dates:
        # positions at start of this date = snapshot from prior date
        prior_positions = stocks_by_date.get(prior_date, []) if prior_date else []
 
        # 1. transaction cash flows
        cash += transaction_cash_flow(txns_by_date.get(date, []))
 
        # 2. dividend cash flows (using prior positions)
        cash += dividend_cash_flow(prices_dates.get(date, []), prior_positions)
 
        cash_by_date[date] = cash
        prior_date = date
 
    # write output
    FUNCTIONS.mkdir(parents=True, exist_ok=True)
    with open(CASH_BY_DATE_FILE, "w") as f:
        json.dump(cash_by_date, f, indent=2)
 
    print(f"Wrote {len(cash_by_date)} dates to {CASH_BY_DATE_FILE}")
 
 
if __name__ == "__main__":
    build_cash_by_date()
