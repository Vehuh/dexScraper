from lib.web_scrapper import DexScraper

scraper = DexScraper()
#Example for Dex Screener
#scraper.search_pairs_from_dex_screener("SOL", "USDT")

#Example for token price with Gecko Terminal with WIF
#print (scraper.get_token_price_from_gecko(token_address="EKpQGSJtjMFqKZ9KQanSqYXRcF8fBopzLHYxdM65zcjm"))

#Example for pool data with Gecko Terminal qith BODEN
scraper.get_pool_from_gecko(pool_address="6UYbX1x8YUcFj8YstPYiZByG7uQzAq2s46ZWphUMkjg5")
