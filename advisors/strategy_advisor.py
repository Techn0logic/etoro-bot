import settings
import etoro
from interfaces.advisor import ABCAdvisor
from strategy import StrategyManager
from my_logging import logger as logging
import datetime
from collections import deque


class StrategyAdvisor(ABCAdvisor):

    def __init__(self, loop, **kwargs):
        super().__init__(loop, **kwargs)
        self.objloop = loop
        self.swop_buy = 0.0003
        self.total_marg = 0
        self.account_type = settings.account_type
        self.user_portfolio = {}
        self.instruments = {}
        self.instruments_rate = {}
        self.object_strategy = StrategyManager(0, '', buy=self.buy, sell=self.sell)
        self.object_strategy.start()
        self.ask = 0
        self.bid = 0
        self.exit_orders = []
        self.close_orders = {}
        self.fine_orders = {}
        self.watch_instuments_id = {}

    async def loop(self):
        datetime_obj = datetime.datetime.now()
        week_day = datetime_obj.weekday()
        if week_day == 6 and week_day == 5:
            return False
        await self.build_data()

    async def build_data(self):
        history_items = await etoro.get_history(count=2)
        self.close_orders = etoro.helpers.get_cache('self.close_orders', 0)
        self.fine_orders = etoro.helpers.get_cache('self.fine_orders', 0)
        if not self.close_orders:
            self.close_orders = {}
        if not self.fine_orders:
            self.fine_orders = {}
        if 'Candles' in history_items and history_items['Candles'] is not None:
            self.ask = history_items['Candles'][0]['Candles'][0]['Close']
            self.bid = self.ask + self.swop_buy
            self.object_strategy.tick(self.ask, self.bid, history_items['Candles'][0]['Candles'][0]['FromDate'])
        content = await etoro.login(self.session, only_info=True)
        if "AggregatedResult" not in content:
            content = await etoro.login(self.session, account_type=self.account_type)
        self.user_portfolio = content["AggregatedResult"]["ApiResponses"]["PrivatePortfolio"]["Content"][
            "ClientPortfolio"]

        self.instruments_rate = etoro.helpers.get_cache('instruments_rate', (1/4))
        if not self.instruments_rate:
            self.instruments_rate = await etoro.instruments_rate(self.session)
            etoro.helpers.set_cache('instruments_rate', self.instruments_rate)
        self.instruments_rate = {instrument['InstrumentID']: instrument for instrument in
                                 self.instruments_rate['Rates']}

        self.instruments = etoro.helpers.get_cache('instruments', 20)
        if not self.instruments:
            self.instruments = await etoro.instruments(self.session)
            etoro.helpers.set_cache('instruments', self.instruments)
        self.instruments = {instrument['InstrumentID']: instrument for instrument in
                            self.instruments['InstrumentDisplayDatas']}
        self.exit_orders = [order['InstrumentID'] for order in self.user_portfolio['ExitOrders']]
        await self.check_position()

    async def check_position(self):
        for position in self.user_portfolio['Positions']:
            if position['InstrumentID'] in self.instruments and position['InstrumentID'] in self.instruments_rate:
                position_id = position['PositionID']
                instrument_name = self.instruments[position['InstrumentID']]['SymbolFull']
                instrument_current_price = self.instruments_rate[position['InstrumentID']]['LastExecution']
                instrument_my_price = position['OpenRate']
                instrument_is_buy = position["IsBuy"]
                if instrument_name in self.close_orders and \
                                self.close_orders[instrument_name] > instrument_current_price:
                    self.message = 'Insrument {} now is fine'.format(instrument_name)
                    logging.debug('Insrument {} now is fine'.format(instrument_name))
                    del self.close_orders[instrument_name]
                if not instrument_is_buy:
                    fee_relative = (instrument_my_price*100/instrument_current_price) - 100
                    fee_absolute = instrument_my_price-instrument_current_price
                else:
                    fee_relative = (instrument_current_price*100/instrument_my_price) - 100
                    fee_absolute = instrument_current_price-instrument_my_price
                logging.debug('{}: {}'.format(instrument_name, fee_relative))
                if fee_relative < (-1*settings.fee_relative) and position['InstrumentID'] not in self.exit_orders:
                    self.message = 'Firs case. I have tried your order. {}'.format(instrument_name)
                    await etoro.close_order(self.session, position_id, demo=False)
                    self.close_orders[instrument_name] = instrument_current_price
                if fee_relative > settings.fee_relative and instrument_name not in self.fine_orders:
                    self.fine_orders[instrument_name] = fee_relative
                if instrument_name in self.fine_orders:
                    if fee_relative > self.fine_orders[instrument_name]:
                        self.fine_orders[instrument_name] = fee_relative
                    if (self.fine_orders[instrument_name] - fee_relative) >= settings.fee_relative:
                        self.message = 'Second case. I have tried your order. {}'.format(instrument_name)
                        await etoro.close_order(self.session, position_id, demo=False)
                        self.close_orders[instrument_name] = instrument_current_price
                        del self.fine_orders[instrument_name]
        etoro.helpers.set_cache('close_orders', self.close_orders)

    async def fast_change_detect(self):
        if not self.instruments:
            return False
        lists = etoro.helpers.get_cache('watch_list', 10)
        if not lists:
            lists = await etoro.watch_list(self.session)
            if 'Watchlists' in lists:
                etoro.helpers.set_cache('watch_list', lists)
            else:
                return False
        for watch_list in lists['Watchlists']:
            for item_list in watch_list['Items']:
                if item_list['ItemType'] == 'Instrument' and item_list['ItemId'] not in self.watch_instuments_id:
                    self.watch_instuments_id[item_list['ItemId']] = deque([])
        if not self.instruments_rate:
            self.instruments_rate = await etoro.instruments_rate(self.session)
            self.instruments_rate = {instrument['InstrumentID']: instrument for instrument in
                                     self.instruments_rate['Rates']}
        for key in self.instruments_rate:
            if key in self.watch_instuments_id:
                self.watch_instuments_id[key].append(self.instruments_rate[key]['LastExecution'])
                if len(self.watch_instuments_id[key]) > 10:
                    changing = self.watch_instuments_id[key][0]/self.watch_instuments_id[key][-1]
                    if changing > 1:
                        changing = (1.0 - 1/changing)*-1
                    else:
                        changing = 1.0 - changing
                    if changing > settings.fast_grow_points or changing < (-1*settings.fast_grow_points):
                        logging.info('Changing for {} is {}'.format(self.instruments[key]['SymbolFull'], str(changing)))
                        self.message = 'Changing {} is {}'.format(self.instruments[key]['SymbolFull'],
                                                              str(changing))
                    self.watch_instuments_id[key].popleft()

    def buy(self, count):
        print('buy', count, self.bid)

    def sell(self, count):
        print('sell', count, self.ask)