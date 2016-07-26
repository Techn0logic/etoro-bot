class First():
    def __init__(self):
        self.direct = 'buy'
        self.backdirect = {'buy': 'sell', 'sell': 'buy'}
        self.last_price = 0
        self.my_store = []

    def start(self, cls, start_date):
        pass

    def tick(self, cls, asc, bid, date):
        count = 1
        profit = 10
        if len(self.my_store) <= 10:
            self.my_store.append(asc)
        else:
            self.my_store.append(asc)
            start = self.my_store[-10]
            end = self.my_store[-1]
            if self.last_price == 0:
                self.last_price = asc
                if start > end:
                    self.order(cls, asc, 'sell')
                else:
                    self.order(cls, asc, 'buy')
            else:
                if self.direct == 'buy':
                    profit_pt = (asc - self.last_price) * 1000
                else:
                    profit_pt = (self.last_price - asc) * 1000
                if profit_pt > profit or profit_pt/2 < -1*profit:
                    self.order(cls, asc, self.backdirect[self.direct])
                # print(profit_pt)


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
