import time
import requests
import threading

from typing import Optional
from .settings import APP_SETTINGS
from .logging import logger
from .indicators import hma, rsi, wma, NotEnoughDataError, NotDataSeriesError


class APIError(Exception):
    pass


class GeckoTerminalAPIError(Exception):
    pass


class DexscreenerAPIError(Exception):
    pass


class ScraperThread:

    sleep_time: int = 60
    history_limit: int = 500

    def __init__(self, network: str, token_address: str, *args, **kwargs):
        self._scraper = DexScraper()
        self.network: str = network
        self._token_address: str = token_address
        self._pool_address: Optional[str] = None
        self._last_updated: Optional[int] = None
        self._response_history: list = []
        self._watch_list_keys: list = []

        self._stop_event = threading.Event()
        self.thread = threading.Thread(target=self._run, args=args, kwargs=kwargs)

    def __repr__(self):
        return (
            f"ScraperThread(network={self.network}, token_address={self.token_address})"
        )

    def __str__(self):
        return (
            f"ScraperThread(network={self.network}, token_address={self.token_address})"
        )

    def __del__(self):
        self.stop()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.stop()

    def __eq__(self, other):
        return (
            self.network == other.network and self.token_address == other.token_address
        )

    def is_token_still_trending(self):
        close_prices = [data["close"] for data in self.response_history]
        try:
            hmaval = hma(src=close_prices, length=81)
            rsi_val = rsi(src=close_prices, length=21)
            wma_val = wma(src=rsi_val, length=10)
        except (NotEnoughDataError, NotDataSeriesError):
            return True
        else:
            if (
                hmaval[-1] > close_prices[-1]
                and rsi_val[-1] < 70
                and wma_val[-1] > rsi_val[-1]
            ):
                return False
            return True

    @property
    def scraper(self):
        return self._scraper

    @property
    def pool_address(self):
        return self._pool_address

    @property
    def response_history(self):
        return self._response_history

    @response_history.setter
    def response_history(self, value: dict):
        if len(self.response_history) + 1 > self.history_limit:
            self._response_history.pop(0)
        self._response_history.append(value)

    @pool_address.setter
    def pool_address(self, value: str):
        self._pool_address = value

    @property
    def last_updated(self):
        return self._last_updated

    @last_updated.setter
    def last_updated(self, value: int):
        self._last_updated = value

    @property
    def network(self):
        return self._network

    @network.setter
    def network(self, value: str):
        if value not in self.scraper.network_ids_for_gecko_terminal:
            raise GeckoTerminalAPIError(f"Invalid network: {value}")
        self._network = value

    @property
    def token_address(self):
        return self._token_address

    def _run(self, *args, **kwargs):
        self.last_updated = int(time.time())
        while not self._stop_event.is_set():
            if "token_platform_address" not in kwargs:
                _, self.pool_address, _ = self.scraper.get_top_pool_from_gecko(
                    network=self.network, token_address=self.token_address
                )
            else:
                self.pool_address = kwargs["token_platform_address"]
            if (self.network in self.scraper.network_ids_for_gecko_terminal) and (
                self.token_address is not None
            ):  # If valid name of network

                try:
                    rest_api_data = self._get_data()
                    self.last_updated = self._post_data(rest_api_data)
                except GeckoTerminalAPIError as e:
                    logger.error(f"GeckoTerminalAPIError in ScraperThread: {e}")
                except APIError as e:
                    logger.error(f"APIError in ScraperThread: {e}")
                except requests.RequestException as e:
                    logger.error(f"RequestException in ScraperThread: {e}")
                else:
                    self.last_updated += self.sleep_time
                finally:
                    if not self.is_token_still_trending():
                        token_name, token_ticker = kwargs.get("token_name"), kwargs.get(
                            "token_ticker"
                        )
                        self._post_delete(
                            {
                                "token_name": token_name,
                                "token_ticker": token_ticker,
                            }
                        )
                        logger.info(f"Token {token_name} deleted from watch list")
                    if self.last_updated > int(time.time()):
                        time.sleep(self.last_updated - int(time.time()))
                    else:
                        time.sleep(self.sleep_time)
                    logger.info(
                        f"Thread for {self.network} {self.pool_address} resumed"
                    )
        logger.info(f"Thread for {self.network} {self.pool_address} stopped")

    def start(self):
        self.thread.start()

    def stop(self):
        self._stop_event.set()
        self.thread.join()

    def _get_data(self):
        tohlcv = self._scraper.get_ohlcv(
            network=self.network, pool_address=self.pool_address
        )
        logger.debug(tohlcv)
        logger.info(f"Data fetched for {self.network} {self.pool_address}")
        self.response_history = {
            "timestamp": tohlcv[0],
            "open": tohlcv[1],
            "high": tohlcv[2],
            "low": tohlcv[3],
            "close": tohlcv[4],
            "volume": tohlcv[5],
        }
        return tohlcv

    def _post_data(self, tohlcv):
        if tohlcv is None:
            logger.info("No data to post")
            return
        gecko_data = {
            "network": self.network,
            "pool_address": self.pool_address,
            "timeframe": "minute",
            "aggregation": "1",
            "timestamp": tohlcv[0],
            "currency": "usd",
            "token": "base",
            **self.response_history[-1],
        }
        self._scraper.post_gecko_data_to_overkill(data=gecko_data)
        logger.info(f"Data posted for {self.network} {self.pool_address}")
        return tohlcv[0]

    def _post_delete(self, token_data):
        return self._scraper.delete_coin_from_watch_list(token_data)


class DexThreadManager:
    scrappers: dict = {}  # dict for network_token-address
    threads_limit: int = 50

    def __init__(self):
        self.scraper = DexScraper()

    @property
    def watch_list(self):
        return self._watch_list

    @watch_list.setter
    def watch_list(self, value: list):
        if len(value) >= self.threads_limit:
            logger.error("Threads limit reached, setting maximum threads")
            value = value[: self.threads_limit]
        self._watch_list_keys = [
            f"{token_data.get('token_network')}_{token_data.get('token_address')}"
            for token_data in value
        ]
        self._watch_list = value
        self._manage_threads()

    @property
    def watch_list_keys(self):
        return self._watch_list_keys

    def _manage_threads(self):
        # stop threads that are not in watch_list
        logger.debug(self.scrappers.keys())
        marked_for_deletion = []
        for key, scapper in self.scrappers.items():
            if key not in self.watch_list_keys:
                scapper.stop()
                marked_for_deletion.append(key)
        for key in marked_for_deletion:
            self.scrappers.pop(key)
        # start threads that are in watch_list
        logger.debug(self.scrappers.keys())
        for token_data in self.watch_list:
            try:
                token_address = token_data.get("token_address")
                network = token_data.get("token_network")
            except KeyError as e:
                raise APIError("Token address or network not found") from e
            token_data.pop("token_network", None)  # Remove key if it exists
            token_data.pop("token_address", None)  # Remove key if it exists
            logger.debug(token_data)
            if f"{network}_{token_address}" not in self.scrappers.keys():
                self.scrappers[f"{network}_{token_address}"] = ScraperThread(
                    network, token_address, **token_data
                )
                self.scrappers[f"{network}_{token_address}"].start()
        logger.info("Threads updated")
        logger.info(f"current size: {len(self.scrappers)}")

    def start(self):
        while True:
            self.watch_list = self.scraper.get_watch_list_from_overkill().get(
                "result", []
            )
            logger.info("Watch List Updated")
            time.sleep(60)


class DexScraper:
    def __init__(self):
        self._name = "DegenAlphaRetriever"
        self._headers = {"Content-Type": "application/json"}
        self._network_ids_for_gecko_terminal = self.get_list_of_networks_from_gecko()

    # Getter for object's name haha
    @property
    def name(self):
        return self._name

    # Getter for the list of valid strings for network IDs for Gecko Terminal API
    @property
    def network_ids_for_gecko_terminal(self):
        return self._network_ids_for_gecko_terminal

    def search_pairs_from_dex_screener(self, token1: str, token2: str):
        url = "https://api.dexscreener.io/latest/dex/search?q={}%20{}"
        url = url.format(token1, token2)

        api_response = requests.get(url, headers=self._headers)
        api_data = api_response.json()

        # Retrieve the schema version and pairs array from the API response
        pairs = api_data.get("pairs", [])

        # Process the pairs array to access and modify token addresses as needed
        try:
            for pair in pairs:
                base_symbol = pair.get("baseToken")["symbol"]
                quote_symbol = pair.get("quoteToken")["symbol"]
                if base_symbol == token1 and quote_symbol == token2:
                    chain_id = pair.get("chainId")
                    price_usd = pair.get("priceUsd")
                    liq_usd = pair.get("liquidity")["usd"]
                    dex_id = pair.get("dexId")
                    dex_url = pair.get("url")
                    return (chain_id, price_usd, liq_usd, dex_id, dex_url)
        except KeyError as e:
            raise DexscreenerAPIError(
                "KeyError in search_pairs_from_dex_screener"
            ) from e

    def get_list_of_networks_from_gecko(self):
        url = "https://api.geckoterminal.com/api/v2/networks?page=1"
        network_ids = []

        api_response = requests.get(url, headers=self._headers)
        api_response.raise_for_status()
        api_data = api_response.json()
        try:
            data = api_data["data"]
            for element in data:
                network_ids.append(element["id"])
        except KeyError as e:
            raise GeckoTerminalAPIError(
                "KeyError in get_list_of_networks_from_gecko"
            ) from e

        return network_ids

    def get_token_price_from_gecko(self, network="solana", token_address=""):
        url = "https://api.geckoterminal.com/api/v2/simple/networks/{}/token_price/{}"
        url = url.format(network, token_address)

        api_response = requests.get(url, headers=self._headers)
        api_response.raise_for_status()
        api_data = api_response.json()
        try:
            data = api_data["data"]
            price = data["attributes"]["token_prices"][token_address]
        except KeyError as e:
            raise GeckoTerminalAPIError("KeyError in get_token_price_from_gecko") from e
        return price

    def get_pool_from_gecko(self, network="solana", pool_address=""):
        url = "https://api.geckoterminal.com/api/v2/networks/{}/pools/{}"
        url = url.format(network, pool_address)

        api_response = requests.get(url, headers=self._headers)
        api_response.raise_for_status()
        api_data = api_response.json()
        try:
            data = api_data["data"]
            price = data["attributes"]["base_token_price_usd"]
            name = data["attributes"]["name"]
            mc = data["attributes"]["market_cap_usd"]
            price_change = data["attributes"]["price_change_percentage"]
            txs = data["attributes"]["transactions"]
            vol = data["attributes"]["volume_usd"]
            fdv = data["attributes"]["fdv"]
            logger.info("Name: ", name, "\nPrice USD: ", price, "\nMarket Cap: ", mc)
        except KeyError as e:
            raise GeckoTerminalAPIError("KeyError in get_pool_from_gecko") from e
        return (name, price, mc)

    def get_top_pool_from_gecko(self, network="solana", token_address=""):
        url = "https://api.geckoterminal.com/api/v2/networks/{}/tokens/{}/pools?page=1"
        url = url.format(network, token_address)

        api_response = requests.get(url, headers=self._headers)
        api_response.raise_for_status()
        api_data = api_response.json()
        try:
            data = api_data["data"]
            top_pool = data[0]["attributes"]
            price = top_pool["base_token_price_usd"]
            pool_address = top_pool["address"]
            pool_name = top_pool["name"]
            mc = top_pool["market_cap_usd"]
            price_change = top_pool["price_change_percentage"]
            txs = top_pool["transactions"]
            vol = top_pool["volume_usd"]
            fdv = top_pool["fdv"]
        except KeyError as e:
            raise GeckoTerminalAPIError("KeyError in get_top_pool_from_gecko") from e
        return (pool_name, pool_address, price)

    def get_ohlcv(
        self,
        network="solana",
        pool_address="",
        timeframe="minute",
        aggregate="1",
        limit="1",
        currency="usd",
    ):
        url = "https://api.geckoterminal.com/api/v2/networks/{}/pools/{}/ohlcv/{}?aggregate={}&limit={}&currency={}"
        url = url.format(network, pool_address, timeframe, aggregate, limit, currency)
        api_response = requests.get(url, headers=self._headers)
        api_response.raise_for_status()
        api_data = api_response.json()
        logger.debug(api_data)
        try:
            data = api_data["data"]
            tohlcv = data["attributes"]["ohlcv_list"][0]
            timestamp = tohlcv[0]
            open = tohlcv[1]
            high = tohlcv[2]
            low = tohlcv[3]
            close = tohlcv[4]
            volume = tohlcv[5]
        except KeyError as e:
            raise GeckoTerminalAPIError("KeyError in get_ohlcv") from e
        return (timestamp, open, high, low, close, volume)

    def post_gecko_data_to_overkill(self, data: dict):
        url = "{}/v1/coin/gecko-terminal/price".format(APP_SETTINGS.overkill_api_url)

        headers = {
            "x-api-key": APP_SETTINGS.x_api_key,
            "x-api-secret": APP_SETTINGS.x_api_secret,
            **self._headers,
        }

        logger.debug(data)
        if not data:
            raise APIError("Data is empty")

        api_response = requests.post(url, headers=headers, json=data)
        api_response.raise_for_status()
        return api_response.json()

    def get_watch_list_from_overkill(self):
        url = "{}/v1/coin/watch".format(APP_SETTINGS.overkill_api_url)

        headers = {
            "x-api-key": APP_SETTINGS.x_api_key,
            "x-api-secret": APP_SETTINGS.x_api_secret,
            **self._headers,
        }
        api_response = requests.get(url, headers=headers)
        api_response.raise_for_status()
        return api_response.json()

    def delete_coin_from_watch_list(self, token_data: dict):
        url = "https://api.princeofcrypto.com/v1/coin/watch"
        headers = {
            "x-api-key": APP_SETTINGS.x_api_key,
            "x-api-secret": APP_SETTINGS.x_api_secret,
            **self._headers,
        }
        if not (token_data):
            raise APIError("No token information to delete")
        logger.info(token_data)
        try:
            payload = {
                "token_name": token_data["token_name"],
                "token_ticker": token_data["token_ticker"],
            }
        except KeyError as e:
            raise APIError("Token name or ticker not found") from e
        api_response = requests.delete(url, headers=headers, json=payload)
        api_response.raise_for_status()
        return api_response.json()
