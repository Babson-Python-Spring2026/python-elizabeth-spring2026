class PortfolioSystem:
    def __init__(self, prices_dates, prices_tickers, ticker_universe, mkt_dates):
        self.ticker_universe = ticker_universe
        self.mkt_dates = mkt_dates

    def get_num_market_dates(self):
        return len(self.mkt_dates)

    def get_num_tickers(self):
        return len(self.ticker_universe)

    def is_valid_ticker(self, ticker):
        return ticker in self.ticker_universe
    
    def first_date(self):
        return self.mkt_dates[0]