from strategy.first import First
from interfaces.strategy import ABCStrategy
from settings import trade_strategy
import sys
from my_logging import logger
import matplotlib.pyplot as plt


class StrategyManager(ABCStrategy):

    def __init__(self, balance, instrument, trade_obj):
        self._balance = balance
        self._count_item = 0
        self.asc = 0
        self.bid = 0
        self._counter = {'total': 0, 'buy': 0, 'sell': 0}
        self.balance_change = []
        if hasattr(sys.modules[__name__], trade_strategy):
            self.class_strategy = getattr(sys.modules[__name__], trade_strategy)()

    def start(self, start_asc, start_bid, start_date):
        logger.info('Date: {} Start balance: {}!'.format(start_date, self._balance))
        self.class_strategy.start(self, start_date)

    def tick(self, asc, bid, date):
        self.asc = asc
        self.bid = asc
        self.class_strategy.tick(self, asc, bid, date)
        if not self.balance_change or (self.balance_change and self.balance_change[-1] != self._balance):
            self.balance_change.append(self._balance)
        logger.debug('Balance: {}. Total: {} Buy: {} Sell: {} Orders: {}'.format(self._balance,
                                                                                 self._counter['total'],
                                                                                 self._counter['buy'],
                                                                                 self._counter['sell'],
                                                                                 self._count_item))

    def finish(self, finish_asc, finish_bid, finish_date):
        self.class_strategy.finish(self, finish_date)
        logger.info('Finish Balance: {}. Total: {} Buy: {} Sell: {} Orders: {}'.format(self._balance,
                                                                                       self._counter['total'],
                                                                                       self._counter['buy'],
                                                                                       self._counter['sell'],
                                                                                       self._count_item))
        logger.info('Finish date: {}'.format(finish_date))
        self.balance_change.append(self._balance)
        plt.plot(self.balance_change, color='red')
        plt.savefig("temp/my_balance.png", dpi=200)


    def buy(self, count):
        if count * self.asc > self._balance and self._count_item > 0:
            logger.info('Not enough money!')
            return False
        self._counter['total'] += 1
        self._counter['buy'] += 1
        if self.asc > 0:
            tmp_count = self._count_item + count
            if self._count_item < 0 and tmp_count >= 0:
                _count = count + self._count_item
                self._balance -= _count * self.asc
                self._balance += (count - _count) * self.asc
            elif tmp_count > 0:
                self._balance -= count * self.asc
            elif tmp_count < 0:
                self._balance += count * self.asc
            self._count_item = tmp_count

    def sell(self, count):
        if count * self.asc > self._balance and self._count_item < 0:
            logger.info('Not enough money!')
            return False
        self._counter['total'] += 1
        self._counter['sell'] += 1
        if self.asc > 0:
            tmp_count = self._count_item - count
            if self._count_item > 0 and tmp_count <= 0:
                _count = count - self._count_item
                self._balance -= _count * self.asc
                self._balance += (count - _count) * self.asc
            elif tmp_count > 0:
                self._balance += count * self.asc
            elif tmp_count < 0:
                self._balance -= count * self.asc
            self._count_item = tmp_count