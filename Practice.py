from PyQt5.QtWidgets import QApplication, QMainWindow
from binance.client import Client
import ccxt
import datetime
import pybithumb
import pandas as pd
import sys
from PyQt5 import uic
import pprint

# API 객체 생성
api_key = ""
secret = ""
with open("api.txt") as f:
    lines = f.readlines()
    api_key = lines[0].strip()
    secret = lines[1].strip()
# python-binance
client = Client(api_key=api_key, api_secret=secret)
# ccxt
binance = ccxt.binance(config={
    'apiKey': api_key,
    'secret': secret,
    'enableRateLimit': True,
    'options': {
        'defaultType': 'future'
    }
})
binance_seed = ccxt.binance(config={
    'apiKey': api_key,
    'secret': secret,
    'enableRateLimit': True,
})
btc_ohlcv_1m = binance.fetch_ohlcv("BTC/USDT", '1m')
df_1m = pd.DataFrame(btc_ohlcv_1m, columns=['datetime', 'open', 'high', 'low', 'close', 'volume'])

def get_High_Low_Point(df, size):
    closedata = df['close']
    timestamp = df['datetime']
    highdata = []
    lowdata = []

    for k, v in enumerate(closedata):

        if (k < size):
            highdata.append('0')
            lowdata.append('0')
            continue
        data = closedata[k - size:k + size + 1]
        if max(data) == v:
            highdata.append('high')
            lowdata.append('0')
        elif min(data) == v:
            highdata.append('0')
            lowdata.append('low')
        else:
            highdata.append('0')
            lowdata.append('0')
    high = pd.DataFrame({'timestamp': timestamp, 'high' : highdata})
    low = pd.DataFrame({'timestamp': timestamp, 'low': lowdata})

    return high, low


def get_long_spot(low, data_close, rsi):
    data_time = low['timestamp']
    lowdata = low['low']
    lowspot = {}

    for i in range(0, 500):
        if (lowdata[i] == '0'):
            continue
        else:
            lowspot[i] = lowdata[i]

    lowspot_keys = list(lowspot.keys())

    for i in range(0, len(lowspot_keys)):
        if i == 0:
            continue
        # print(data_close[lowspot_keys[i]], '<', data_close[lowspot_keys[i - 1]],rsi[lowspot_keys[i]], '>', rsi[lowspot_keys[i - 1]])
        if data_close[lowspot_keys[i]] < data_close[lowspot_keys[i - 1]] and rsi[lowspot_keys[i]] > rsi[
            lowspot_keys[i - 1]]:
            print(datetime.datetime.fromtimestamp(data_time[lowspot_keys[i]] / 1000), "는 매수점.")


def get_short_spot(high, data_close, rsi):
    data_time = high['timestamp']
    highdata = high['high']

    lowspot = {}

    for i in range(0, 500):
        if (highdata[i] == '0'):
            continue
        else:
            lowspot[i] = highdata[i]

    highspot_keys = list(lowspot.keys())

    for i in range(0, len(highspot_keys)):
        if i == 0:
            continue
        # print(data_close[highspot_keys[i]], '>', data_close[highspot_keys[i - 1]],rsi[highspot_keys[i]], '<', rsi[highspot_keys[i - 1]])
        if data_close[highspot_keys[i]] < data_close[highspot_keys[i - 1]] and rsi[highspot_keys[i]] > rsi[
            highspot_keys[i - 1]]:
            print(datetime.datetime.fromtimestamp(data_time[highspot_keys[i]] / 1000), "는 숏점.")


def getRSI(df):
    closedata = df.loc[480:499, 'close']
    print(closedata)
    delta = closedata.diff()
    ups, downs = delta.copy(), delta.copy()
    ups[ups < 0] = 0
    downs[downs > 0] = 0

    period = 14
    au = ups.ewm(alpha=1 / period, min_periods=period).mean()
    ad = downs.abs().ewm(alpha=1 / period, min_periods=period).mean()

    RS = au / ad
    RSI = pd.Series(100 - (100 / (1 + RS)))
    return RSI


def getMA20(df):

    ma20 = df['close'].rolling(window=20).mean()
    return ma20

def get_Boll(df):

    ma20 = pd.Series(getMA20(df), name='MIDDLE')
    STD = df['close'].rolling(window=20).std()
    lowerBound = pd.Series(ma20 - STD * 2, name='LOWER')
    upperBound = pd.Series(ma20 + STD * 2, name='UPPER')
    Boll = pd.concat([ma20, lowerBound, upperBound],axis=1)
    return Boll

balance_position = binance.fetch_balance()
positions = balance_position['info']['positions']



# 바이낸스 매수매도 연습
"""
order = binance.create_market_buy_order(
    symbol="BTC/USDT",
    amount=0.001
)
order = binance.create_market_sell_order(
    symbol="BTC/USDT",
    amount=0.001
)
"""


bp = None

for position in positions:
    if position["symbol"] == "BTCUSDT":
        bp = position

pl = (float(bp['initialMargin']) + float(bp['unrealizedProfit'])) / float(bp['initialMargin'])
pprint.pprint(bp)
print(pl)



"""
# 현재가 조회
btc_usdt = client.get_symbol_ticker(symbol="BTCUSDT")
btc = pybithumb.get_current_price("BTC")

# 호가창 조회
bithumb_orderbook = pybithumb.get_orderbook("BTC", limit=10)
binance_orderbook = client.get_order_book(symbol="BTCUSDT")

# 현물 계좌잔고
balance = clientAPI.get_asset_balance(asset='USDT')

# 선물 계좌 잔고
balance_future = binanceAPI.fetch_balance(params={"type": "future"})

# Symbol Info 얻기
info = binance.fetch_ticker('BTC/USDT')

# 과거데이터 조회
btc_ohlcv_15m = binance.fetch_ohlcv("BTC/USDT", '15m')
df_15m = pd.DataFrame(btc_ohlcv_15m, columns=['datetime', 'open', 'high', 'low', 'close',
                                              'volume'])
df_15m['datetime'] = pd.to_datetime(df_15m['datetime'], unit='ms')
df_15m.set_index('datetime', inplace=True)

# 시장가 선물 매수매도
order = binance.create_market_buy_order(
    symbol="BTC/USDT",
    amount=0.001
)
order = binance.create_market_sell_order(
    symbol="BTC/USDT",
    amount=0.001
)

#현재 포지션
balance = binance.fetch_balance()
positions = balance['info']['positions']
for position in positions:
    if position["symbol"] == "BTCUSDT":
        pprint.pprint(position)

#지정가 TP/SL
orders = [None] * 3
price = 19400

# - 지정가 매수
orders[0] = binance.create_order(
    symbol="BTC/USDT",
    type="LIMIT",
    side="buy",
    amount=0.001,
    price=price
)
# - 시장가 매수 (ex: 19500$)
orders[0] = binance.create_order(
    symbol="BTC/USDT",
    type="MARKET",
    side="buy",
    amount=0.001
)

# take profit
orders[1] = binance.create_order(
    symbol="BTC/USDT",
    type="TAKE_PROFIT",
    side="sell",
    amount=0.001,
    price=price,
    params={'stopPrice': 19600}
)

# stop loss
orders[2] = binance.create_order(
    symbol="BTC/USDT",
    type="STOP",
    side="sell",
    amount=0.001,
    price=price,
    params={'stopPrice': 19200}
)
"""
