import json

SOURCE = 'classes/04-01 W/data/source/portfolio_prices_raw_and_split_adjusted_20260331b.csv'

# --- keyed by date ---
by_date = {}
with open(SOURCE, 'r') as f:
    next(f)  # skip header
    for line in f:
        date, ticker, raw_close, adjusted_close = line.strip().split(',')
        if date not in by_date:
            by_date[date] = []
        by_date[date].append({'ticker': ticker, 'raw_close': float(raw_close), 'adjusted_close': float(adjusted_close)})

with open('classes/04-01 W/data/system/prices_by_date.json', 'w') as f:
    json.dump(by_date, f, indent=2)

# --- keyed by ticker ---
by_ticker = {}
with open(SOURCE, 'r') as f:
    next(f)  # skip header
    for line in f:
        date, ticker, raw_close, adjusted_close = line.strip().split(',')
        if ticker not in by_ticker:
            by_ticker[ticker] = []
        by_ticker[ticker].append({'date': date, 'raw_close': float(raw_close), 'adjusted_close': float(adjusted_close)})

with open('classes/04-01 W/data/system/prices_by_ticker.json', 'w') as f:
    json.dump(by_ticker, f, indent=2)
