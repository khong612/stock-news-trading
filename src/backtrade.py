from __future__ import (absolute_import, division, print_function, unicode_literals)

import backtrader as bt
import datetime
import os.path, sys
from scrape import get_stock


class Sentiment(bt.Indicator):
    lines = ("sentiment",)
    plotinfo = dict(
        plotymargin=0.15,
        plothlines=[0],
        plotyticks=[1.0, 0, -1.0])

    def next(self):
        self.date = self.data.datetime
        date = bt.num2date(self.date[0]).date()
        prev_sentiment = self.sentiment
        if date in date_sentiment:
            self.sentiment = date_sentiment[date]
        self.lines.sentiment[0] = self.sentiment


class SentimentStrategy(bt.Strategy):
    params = (
        ("maperiod", 15),
        ("printlog", True),
    )

    def log(self, txt, dt=None, doprint=False):
        """Logging function for this strategy"""
        if self.params.printlog or doprint:
            dt = dt or self.datas[0].datetime.date(0)
            print("%s, %s" % (dt.isoformat(), txt))

    def __init__(self):
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close

        # To keep track of pending orders and buy price/commission
        self.order = None
        self.buyprice = None
        self.buycomm = None
        self.sma = bt.indicators.SimpleMovingAverage(self.datas[0], period=self.params.maperiod)
        self.date = self.data.datetime
        self.sentiment = None
        Sentiment(self.data)

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    "BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f" %
                    (order.executed.price,
                     order.executed.value,
                     order.executed.comm))

                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:  # Sell
                self.log("SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f" %
                         (order.executed.price,
                          order.executed.value,
                          order.executed.comm))

            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log("Order Canceled/Margin/Rejected")

        # Write down: no pending order
        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log("OPERATION PROFIT, GROSS %.2f, NET %.2f" %
                 (trade.pnl, trade.pnlcomm))

    def next(self):
        # Simply log the closing price of the series from the reference
        self.log("Close, %.2f" % self.dataclose[0])

        date = bt.num2date(self.date[0]).date()
        prev_sentiment = self.sentiment
        if date in date_sentiment:
            self.sentiment = date_sentiment[date]

        # Check if an order is pending ... if yes, we cannot send a 2nd one
        if self.order:
            return
        print("Sentiment score: " + str(self.sentiment))

        # Previous sentiment exists
        if prev_sentiment:
            # Buy if position is less than 50 shares, current close is more than SMA, and sentiment has increased by >= 0.5
            if self.position.size < 50 and self.dataclose[0] > self.sma[0] and self.sentiment - prev_sentiment >= 0.5:
                self.log("BUY CREATE, %.2f" % self.dataclose[0])
                self.order = self.buy()

            # Sell if position exists, current close is less than SMA, and sentiment has decreased by >= 0.5
            elif self.position and self.dataclose[0] < self.sma[0] and self.sentiment - prev_sentiment <= -0.5:
                self.log("SELL CREATE, %.2f" % self.dataclose[0])
                self.order = self.sell()

    def stop(self):
        self.log("(SMA Period %2d) Ending Value %.2f" %
                 (self.params.maperiod, self.broker.getvalue()), doprint=True)


if __name__ == "__main__":
    name = "Tesla"
    ticker = "TSLA"
    date_sentiment = get_stock(name, ticker, 101)
    # print(date_sentiment)
    cerebro = bt.Cerebro()
    cerebro.addstrategy(SentimentStrategy)

    data = bt.feeds.YahooFinanceData(
        dataname = ticker,
        fromdate = min(date_sentiment.keys()),
        todate = max(date_sentiment.keys()),
        reverse = False
    )

    cerebro.adddata(data)
    cerebro.addsizer(bt.sizers.FixedSize, stake=10)
    cerebro.broker.setcash(100000.0)
    cerebro.broker.setcommission(commission=0.001)
    print("Starting Portfolio Value: %.2f" % cerebro.broker.getvalue())
    cerebro.run()
    print("Final Portfolio Value: %.2f" % cerebro.broker.getvalue())

    cerebro.plot()
