import settings
import etoro
from interfaces.advisor import ABCAdvisor
from strategy import StrategyManager

class StrategyAdvisor(ABCAdvisor):

    def __init__(self, loop):
        self.objloop = loop
        self.swop_buy = 0.0003
        self.total_marg = 0
        self.object_strategy = StrategyManager(0, '', buy=self.buy, sell=self.sell)
        self.object_strategy.start()
        self.ask = 0
        self.bid = 0

    async def loop(self):
        history_items = await etoro.get_history(count=2)
        if 'Candles' in history_items and history_items['Candles'] is not None:
            self.ask = history_items['Candles'][0]['Candles'][0]['Close']
            self.bid = self.ask + self.swop_buy
            self.object_strategy.tick(self.ask, self.bid, history_items['Candles'][0]['Candles'][0]['FromDate'])

    def buy(self, count):
        print('buy', count, self.bid)

    def sell(self, count):
        print('sell', count, self.ask)