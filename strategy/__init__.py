from strategy.first import First
from interfaces.strategy import ABCStrategy
from settings import trade_strategy
import sys
from my_logging import logger
import matplotlib.pyplot as plt
import uuid


class StrategyManager(ABCStrategy):

    def __init__(self, balance, instrument='', trade_obj=None, buy=None, sell=None):
        self._start_balance = balance
        self._balance = balance
        self._count_item = 0
        self.asc = 0
        self.bid = 0
        self._counter = {'total': 0, 'buy': 0, 'sell': 0}
        self.balance_change = []
        self.parent = trade_obj
        self.buy_method = buy
        self.sell_method = sell
        if hasattr(sys.modules[__name__], trade_strategy):
            self.class_strategy = getattr(sys.modules[__name__], trade_strategy)()

    def start(self, start_asc=None, start_bid=None, start_date=None):
        logger.info('Start Date: {} Start balance: {}!'.format(start_date, self._balance))
        self.class_strategy.start(self, start_date)

    def tick(self, asc, bid, date):
        split_asc = str(asc).split('.')
        if len(split_asc[0]) > 1:
            new_bid = self.bid + 0.03
            coef = 100
        else:
            new_bid = self.bid + 0.0003
            coef = 10000
        self.asc = asc
        if asc == bid:
            self.bid = new_bid
        else:
            self.bid = asc
        self.class_strategy.tick(self, asc, bid, date, coef)
        if not self.balance_change or (self.balance_change and self.balance_change[-1] != self._balance):
            if not self._count_item:
                self.balance_change.append(self._balance)
        logger.debug('Asc: {} Balance: {}. Total: {} Buy: {} Sell: {} Orders: {}'.format(asc,
                                                                                 self._balance,
                                                                                 self._counter['total'],
                                                                                 self._counter['buy'],
                                                                                 self._counter['sell'],
                                                                                 self._count_item))

    def finish(self, finish_asc, finish_bid, finish_date):
        self.class_strategy.finish(self, finish_date)
        logger.info('Finish Date: {} Balance: {}. Total: {} Buy: {} Sell: {} Orders: {} Marg: {}'.format(finish_date,
                                                                                       self._balance,
                                                                                       self._counter['total'],
                                                                                       self._counter['buy'],
                                                                                       self._counter['sell'],
                                                                                       self._count_item,
                                                                                       self._balance - self._start_balance))
        if self.parent is not None:
            self.parent.total_marg += self._balance - self._start_balance
        self.balance_change.append(self._balance)
        plt.plot(self.balance_change, color='red')
        plt.savefig("temp/mybalance/my_balance{}.png".format(uuid.uuid4()), dpi=200)
        plt.close()


    def buy(self, count):
        if self.buy_method is None:
            if count * self.asc > self._balance and self._count_item >= 0:
                logger.info('Buy. Not enough money! Need: {}. Balance: {}'.format(count * self.asc, self._balance))
            self._counter['total'] += 1
            self._counter['buy'] += 1
            if self.asc > 0:
                tmp_count = self._count_item + count
                self._balance -= count * self.asc
                self._count_item = tmp_count
                logger.debug('Buy asc: {}'.format(self.asc))
        else:
            self.buy_method(count)

    def sell(self, count):
        if self.sell_method is None:
            if count * self.asc > self._balance and self._count_item <= 0:
                logger.info('Sell. Not enough money! Need: {}. Balance: {}'.format(count * self.asc, self._balance))
                return False
            self._counter['total'] += 1
            self._counter['sell'] += 1
            if self.asc > 0:
                tmp_count = self._count_item - count
                self._balance += count * self.asc
                self._count_item = tmp_count
                logger.debug('Sell asc: {}'.format(self.asc))
        else:
            self.sell_method(count)