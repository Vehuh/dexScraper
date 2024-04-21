from lib.web_scrapper import DexScraper
import time

if __name__ == "__main__":
  scraper = DexScraper()

  while (True):
    watch_list = scraper.get_watch_list_from_overkill()  
    token_list = watch_list['result']
    for i in range(len(token_list)):
      token = token_list[i]
      token_name = token['token_name']
      token_ticker = token['token_ticker']
      token_address = token['token_address']
      token_platform = token['token_platform']
      token_platform_address = token['token_platform_address']
      network = "solana"
      if (network in scraper.network_ids_for_gecko_terminal) and (token_address is not None) and (token_address != "string"): #If valid name of network

        try:
          pool_name, pool_address, price = scraper.get_top_pool_from_gecko(network = network, token_address=token_address)
        except:
          pass
        else:
          time.sleep(1) #Wait 1 sec between requests
          tohlcv = scraper.get_ohlcv(network = network, pool_address=pool_address)
          time.sleep(1) #Wait 1 sec between requests

          gecko_data = {
            "network": "string",
            "pool_address": "string",
            "timeframe": "minute",
            "aggregation": "1",
            "timestamp": tohlcv[0],
            "currency": "usd",
            "token": "base",
            "open": tohlcv[1],
            "high": tohlcv[2],
            "low": tohlcv[3],
            "close": tohlcv[4],
            "volume": tohlcv[5]
          }
          try:
            scraper.post_gecko_data_to_overkill(data=gecko_data)
          except:
            pass
    time.sleep(298)
