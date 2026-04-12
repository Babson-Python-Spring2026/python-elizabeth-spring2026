"""
create_transaction.py

State read:
    transactions.json, mkt_dates.json, ticker_universe.json, prices_dates.json

Transition logic:
    validates one new transaction and appends it to the ledger

Invariant:
    every record has a unique record_number; list stays sorted by (date, record_number)
"""

import json
from pathlib import Path

# ── paths ──────────────────────────────────────────────────────────────────────
LAB_ROOT             = Path(__file__).parent.parent.parent.parent
TRANSACTIONS_FILE    = LAB_ROOT / "data/system/transactions/transactions.json"
MKT_DATES_FILE       = LAB_ROOT / "data/system/mkt_dates.json"
TICKER_UNIVERSE_FILE = LAB_ROOT / "data/system/ticker_universe.json"
PRICES_DATES_FILE    = LAB_ROOT / "data/system/prices_dates.json"


# ── file helpers ───────────────────────────────────────────────────────────────

def load_json(path):
    with open(path, "r") as f:
        return json.load(f)


def save_json(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=4)


# ── record helper ──────────────────────────────────────────────────────────────

def next_record_number(transactions):
    """Return max existing record_number + 1, or 1 if the ledger is empty."""
    if not transactions:
        return 1
    return max(t.get("record_number", 0) for t in transactions) + 1


# ── validation helpers ─────────────────────────────────────────────────────────

def get_valid_date():
    """Prompt until the user enters a date that exists in mkt_dates.json."""
    mkt_dates = set(load_json(MKT_DATES_FILE))
    while True:
        date = input("Enter transaction date (YYYY-MM-DD): ").strip()
        if date in mkt_dates:
            return date
        print(f"  '{date}' is not a valid market date. Try again.")


def get_valid_transaction_type():
    """Prompt until the user picks one of the four allowed transaction types."""
    valid = {"contribution", "withdrawal", "buy", "sell"}
    while True:
        tx_type = input(
            "Enter transaction type (contribution, withdrawal, buy, sell): "
        ).strip().lower()
        if tx_type in valid:
            return tx_type
        print(f"  '{tx_type}' is not a valid type.")


def get_valid_ticker():
    """Prompt until the user enters a ticker that exists in ticker_universe.json."""
    universe = set(load_json(TICKER_UNIVERSE_FILE))
    while True:
        ticker = input("Enter ticker symbol: ").strip().upper()
        if ticker in universe:
            return ticker
        print(f"  '{ticker}' is not in the ticker universe.")


def get_valid_price(ticker, date):
    """
    Prompt until the user enters a price within ±15% of the market price
    for (ticker, date) in prices_dates.json.
    """
    prices_by_date = load_json(PRICES_DATES_FILE)
    market_price = None
    for entry in prices_by_date.get(date, []):
        if entry["ticker"] == ticker:
            market_price = entry["raw_price"]
            break

    if market_price is None:
        print(f"  No market price for {ticker} on {date}. Accepting any positive price.")
        return get_positive_float("Enter price per share: ")

    low  = market_price * 0.85
    high = market_price * 1.15
    print(f"  Market price for {ticker} on {date}: {market_price:.2f}  "
          f"(valid range: {low:.2f} – {high:.2f})")
    while True:
        price = get_positive_float("Enter price per share: ")
        if low <= price <= high:
            return price
        print(f"  {price:.2f} is outside ±15% ({low:.2f} – {high:.2f}).")


def get_positive_float(prompt):
    """Prompt until the user enters a strictly positive number."""
    while True:
        try:
            value = float(input(prompt).strip())
            if value > 0:
                return value
            print("  Value must be greater than 0.")
        except ValueError:
            print("  Please enter a valid number.")


# ── main function ──────────────────────────────────────────────────────────────

def create_transaction():
    """
    Interactively create one transaction, validate all fields,
    append it to transactions.json, and save.

    State read:    transactions.json, mkt_dates.json, ticker_universe.json,
                   prices_dates.json
    Transition:    appends one validated record; re-sorts by (date, record_number)
    Invariant:     record_numbers are unique; list is chronologically ordered
    """
    transactions = load_json(TRANSACTIONS_FILE) if TRANSACTIONS_FILE.exists() else []

    date    = get_valid_date()
    tx_type = get_valid_transaction_type()

    record = {
        "date":          date,
        "type":          tx_type,
        "record_number": next_record_number(transactions),
    }

    if tx_type in {"contribution", "withdrawal"}:
        record["ticker"] = "$$$$"
        record["shares"] = get_positive_float("Enter amount ($): ")
        record["price"]  = 1.0

    else:  # buy or sell
        record["ticker"] = get_valid_ticker()
        record["shares"] = get_positive_float("Enter number of shares: ")
        record["price"]  = get_valid_price(record["ticker"], date)

    transactions.append(record)
    transactions.sort(key=lambda t: (t["date"], t.get("record_number", 0)))

    save_json(TRANSACTIONS_FILE, transactions)
    print(f"\n  Saved transaction: {record}")


if __name__ == "__main__":
    create_transaction()
