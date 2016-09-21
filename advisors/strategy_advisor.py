import settings
import aiohttp
import etoro
from interfaces.advisor import ABCAdvisor
from strategy import StrategyManager
from my_logging import logger as logging
import datetime


class StrategyAdvisor(ABCAdvisor):

    def __init__(self, loop, **kwargs):
        if 'messenger' in kwargs:
            kwargs['messenger'].clients.append(self)
        self.objloop = loop
        self.swop_buy = 0.0003
        self.total_marg = 0
        self.session = aiohttp.ClientSession(loop=loop)
        self.account_type = settings.account_type
        self.user_portfolio = {}
        self.instruments_rate = {}
        self.object_strategy = StrategyManager(0, '', buy=self.buy, sell=self.sell)
        self.object_strategy.start()
        self.ask = 0
        self.bid = 0
        self.exit_orders = []
        self.close_orders = {}
        self.fine_orders = {}
        self.message = ''

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
        self.instruments_rate = await etoro.instruments_rate(self.session)
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
            position_id = position['CID']
            instrument_name = self.instruments[position['InstrumentID']]['SymbolFull'];
            instrument_current_price = self.instruments_rate[position['InstrumentID']]['LastExecution']
            instrument_my_price = position['OpenRate']
            instrument_is_buy = position["IsBuy"]
            if instrument_name in self.close_orders and position['InstrumentID'] not in self.exit_orders:
                del self.close_orders[instrument_name]
            if not instrument_is_buy:
                fee_relative = (instrument_my_price*100/instrument_current_price) - 100
                fee_absolute = instrument_my_price-instrument_current_price
            else:
                fee_relative = (instrument_current_price*100/instrument_my_price) - 100
                fee_absolute = instrument_current_price-instrument_my_price
            logging.info('{}: {}'.format(instrument_name, fee_relative))
            if fee_relative < -1.5 and position['InstrumentID'] not in self.exit_orders:
                self.message = 'Firs case. I have tried your order. {}'.format(instrument_name)
                await etoro.close_order(self.session, position_id)
                self.close_orders[instrument_name] = instrument_current_price
                etoro.helpers.set_cache('self.close_orders', self.close_orders)
            if fee_relative > 1.5 and instrument_name not in self.fine_orders:
                self.fine_orders[instrument_name] = fee_relative
            if instrument_name in self.fine_orders:
                if fee_relative > self.fine_orders[instrument_name]:
                    self.fine_orders[instrument_name] = fee_relative
                if (self.fine_orders[instrument_name] - fee_relative) >= 1.5:
                    self.message = 'Second case. I have tried your order. {}'.format(instrument_name)
                    await etoro.close_order(self.session, position_id)
                    self.close_orders[instrument_name] = instrument_current_price
                    etoro.helpers.set_cache('close_orders', self.close_orders)
                    del self.fine_orders[instrument_name]

    async def fast_grow(self):
        pass

    def get_message(self):
        return self.message

    def buy(self, count):
        print('buy', count, self.bid)

    def sell(self, count):
        print('sell', count, self.ask)