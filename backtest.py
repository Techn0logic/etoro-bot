import strategy
from backtesting.backtesting import BackTesting
import etoro
import asyncio


class BaseTrade(object):
    def __init__(self):
        self.instrument = 'EURUSD'
        self.balance = 100
        self.shoulder = 100

    def back_testing(self, dataframe, strategy, trade_obj):
        BackTesting(dataframe, strategy, self.balance, self.instrument, trade_obj)

if __name__ == "__main__":
    dataframe = []
    trade_obj = BaseTrade()
    loop = asyncio.get_event_loop()
    history_items = loop.run_until_complete(etoro.get_history())
    for item in history_items['Candles'][0]['Candles']:
        dataframe.append({'asc': item['Close'],
                       'bid': item['Open'],
                       'date': item['FromDate']})
    trade_obj.back_testing(dataframe, strategy.StrategyManager, trade_obj)