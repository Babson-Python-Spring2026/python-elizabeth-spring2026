cash = 10000
positions = {"AAPL": 10, "MSFT": 5}
prices = {"AAPL": 190, "MSFT": 420}

port = {'cash': 10000.00,
        'positions', {('sys':'APPL', 
                       'shares': 10, 
                       'price': 190.00),
                       ('sym': 'MSFT',
                        'shares': 5,
                        'price': 420.00)}}

def buy_stock(port):
    sys = input ('Enter stock symbol you want to buy: ')
    
    txt = 'Enter shares you want to buy'
    while True:
        try:
            shares = int(input(txt))
            break
        except ValueError:
            txt = 'You must enter an integer'

    txt = f'Enter price of (sym):'
    while True:
        try:
            price = float(input(txt))
            break
        except ValueError:
            txt = 'You must enter a float'
    
    if shares = price > port ['cash']: