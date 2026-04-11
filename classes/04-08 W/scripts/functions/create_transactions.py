# transactions.py
# First-pass student script: manual transaction ledger
# Loads prior transactions, runs an entry session for one working date,
# saves to JSON after every transaction.

import json
from pathlib import Path

# ── file location ──────────────────────────────────────────────────────────────
# scripts/functions/transactions.py  →  up 3 levels  →  class_repo/
REPO_ROOT = Path(__file__).parent.parent.parent
TRANSACTIONS_FILE = REPO_ROOT / "data" / "system" / "transactions" / "transactions.json"


# ── helpers ────────────────────────────────────────────────────────────────────

def load_transactions():
    if TRANSACTIONS_FILE.exists():
        with open(TRANSACTIONS_FILE, "r") as f:
            return json.load(f)
    return []


def save_transactions(transactions):
    TRANSACTIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(TRANSACTIONS_FILE, "w") as f:
        json.dump(transactions, f, indent=2)


def create_transaction(transactions, date, tx_type, ticker=None, shares=None, price=None, amount=None):
    tx = {"date": date, "type": tx_type}
    if tx_type in ("buy", "sell"):
        tx["ticker"] = ticker
        tx["shares"] = shares
        tx["price"] = price
    else:  # contribution or withdrawal
        tx["amount"] = amount
    transactions.append(tx)
    save_transactions(transactions)
    print(f"  Saved: {tx}")
    return tx


def get_cash_balance(transactions, as_of_date):
    cash = 0.0
    for tx in transactions:
        if tx["date"] > as_of_date:
            continue
        if tx["type"] == "contribution":
            cash += tx["amount"]
        elif tx["type"] == "withdrawal":
            cash -= tx["amount"]
        elif tx["type"] == "buy":
            cash -= tx["shares"] * tx["price"]
        elif tx["type"] == "sell":
            cash += tx["shares"] * tx["price"]
    return cash


def build_portfolio(transactions, as_of_date):
    positions = {}
    for tx in transactions:
        if tx["date"] > as_of_date:
            continue
        if tx["type"] == "buy":
            positions[tx["ticker"]] = positions.get(tx["ticker"], 0) + tx["shares"]
        elif tx["type"] == "sell":
            positions[tx["ticker"]] = positions.get(tx["ticker"], 0) - tx["shares"]
    # drop any tickers that went to zero
    positions = {t: s for t, s in positions.items() if s != 0}
    return positions


def list_transactions_for_ticker(transactions, ticker):
    return [tx for tx in transactions if tx.get("ticker") == ticker]


# ── entry session ──────────────────────────────────────────────────────────────

def run_session():
    transactions = load_transactions()
    print(f"Loaded {len(transactions)} existing transaction(s).")

    working_date = input("Enter working date (YYYY-MM-DD): ").strip()

    while True:
        print("\nTransaction types: contribution, withdrawal, buy, sell")
        print("Commands:          done, cash, portfolio, history")
        tx_type = input("Enter type or command: ").strip().lower()

        if tx_type == "done":
            print("Session ended.")
            break

        elif tx_type == "cash":
            as_of = input("  Cash balance as of date (YYYY-MM-DD): ").strip()
            print(f"  Cash balance: {get_cash_balance(transactions, as_of):.2f}")

        elif tx_type == "portfolio":
            as_of = input("  Portfolio as of date (YYYY-MM-DD): ").strip()
            print(f"  Portfolio: {build_portfolio(transactions, as_of)}")

        elif tx_type == "history":
            ticker = input("  Ticker: ").strip().upper()
            history = list_transactions_for_ticker(transactions, ticker)
            for tx in history:
                print(" ", tx)

        elif tx_type == "contribution":
            amount = float(input("  Amount: "))
            create_transaction(transactions, working_date, "contribution", amount=amount)

        elif tx_type == "withdrawal":
            amount = float(input("  Amount: "))
            create_transaction(transactions, working_date, "withdrawal", amount=amount)

        elif tx_type == "buy":
            ticker = input("  Ticker: ").strip().upper()
            shares = float(input("  Shares: "))
            price  = float(input("  Price:  "))
            create_transaction(transactions, working_date, "buy",
                               ticker=ticker, shares=shares, price=price)

        elif tx_type == "sell":
            ticker = input("  Ticker: ").strip().upper()
            shares = float(input("  Shares: "))
            price  = float(input("  Price:  "))
            create_transaction(transactions, working_date, "sell",
                               ticker=ticker, shares=shares, price=price)

        else:
            print("  Unrecognized input. Try again.")


if __name__ == "__main__":
    run_session()