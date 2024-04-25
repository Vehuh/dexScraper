import requests


class APIError(Exception):
    pass


class GeckoTerminalAPIError(Exception):
    pass


class DexscreenerAPIError(Exception):
    pass


class DexScraper:
    def __init__(self):
        self._name = "DegenAlphaRetriever"
        self._headers = {"Content-Type": "application/json"}
        self._network_ids_for_gecko_terminal = [
            "eth",
            "bsc",
            "polygon_pos",
            "avax",
            "movr",
            "cro",
            "one",
            "boba",
            "ftm",
            "bch",
            "aurora",
            "metis",
            "arbitrum",
            "fuse",
            "okexchain",
            "kcc",
            "iotx",
            "celo",
            "xdai",
            "heco",
            "glmr",
            "optimism",
            "nrg",
            "wan",
            "ronin",
            "kai",
            "mtr",
            "velas",
            "sdn",
            "tlos",
            "sys",
            "oasis",
            "astr",
            "ela",
            "milkada",
            "dfk",
            "evmos",
            "solana",
            "cfx",
            "bttc",
            "sxn",
            "xdc",
            "klaytn",
            "kava",
            "bitgert",
            "tombchain",
            "dogechain",
            "findora",
            "thundercore",
            "arbitrum_nova",
            "canto",
            "ethereum_classic",
            "step-network",
            "ethw",
            "godwoken",
            "songbird",
            "redlight_chain",
            "tomochain",
            "fx",
            "platon_network",
            "exosama",
            "oasys",
            "bitkub_chain",
            "wemix",
            "flare",
            "onus",
            "aptos",
            "core",
            "goerli-testnet",
            "filecoin",
            "lung-chain",
            "zksync",
            "poochain",
            "loop-network",
            "multivac",
            "polygon-zkevm",
            "eos-evm",
            "apex",
            "callisto",
            "ultron",
            "sui-network",
            "pulsechain",
            "trustless-computer",
            "enuls",
            "tenet",
            "rollux",
            "starknet-alpha",
            "mantle",
            "neon-evm",
            "linea",
            "base",
            "bitrock",
            "opbnb",
            "maxxchain",
            "sei-network",
            "shibarium",
            "manta-pacific",
            "sepolia-testnet",
            "hedera-hashgraph",
            "shimmerevm",
        ]

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
            print("Name: ", name, "\nPrice USD: ", price, "\nMarket Cap: ", mc)
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
        url = "https://api.princeofcrypto.com/v1/coin/gecko-terminal/price"

        # TODO: add creadentials reader
        with open("~/x-api-key.txt", "r") as file:
            API_KEY = file.read()

        with open("~/x-api-secret.txt", "r") as file:
            API_SECRET = file.read()

        headers = {"x-api-key": API_KEY, "x-api-secret": API_SECRET, **self._headers}

        api_response = requests.post(url, headers=headers, json=data)
        if api_response.status_code == 200:
            return api_response.json()
        else:
            raise APIError("POST Gecko Price to Overkill Failed")

    def get_watch_list_from_overkill(self):
        url = "https://api.princeofcrypto.com/v1/coin/watch-list"

        # TODO: add creadentials reader
        with open("~/x-api-key.txt", "r") as file:
            API_KEY = file.read()

        with open("~/x-api-secret.txt", "r") as file:
            API_SECRET = file.read()
        headers = {"x-api-key": API_KEY, "x-api-secret": API_SECRET, **self._headers}
        api_response = requests.get(url, headers=headers)
        if api_response.status_code == 200:
            return api_response.json()
        else:
            raise APIError("GET Watch List from Overkill Failed")
