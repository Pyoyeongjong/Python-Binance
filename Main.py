import time
import pandas as pd
from PyQt5.QtWidgets import QApplication, QMainWindow
from binance.client import Client
import ccxt
import sys
from PyQt5 import uic
from PyQt5.QtCore import QThread, pyqtSignal

form_class = uic.loadUiType("resource/main.ui")[0]

client = None  ## python-binance


def getRSI(df):
    closedata = df.loc[480:499, 'close']
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
    Boll = pd.concat([ma20, lowerBound, upperBound], axis=1)
    return Boll


class MainWindow(QMainWindow, form_class):
    # 초기 데이터
    def __init__(self):
        super().__init__()
        self.positions = None
        self.binance = None  ## CCXT
        self.binance_seed = None  ## CCXT
        self.balance = None
        self.balance_seed = None
        self.islogin = False
        self.reverage = 0
        self.setupUi(self)
        self.resp = None
        self.leverage = None
        self.market = None
        # 알고리즘 데이터
        self.isBuy = False
        self.BPend = False
        self.isSell = False
        self.SPend = False
        self.Position = "None"
        self.order = None
        self.bp = None
        self.USDT = 0
        self.am = None
        self.pl = None

        self.ticker = "BTC"

        self.button.clicked.connect(self.clickBtn)
        self.revButton.clicked.connect(self.clickrevBtn)

        self.mww = MainWindowWorker()
        self.mww.dataSent.connect(self.fillData)

        self.maw = MainAlgorithmWorker()
        self.maw.dataSent.connect(self.algorithm)

    # 로그인, 초기 데이터 구현.
    def clickBtn(self):
        if self.button.text() == "매매시작":

            # 임시 자동 로그인
            with open("api.txt") as f:
                lines = f.readlines()
                apiKey = lines[0].strip()
                secKey = lines[1].strip()
            # apiKey = self.apiKey.text()
            # secKey = self.secKey.text()

            if len(apiKey) <= 3 or len(secKey) <= 3:
                self.textEdit.append("Type a : Key가 올바르지 않습니다.")
                return
            else:
                self.binance = ccxt.binance(config={
                    'apiKey': apiKey,
                    'secret': secKey,
                    'enableRateLimit': True,
                    'options': {
                        'defaultType': 'future'
                    }
                })
                self.binance_seed = ccxt.binance(config={
                    'apiKey': apiKey,
                    'secret': secKey,
                    'enableRateLimit': True,
                })

                try:
                    self.balance = self.binance.fetch_balance(params={"type": "future"})
                except:
                    self.textEdit.append("Type b : Key가 올바르지 않습니다.")
                    return

            self.button.setText("매매중지")
            self.textEdit.append("----START----")
            self.islogin = True

            self.mww.start()
            self.maw.start()
            symbol = "BTC/USDT"
            self.market = self.binance.market(symbol)
            self.leverage = 0

            self.textEdit.append(f"보유현금 :{self.balance['info']['totalCrossWalletBalance']}USDT")
            text = "매매중지"
            self.button.setText(text)
        else:
            self.textEdit.append("----END----")
            text = "매매시작"
            self.button.setText(text)

    # 레버리지 변경 구현, 현재 폐지
    def clickrevBtn(self):
        pass
        # 레버리지 잠금.
        """
                if self.islogin == False:
                    self.textEdit.append("로그인하지 않았습니다.")
                    return
                if(self.revLine.text()<self)
                self.reverage = self.revLine.text()
                self.leverage = int(self.reverage)
                print(self.leverage)

                self.resp = self.binance.fapiPrivate_post_leverage({
                    'symbol': self.market['id'],
                    'leverage': self.leverage
                })
                self.rev.setText(f"{self.reverage} 배")
                self.textEdit.append("레버리지가 변경되었습니다.")
        """

    # 초마다 데이터 업데이트
    def fillData(self):

        if self.balance is None:
            print('No balance')
            pass
        self.balance = self.binance.fetch_balance(params={"type": "future"})
        btc = self.binance.fetch_ticker("BTC/USDT")

        balance_position = self.binance.fetch_balance()
        self.positions = balance_position['info']['positions']
        self.balance_seed = self.binance_seed.fetch_balance()
        self.free.setText(f"{self.balance['USDT']['free']:.2f} USDT")
        self.used.setText(f"{self.balance['USDT']['used']:.2f} USDT")
        self.total.setText(f"{self.balance['USDT']['total']:.2f} USDT")
        self.USDT = float(self.balance['USDT']['total'])
        self.money.setText(f"{self.balance_seed['USDT']['free']:.2f} USDT")

        for position in self.positions:
            if position["symbol"] == "BTCUSDT":
                if float(position['initialMargin']) == 0:
                    self.LS.setText("No Position")
                    self.Position = "None"
                else:
                    if (float(btc['close']) < float(position['entryPrice'])) and (
                            float(position['unrealizedProfit']) < 0):
                        self.LS.setText("Long")
                        self.Position = "Long"
                    else:
                        self.LS.setText("Short")
                        self.Position = "Short"

                self.rev.setText(f"{float(position['leverage']):.0f} 배")
                self.leverage = int(position['leverage'])
                self.initialMargin.setText(f"{float(position['isolatedWallet']):.2f} USDT")
                self.entryPrice.setText(f"{float(position['entryPrice']):.2f}")
                self.unrealizedProfit.setText(f"{float(position['unrealizedProfit']):.2f} USDT")
                self.tp.setText(f"{float(position['entryPrice']) * 1.01:.2f}")
                self.sl.setText(f"{float(position['entryPrice']) * 0.99:.2f}")

    # 매매 알고리즘
    def algorithm(self):

        for position in self.positions:
            if position["symbol"] == "BTCUSDT":
                self.bp = position

        if self.Position == "None":
            self.pl = 1
        else:
            self.pl = (float(self.bp['initialMargin']) + float(self.bp['unrealizedProfit'])) / float(self.bp['initialMargin'])


        btc_ohlcv_1m = self.binance.fetch_ohlcv("BTC/USDT", '1m')
        btc_1m = pd.DataFrame(btc_ohlcv_1m, columns=['datetime', 'open', 'high', 'low', 'close', 'volume'])
        self.am = round(float(self.USDT * 0.5 * self.leverage / btc_1m.loc[499, 'close']), 3)
        btc_1m_rsi = getRSI(btc_1m)
        btc_1m_boll = get_Boll(btc_1m)

        if float(btc_1m_rsi[499]) < 25 and float(btc_1m_boll.loc[499, 'LOWER']) > float(btc_1m.loc[499, 'low']):
            self.isBuy = True
        else:
            self.isBuy = False
        if float(btc_1m_rsi[499]) > 75 and float(btc_1m_boll.loc[499, 'UPPER']) < float(btc_1m.loc[499, 'high']):
            self.isSell = True
        else:
            self.isSell = False
        if (float(btc_1m_rsi[499]) > 65 and float(btc_1m_boll.loc[499, 'LOWER']) > float(btc_1m.loc[499, 'low'])) \
                or self.pl < 0.9:
            self.BPend = True
        else:
            self.BPend = False
        if (float(btc_1m_rsi[499]) < 25 and float(btc_1m_boll.loc[499, 'LOWER']) > float(btc_1m.loc[499, 'low'])) \
                or self.pl > 1.1:
            self.SPend = True
        else:
            self.SPend = False
        print(self.isBuy, self.isSell, self.BPend, self.SPend, self.Position, self.am, self.pl)

        if self.Position == "None":
            if self.isBuy:
                self.order = self.binance.create_market_buy_order(
                    symbol="BTC/USDT",
                    amount=self.am
                )
                self.Position = "Long"
                self.textEdit.append("공매수 완료. 포지션 : 롱")
            elif self.isSell:
                self.order = self.binance.create_market_sell_order(
                    symbol="BTC/USDT",
                    amount=self.am
                )
                self.Position = "Short"
                self.textEdit.append("공매도 완료. 포지션 : 숏")
        elif self.Position != "None":
            # 손절매
            if self.BPend:
                if self.Position == "Long":
                    self.order = self.binance.create_market_sell_order(
                        symbol="BTC/USDT",
                        amount=self.am
                    )
                    self.textEdit.append("공매수 정리. 결과 : 손절")
                elif self.Position == "Short":
                    self.order = self.binance.create_market_buy_order(
                        symbol="BTC/USDT",
                        amount=self.am
                    )
                    self.textEdit.append("공매도 정리. 결과 : 손절")
                self.Position = "None"
            # 익절매
            if self.SPend:
                if self.Position == "Long":
                    self.order = self.binance.create_market_sell_order(
                        symbol="BTC/USDT",
                        amount=self.am
                    )
                    self.textEdit.append("공매수 정리. 결과 : 익절")
                elif self.Position == "Short":
                    self.order = self.binance.create_market_buy_order(
                        symbol="BTC/USDT",
                        amount=self.am
                    )
                    self.textEdit.append("공매도 정리. 결과 : 손절")
                self.Position = "None"

    # 창 종료
    def closeEvent(self, event):
        self.mww.close()


# 워커 쓰레드.
class MainWindowWorker(QThread):
    dataSent = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.alive = True

    def run(self):
        while self.alive:
            self.dataSent.emit()
            # 얼마나 빨리 업뎃할지.
            time.sleep(1)

    def close(self):
        self.alive = False


# 워커 쓰레드.
class MainAlgorithmWorker(QThread):
    dataSent = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.alive = True

    def run(self):
        while self.alive:
            self.dataSent.emit()
            # 얼마나 빨리 업뎃할지.
            time.sleep(1)

    def close(self):
        self.alive = False


if __name__ == "__main__":
    app = QApplication(sys.argv)
    mw = MainWindow()
    mw.show()
    exit(app.exec_())
