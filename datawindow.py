import ccxt
import time
from binance.client import Client
from PyQt5.QtWidgets import QWidget
from PyQt5 import uic
from PyQt5.QtCore import QThread, pyqtSignal
import pandas as pd

# python-binance
client = Client()
# ccxt
binance = ccxt.binance()


class DatawindowWidget(QWidget):
    def __init__(self, parent=None, ticker="BTCUSDT"):
        super().__init__(parent)
        uic.loadUi("resource/datawindow.ui", self)
        self.ticker = ticker

        self.dww = DatawindowWorker(ticker)
        self.dww.dataSent.connect(self.fillData)
        self.dww.start()

    def fillData(self, rsi_1m, boll_1m, short_going, long_going):

        self.rsi1m.setText(f"{rsi_1m:.2f}")
        self.boll1m.setText(f"{boll_1m:.2f}")
        self.shortgoing.setText(f"{short_going:.2f}")
        self.longgoing.setText(f"{long_going:.2f}")

    def closeEvent(self, event):
        self.dww.close()

class DatawindowWorker(QThread):
    dataSent = pyqtSignal(float, float, float, float)

    def __init__(self, ticker):
        super().__init__()
        self.ticker = ticker
        self.alive = True

    def run(self):
        while self.alive:
            btc_ohlcv_1m = binance.fetch_ohlcv("BTC/USDT", '1m')
            df_1m = pd.DataFrame(btc_ohlcv_1m, columns=['datetime', 'open', 'high', 'low', 'close', 'volume'])
            rsi_1m = getRSI(df_1m)
            boll_1m = get_Boll(df_1m)

            self.dataSent.emit(float(rsi_1m[499]),
                               float(boll_1m.loc[499, 'UPPER']),
                               float(boll_1m.loc[499, 'MIDDLE']),
                               float(boll_1m.loc[499, 'LOWER']))

            time.sleep(1)

    def close(self):
        self.alive = False


def getRSI(df):
    closedata = df['close']
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


if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    dw = DatawindowWidget()
    dw.show()
    exit(app.exec_())