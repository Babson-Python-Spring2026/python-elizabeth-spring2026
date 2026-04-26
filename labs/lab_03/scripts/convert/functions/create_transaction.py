# create_transaction.py
#
# Reads:
#   functions/transactions.json    — [{date, type, record_number, ticker, shares, price}]
#   functions/mkt_dates.json       — [date_str, ...]  sorted ascending
#   functions/ticker_universe.json — [ticker_str, ...]
#   functions/prices_dates.json    — {date: [{ticker, raw_price, ...}]}
#
# Writes:
#   functions/transactions.json    — appends one validated transaction, sorted by (date, record_number)
#
# Transition logic:
#   Validates one new transaction and appends it to the ledger.
#
# Invariants:
#   - every record has a unique record_number
#   - list stays sorted by (date, record_number)
#   - buy/sell records have: date, type, record_number, ticker, shares, price
#   - contribution/withdrawal records have: date, type, record_number, amount

import json
from pathlib import Path

# ── paths ──────────────────────────────────────────────────────────────────────

SCRIPT_DIR           = Path(__file__).parent
FUNCTIONS            = SCRIPT_DIR / "functions"

TRANSACTIONS_FILE    = FUNCTIONS / "transactions.json"
MKT_DATES_FILE       = FUNCTIONS / "mkt_dates.json"
TICKER_UNIVERSE_FILE = FUNCTIONS / "ticker_universe.json"
PRICES_DATES_FILE    = FUNCTIONS / "prices_dates.json"

# ── loaders ────────────────────────────────────────────────────────────────────

def load_json(path):
    with open(path, "r") as f:
        return json.load(f)


def load_transactions():
    if TRANSACTIONS_FILE.exists():
        return load_json(TRANSACTIONS_FILE)
    return []


def save_transactions(transactions):
    FUNCTIONS.mkdir(parents=True, exist_ok=True)
    with open(TRANSACTIONS_FILE, "w") as f:
        json.dump(transactions, f, indent=2)

# ── validators ─────────────────────────────────────────────────────────────────

def get_valid_date(mkt_dates):
    """
    Prompt until the user enters a date that exists in mkt_dates.
    Returns the validated date string.
    """
    mkt_date_set = set(mkt_dates)
    while True:
        date = input("Date (YYYY-MM-DD): ").strip()
        if date in mkt_date_set:
            return date
        print(f"  '{date}' is not a valid market date. Try again.")


def get_valid_transaction_type():
    """
    Prompt until the user enters a valid transaction type.
    Valid types: buy, sell, contribution, withdrawal.
    Returns the type string in lowercase.
    """
    valid_types = {"buy", "sell", "contribution", "withdrawal"}
    while True:
        tx_type = input("Type (buy / sell / contribution / withdrawal): ").strip().lower()
        if tx_type in valid_types:
            return tx_type
        print(f"  '{tx_type}' is not a valid type. Try again.")


def get_valid_ticker(ticker_universe):
    """
    Prompt until the user enters a ticker that exists in ticker_universe.
    Returns the ticker string in uppercase.
    """
    ticker_set = set(ticker_universe)
    while True:
        ticker = input("Ticker: ").strip().upper()
        if ticker in ticker_set:
            return ticker
        print(f"  '{ticker}' is not in the ticker universe. Try again.")


def get_valid_shares():
    """
    Prompt until the user enters a positive number for shares.
    Returns shares as a float.
    """
    while True:
        raw = input("Shares: ").strip()
        try:
            shares = float(raw)
            if shares > 0:
                return shares
            print("  Shares must be a positive number. Try again.")
        except ValueError:
            print("  Invalid number. Try again.")


def get_valid_price(date, ticker, prices_dates):
    """
    Prompt until the user enters a positive number for price.
    Warns (but does not block) if the price differs from the market price
    in prices_dates for that date and ticker.
    Returns price as a float.
    """
    # look up market price for reference
    market_price = None
    for record in prices_dates.get(date, []):
        if record["ticker"] == ticker:
            market_price = record["raw_price"]
            break

    if market_price is not None:
        print(f"  Market price for {ticker} on {date}: {market_price:.6f}")

    while True:
        raw = input("Price: ").strip()
        try:
            price = float(raw)
            if price <= 0:
                print("  Price must be a positive number. Try again.")
                continue
            if market_price is not None and abs(price - market_price) / market_price > 0.05:
                confirm = input(
                    f"  Warning: entered price {price:.6f} differs from market price "
                    f"{market_price:.6f} by more than 5%. Enter 'yes' to confirm: "
                ).strip().lower()
                if confirm != "yes":
                    continue
            return price
        except ValueError:
            print("  Invalid number. Try again.")


def get_valid_amount():
    """
    Prompt until the user enters a positive number for a contribution/withdrawal amount.
    Returns amount as a float.
    """
    while True:
        raw = input("Amount: ").strip()
        try:
            amount = float(raw)
            if amount > 0:
                return amount
            print("  Amount must be a positive number. Try again.")
        except ValueError:
            print("  Invalid number. Try again.")


def next_record_number(transactions):
    """
    Return the next available record_number (max existing + 1).
    Returns 1 if no transactions exist yet.
    """
    if not transactions:
        return 1
    return max(tx["record_number"] for tx in transactions) + 1

# ── transaction builder ────────────────────────────────────────────────────────

def build_transaction(date, tx_type, record_number,
                      ticker=None, shares=None, price=None, amount=None):
    """
    Assemble a transaction dict with a consistent field order.
    buy/sell:              date, type, record_number, ticker, shares, price
    contribution/withdrawal: date, type, record_number, amount
    """
    if tx_type in ("buy", "sell"):
        return {
            "date":          date,
            "type":          tx_type,
            "record_number": record_number,
            "ticker":        ticker,
            "shares":        shares,
            "price":         price,
        }
    else:
        return {
            "date":          date,
            "type":          tx_type,
            "record_number": record_number,
            "amount":        amount,
        }

# ── main ───────────────────────────────────────────────────────────────────────

def create_transaction():
    mkt_dates       = load_json(MKT_DATES_FILE)
    ticker_universe = load_json(TICKER_UNIVERSE_FILE)
    prices_dates    = load_json(PRICES_DATES_FILE)
    transactions    = load_transactions()

    print(f"Loaded {len(transactions)} existing transaction(s).\n")

    # 1. date
    date = get_valid_date(mkt_dates)

    # 2. type
    tx_type = get_valid_transaction_type()

    # 3. type-specific fields
    record_number = next_record_number(transactions)

    if tx_type in ("buy", "sell"):
        ticker = get_valid_ticker(ticker_universe)
        shares = get_valid_shares()
        price  = get_valid_price(date, ticker, prices_dates)
        tx     = build_transaction(date, tx_type, record_number,
                                   ticker=ticker, shares=shares, price=price)
    else:
        amount = get_valid_amount()
        tx     = build_transaction(date, tx_type, record_number, amount=amount)

    # 4. append and re-sort by (date, record_number)
    transactions.append(tx)
    transactions.sort(key=lambda t: (t["date"], t["record_number"]))

    # 5. save
    save_transactions(transactions)
    print(f"\n  Saved: {tx}")


if __name__ == "__main__":
    create_transaction()