import json

SOURCE = 'classes/04-01 W/data/source/portfolio_splits_true_splits_only_20260331b.csv'

# --- keyed by date ---
by_date = {}
with open(SOURCE, 'r') as f:
    next(f)  # skip header
    for line in f:
        date, ticker, ratio = line.strip().split(',')
        if date not in by_date:
            by_date[date] = []
        by_date[date].append({'ticker': ticker, 'split_ratio': float(ratio)})

with open('classes/04-01 W/data/system/splits_by_date.json', 'w') as f:
    json.dump(by_date, f, indent=2)

# --- keyed by ticker ---
by_ticker = {}
with open(SOURCE, 'r') as f:
    next(f)  # skip header
    for line in f:
        date, ticker, ratio = line.strip().split(',')
        if ticker not in by_ticker:
            by_ticker[ticker] = []
        by_ticker[ticker].append({'date': date, 'split_ratio': float(ratio)})

with open('classes/04-01 W/data/system/splits_by_ticker.json', 'w') as f:
    json.dump(by_ticker, f, indent=2)
