import settings
import aiohttp
import etoro
from interfaces.advisor import ABCAdvisor
from strategy import StrategyManager


class StrategyAdvisor(ABCAdvisor):

    def __init__(self, loop):
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

    async def loop(self):
        history_items = await etoro.get_history(count=2)
        close_orders = etoro.helpers.get_cache('close_orders', 0)
        fine_orders = etoro.helpers.get_cache('fine_orders', 0)
        if not close_orders:
            close_orders = {}
        if not fine_orders:
            fine_orders = {}
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
        exit_orders = [order['InstrumentID'] for order in self.user_portfolio['ExitOrders']]
        for position in self.user_portfolio['Positions']:
            position_id = position['CID']
            instrument_name = self.instruments[position['InstrumentID']]['SymbolFull'];
            instrument_current_price = self.instruments_rate[position['InstrumentID']]['LastExecution']
            instrument_my_price = position['OpenRate']
            instrument_is_buy = position["IsBuy"]
            if instrument_name in close_orders and position['InstrumentID'] not in exit_orders:
                del close_orders[instrument_name]
            if not instrument_is_buy:
                fee_relative = (instrument_my_price*100/instrument_current_price) - 100
                fee_absolute = instrument_my_price-instrument_current_price
            else:
                fee_relative = (instrument_current_price*100/instrument_my_price) - 100
                fee_absolute = instrument_current_price-instrument_my_price
            if fee_relative < -1.5 and position['InstrumentID'] not in exit_orders:
                await etoro.close_order(self.session, position_id)
                close_orders[instrument_name] = instrument_current_price
                etoro.helpers.set_cache('close_orders', close_orders)
            if fee_relative > 1.5 and instrument_name not in fine_orders:
                fine_orders[instrument_name] = fee_relative
            if instrument_name in fine_orders:
                if fee_relative > fine_orders[instrument_name]:
                    fine_orders[instrument_name] = fee_relative
                if (fine_orders[instrument_name] - fee_relative) >= 1.5:
                    await etoro.close_order(self.session, position_id)
                    close_orders[instrument_name] = instrument_current_price
                    etoro.helpers.set_cache('close_orders', close_orders)
                    del fine_orders[instrument_name]





    def buy(self, count):
        print('buy', count, self.bid)

    def sell(self, count):
        print('sell', count, self.ask)