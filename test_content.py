import yfinance as yf

# search = yf.Search("stocks", max_results=30)
# trending_tickers = [q['symbol'] for q in search.quotes if q.get('quoteType') == 'EQUITY']
# print(trending_tickers)
samsung = yf.Ticker("005930.KS")
print(samsung)