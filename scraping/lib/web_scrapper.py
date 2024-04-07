from selenium import webdriver
from selenium.webdriver.chrome.service import Service
import json
import time

class DexScraper ():
    def __init__(self):
        self.service = Service()
        self.options = webdriver.ChromeOptions()
        self.driver = webdriver.Chrome(service=self.service, options=self.options)

    def search_pairs (self, token1 : str, token2 : str):
        url = "https://api.dexscreener.io/latest/dex/search?q={}%20{}"
        url = url.format(token1, token2)
        self.driver.get(url)
        time.sleep(0.5)

        api_response_element = self.driver.find_element(by='tag name', value='pre')
        api_response = api_response_element.text

        self.driver.quit()

        api_data = json.loads(api_response)

        # Retrieve the schema version and pairs array from the API response
        schema_version = api_data.get('schemaVersion')
        pairs = api_data.get('pairs', [])

        # Process the pairs array to access and modify token addresses as needed
        for pair in pairs:
            base_symbol = pair.get('baseToken')['symbol']
            quote_symbol = pair.get('quoteToken')['symbol']
            if (base_symbol == token1 and quote_symbol == token2):
                chain_id = pair.get('chainId')
                price_usd = pair.get('priceUsd')
                liq_usd = pair.get('liquidity')['usd']
                dex_id = pair.get('dexId')
                dex_url = pair.get('url')
                print ('/'*40)
                # Perform necessary operations with the token addresses

                # Example: Print the token addresses
                print("Chain: ", chain_id, "\nPrice USD: ", price_usd, "\nLiquidity USD: ", liq_usd, "\nDEX ID: ", dex_id, "\nDEX URL: ", dex_url)