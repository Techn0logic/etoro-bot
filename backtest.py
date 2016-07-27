import strategy
from backtesting.backtesting import BackTesting
import etoro
import asyncio
import os
from my_logging import logger
import time


class BaseTrade(object):
    def __init__(self):
        self.instrument = 'EURUSD'
        self.balance = 5000
        self.shoulder = 100
        self.total_marg = 0

    def back_testing(self, dataframe, strategy, trade_obj):
        BackTesting(dataframe, strategy, self.balance, self.instrument, trade_obj)

if __name__ == "__main__":
    filelist = [f for f in os.listdir("temp/mybalance/") if f.endswith(".png")]
    for f in filelist:
        os.remove("temp/mybalance/" + f)
    trade_obj = BaseTrade()
    loop = asyncio.get_event_loop()
    for i in range(1, 8):
        dataframe = []
        history_items = loop.run_until_complete(etoro.get_history(i))
        if 'Candles' in history_items and history_items['Candles'] is not None:
            if history_items['Candles'][0]['Candles']:
                for item in history_items['Candles'][0]['Candles']:
                    dataframe.append({'asc': item['Close'],
                                   'bid': item['Open'],
                                   'date': item['FromDate']})
            trade_obj.back_testing(dataframe, strategy.StrategyManager, trade_obj)
        time.sleep(1)
    logger.info('Total marg: {}'.format(trade_obj.total_marg))