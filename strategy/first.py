from my_logging import logger

class First():
    def __init__(self):
        self.direct = 'buy'
        self.backdirect = {'buy': 'sell', 'sell': 'buy'}
        self.last_price = 0
        self.my_store = []

    def start(self, cls, start_date):
        pass

    def tick(self, cls, asc, bid, date, coef):
        profit = 10
        if len(self.my_store) <= 10:
            self.my_store.append(asc)
        else:
            self.my_store.append(asc)
            start = self.my_store[-10]
            end = self.my_store[-1]
            if self.last_price == 0:
                self.last_price = asc
                extremum = (end-start) * coef
                if extremum < -5:
                    self.order(cls, asc, 'sell')
                if extremum > 5:
                    pass
                    # self.order(cls, asc, 'buy')
            else:
                if self.direct == 'buy':
                    profit_pt = (asc - self.last_price) * coef
                else:
                    profit_pt = (self.last_price - asc) * coef
                logger.debug('DifPrice: {} Coef: {}, Profit: {} Last-Price: {}'.format((asc - self.last_price), coef, profit_pt, self.last_price))
                if profit_pt > profit or profit_pt < -1*profit:
                    if profit_pt > profit:
                        logger.debug('plus')
                    else:
                        logger.debug('minus')
                    self.order(cls, asc, self.backdirect[self.direct])
                    self.last_price = 0


    def finish(self, cls, finish_date):
        if cls._count_item > 0:
            cls.sell(cls._count_item)
        else:
            cls.buy(cls._count_item*-1)

    def order(self, cls, asc, direct, count=1):

        if direct == 'buy':
            cls.buy(count)
            self.direct = 'buy'
        else:
            cls.sell(count)
            self.direct = 'sell'
