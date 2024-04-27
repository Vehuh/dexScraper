import numpy as np
import math
from functools import wraps


class NotEnoughDataError(Exception):
    pass


class NotDataSeriesError(Exception):
    pass


def indicator_wrapper(func):

    @wraps(func)
    def wrapper(*args, **kwargs):

        if "src" in kwargs:
            if isinstance(kwargs["src"], (float, int)):
                raise NotDataSeriesError("src must be a list or numpy array")
        if "length" in kwargs:
            if not isinstance(kwargs["length"], int):
                raise NotDataSeriesError("length must be an integer")
        if "src" in kwargs and "length" in kwargs:
            if len(kwargs["src"]) < kwargs["length"]:
                raise NotEnoughDataError("Not enough data to calculate indicator")
        return func(*args, **kwargs)

    return wrapper


@indicator_wrapper
def wma(src, length):
    sum_val = 0.0
    norm = 0.0
    for i in range(min(length, len(src))):
        weight = (length - i) * length
        sum_val += src[i] * weight
        norm += weight
    return sum_val / norm


@indicator_wrapper
def hma(src, length):
    wma1 = wma(src, length)
    wma2 = wma(src, length // 2)
    wma3 = wma(np.subtract(wma1, np.multiply(wma2, 2)), int(math.sqrt(length)))
    return np.multiply(wma3, -1)


@indicator_wrapper
def rsi(src, length):
    deltas = np.diff(src)
    seed = deltas[: length + 1]
    up = seed[seed >= 0].sum() / length
    down = -seed[seed < 0].sum() / length
    rs = up / down
    rsi = np.zeros_like(src)
    rsi[:length] = 100.0 - 100.0 / (1.0 + rs)

    for i in range(length, len(src)):
        delta = deltas[i - 1]  # The change in price at index i
        if delta > 0:
            upval = delta
            downval = 0.0
        else:
            upval = 0.0
            downval = -delta
        up = (up * (length - 1) + upval) / length
        down = (down * (length - 1) + downval) / length
        rs = up / down
        rsi[i] = 100.0 - 100.0 / (1.0 + rs)

    return rsi


@indicator_wrapper
def sma(src, length):
    return np.mean(src[-length:])


# close_prices = np.array([day[3] for day in price_data])  # Extract close prices
# hmalen = 30
# hma_result = hma(close_prices, hmalen)
# print("HMA Result:", hma_result)
