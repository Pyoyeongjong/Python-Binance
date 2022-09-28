import sys
import time

import ccxt
from PyQt5.QtWidgets import QWidget
from PyQt5 import uic
from PyQt5.QtCore import QThread, pyqtSignal

binance = ccxt.binance()


class OverviewWidget(QWidget):
    def __init__(self, parent=None, ticker="BTC"):
        super().__init__(parent)
        uic.loadUi("resource/overview.ui", self)
        self.ticker = ticker

        self.ovw = OverViewWorker(ticker)
        self.ovw.dataSent.connect(self.fillData)
        self.ovw.start()

    def fillData(self, currPrice, chgRate, volume, highPrice, value,
                 lowPrice, change, prevClosePrice):

        self.label_1.setText(f"{currPrice:,}")
        self.label_2.setText(f"{chgRate:+.2f}%")
        self.label_4.setText(f"{volume:.4f} {self.ticker}")
        self.label_6.setText(f"{highPrice:,}")
        self.label_8.setText(f"{value / 100000000:,.1f} USD")
        self.label_10.setText(f"{lowPrice:,}")
        self.label_12.setText(f"{change:,}")
        self.label_14.setText(f"{prevClosePrice:,}")

        self.__updateStyle()

    def closeEvent(self, event):
        self.ovw.close()

    def __updateStyle(self):

        if '-' in self.label_2.text():
            self.label_1.setStyleSheet("color:blue;")
            self.label_2.setStyleSheet("background-color:blue;color:white")
        else:
            self.label_1.setStyleSheet("color:red;")
            self.label_2.setStyleSheet("background-color:red;color:white")


class OverViewWorker(QThread):
    dataSent = pyqtSignal(float, float, float, float, float, float,
                          float, float)

    def __init__(self, ticker):
        super().__init__()
        self.ticker = ticker
        self.alive = True

    def run(self):

        while self.alive:
            data = binance.fetch_ticker('BTC/USDT')
            self.dataSent.emit(float(data['close']),
                               float(data['percentage']),
                               float(data['baseVolume']),
                               float(data['high']),
                               float(data['quoteVolume']),
                               float(data['low']),
                               float(data['change']),
                               float(data['previousClose']))
            time.sleep(1)

    def close(self):
        self.alive = False


if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    ob = OverviewWidget()
    ob.show()
    exit(app.exec_())