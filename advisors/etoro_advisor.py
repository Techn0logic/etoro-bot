import aiohttp
import asyncio

import random
import json
import operator
import datetime

import helpers
import etoro
from my_logging import logger as logging
from interfaces.advisor import ABCAdvisor
import settings


class EtoroAdvisor(ABCAdvisor):

    def __init__(self, in_loop, **kwargs):
        super().__init__(in_loop, **kwargs)
        self.aggregate_data = {}
        self.trade = {}
        self.time_out = 5
        self.cache_time_value = 60
        self.aviable_limit = 50
        self.user_portfolio = {}
        self.instruments = {}
        self.instruments_rate = {}
        self.instruments_instrument = {}
        self.my_portfolio = {}
        self.time_out *= 60
        # self.messenger = self._messageManager(in_loop)
        self.account_type = settings.account_type
        self.last_run = None
        self.last_send_message = None
        self._message = None

    @property
    def cache_time(self):
        return random.randint(self.cache_time_value-30, self.cache_time_value)

    def do_somesing(self):
        while True:
            pass

    async def traders_info(self, entire_balance=True):
        list_traders = helpers.get_cache('list_traders', self.cache_time)
        if not list_traders:
            list_traders = await etoro.trader_list(self.session, gainmin=0, profitablemonthspctmin=35)
            helpers.set_cache('list_traders', list_traders)
        logging.debug('Traders was found: {}'.format(list_traders['TotalRows']))
        traders = helpers.get_cache('traders', self.cache_time * 10)
        if not traders:
            traders = []
            for trader in list_traders['Items']:
                trader_info = helpers.get_cache('trader_portfolios/trader_info_{}'.format(trader['UserName']),
                                                 self.cache_time)
                if not trader_info:
                    trader_info = await etoro.user_info(self.session, trader['UserName'])
                    helpers.set_cache('trader_portfolios/trader_info_{}'.format(trader['UserName']), trader_info)
                traders.append(trader_info)
            helpers.set_cache('traders', traders)

        for trader in traders:
            portfolio = helpers.get_cache('trader_portfolios/{}'.format(trader['realCID']), (random.randint(5, self.cache_time)))
            if not portfolio:
                portfolio = await etoro.user_portfolio(self.session, trader['realCID'])
                if portfolio:
                    helpers.set_cache('trader_portfolios/{}'.format(trader['realCID']), portfolio)
            if portfolio:
                balance = 9999999 if entire_balance else self.user_portfolio["Credit"]
                if 'AggregatedPositions' in portfolio:
                    for position in portfolio['AggregatedPositions']:
                        if position['Direction'] in self.aggregate_data \
                                and self.instruments_instrument[position['InstrumentID']]['MinPositionAmount'] <= self.aviable_limit\
                                and self.instruments_instrument[position['InstrumentID']]['MinPositionAmount'] <= balance:
                            if position['InstrumentID'] not in self.aggregate_data[position['Direction']]:
                                self.aggregate_data[position['Direction']][position['InstrumentID']] = 0
                            self.aggregate_data[position['Direction']][position['InstrumentID']] += 1
                            break
        return True

    def full_my_porfolio(self):
        for position in self.user_portfolio["Positions"]:
            self.my_portfolio[position["InstrumentID"]] = {
                'IsBuy': position["IsBuy"],
                'Amount': position["Amount"],
                'CID': position["CID"],
                'PositionID': position["PositionID"]
            }
            logging.debug('My order: {}. My price: {}. Current Ask: {}. Direct: {}'.format(
                self.instruments[position["InstrumentID"]]['SymbolFull'], position["OpenRate"],
                self.instruments_rate[position["InstrumentID"]]["Ask"], 'Byu' if position["IsBuy"] else 'Sell'))

    async def check_instruments(self):
        self.instruments = helpers.get_cache('instruments', self.cache_time)
        if not self.instruments:
            self.instruments = await etoro.instruments(self.session)
            helpers.set_cache('instruments', self.instruments)
        self.instruments = {instrument['InstrumentID']: instrument for instrument in
                       self.instruments['InstrumentDisplayDatas']}
        self.instruments_rate = helpers.get_cache('instruments_rate', self.cache_time)
        if not self.instruments_rate:
            self.instruments_rate = await etoro.instruments_rate(self.session)
            helpers.set_cache('instruments_rate', self.instruments_rate)
        self.instruments_instrument = {instrument['InstrumentID']: instrument for instrument in
                                  self.instruments_rate['Instruments']}
        self.instruments_rate = {instrument['InstrumentID']: instrument for instrument in self.instruments_rate['Rates']}
        self.full_my_porfolio()


    async def check_my_order(self, buy_max, sell_max):
        for instrument_id in self.my_portfolio:
            if instrument_id not in buy_max['ids'] and instrument_id not in sell_max['ids'] or \
                    (instrument_id in buy_max['ids'] and buy_max['count'] <= 1) or \
                    (instrument_id in sell_max['ids'] and sell_max['count'] <= 1):
                logging.debug('Deleting of instrument {}'.format(self.instruments[instrument_id]['SymbolFull']))
                price_view = self.instruments_rate[instrument_id]['Ask'] if self.my_portfolio[instrument_id]['IsBuy'] else \
                    self.instruments_rate[instrument_id]['Bid']

                await etoro.close_order(self.session, self.my_portfolio[instrument_id]['PositionID'], price_view)


    async def login(self):
        if self.session.closed:
            self.session.close()
        content = await etoro.login(self.session, account_type=self.account_type)
        return content

    async def loop(self):
        if self.last_run is not None:
            dif_time = datetime.datetime.now() - self.last_run
            if dif_time.seconds > 0 and dif_time.seconds < 300:
                return False
        async def trading(store_max, is_buy=True, demo=True):
            if is_buy:
                rate_type = 'Ask'
            else:
                rate_type = 'Bid'
            for instr_id in store_max['ids']:
                if instr_id in self.instruments:
                    if instr_id in self.my_portfolio and ((is_buy and self.my_portfolio[instr_id]['IsBuy']) or
                                                         (not is_buy and not self.my_portfolio[instr_id]['IsBuy'])):
                        logging.debug('You have {} in your portfolio'.format(self.instruments[instr_id]['SymbolFull']))
                    elif instr_id in self.my_portfolio and ((is_buy and not self.my_portfolio[instr_id]['IsBuy']) or
                                                           (not is_buy and self.my_portfolio[instr_id]['IsBuy'])):
                        logging.debug('You have backward {} in portfolio'.format(self.instruments[instr_id]['SymbolFull']))

                        if instr_id in self.instruments_rate:
                            await etoro.close_order(self.session, self.my_portfolio[instr_id]['PositionID'],
                                            self.instruments_rate[instr_id][rate_type], demo=demo)
                    else:
                        logging.debug('You didn\'t have {} in portfolio'.format(self.instruments[instr_id]['SymbolFull']))

                        if instr_id in self.instruments_rate:
                            await etoro.order(self.session, instr_id, self.instruments_rate[instr_id][rate_type],
                                      Amount=self.instruments_instrument[instr_id]['MinPositionAmount'],
                                      Leverage=self.instruments_instrument[instr_id]['Leverages'][0], IsBuy=is_buy,
                                      demo=demo)

        self.aggregate_data = {'Buy': {}, 'Sell': {}}
        content = await etoro.login(self.session, only_info=True)

        helpers.set_cache('login_info', content)

        while "AggregatedResult" not in content:
            logging.debug('Login fail')
            content = await self.login()


        self.user_portfolio = content["AggregatedResult"]["ApiResponses"]["PrivatePortfolio"]["Content"][
            "ClientPortfolio"]
        logging.debug('Balance: {}'.format(self.user_portfolio["Credit"]))

        await self.check_instruments()
        trader_info_status = await self.traders_info()
        buy_list = {self.instruments[inst_id]['SymbolFull']:self.aggregate_data['Buy'][inst_id]
                    for inst_id in self.aggregate_data['Buy']}
        buy_list = sorted(buy_list.items(), key=operator.itemgetter(1), reverse=True)
        sell_list = {self.instruments[inst_id]['SymbolFull']:self.aggregate_data['Sell'][inst_id]
                    for inst_id in self.aggregate_data['Sell']}
        sell_list = sorted(sell_list.items(), key=operator.itemgetter(1), reverse=True)

        self._message = 'Баланс: {}\r\n\r\n'.format(self.user_portfolio["Credit"])
        self._message += 'Мое портфолио: \r\n'
        for position in self.user_portfolio["Positions"]:
            self._message += 'My order: {}. My price: {}. Current Ask: {}. Direct: {}\r\n'.format(
                self.instruments[position["InstrumentID"]]['SymbolFull'], position["OpenRate"],
                self.instruments_rate[position["InstrumentID"]]["Ask"], 'Byu' if position["IsBuy"] else 'Sell')
        self._message += '\r\nПокупка: \r\n'
        for tuple_item in buy_list:
            self._message += '{}: {}\r\n'.format(tuple_item[0], tuple_item[1])
        self._message += '\r\nПродажа: \r\n'
        for tuple_item in sell_list:
            self._message += '{}: {}\r\n'.format(tuple_item[0], tuple_item[1])
        close_orders = helpers.set_cache('close_orders', 0)
        if close_orders:
            self._message += '\r\nОрдера, закрытые роботом: \r\n'
            for close_order_key in close_orders:
                self._message += '{}: {}'.format(close_order_key, close_orders[close_order_key])
        if trader_info_status:
            buy_max = helpers.get_list_instruments(self.aggregate_data)
            sell_max = helpers.get_list_instruments(self.aggregate_data, type='Sell')
            if not buy_max and not sell_max:
                return False

            logging.debug('buy info {}, sell info {}'.format(buy_max, sell_max))
            if buy_max['count'] > 2:
                # await trading(buy_max, is_buy=True, demo=True)
                pass

            if sell_max['count'] > 2:
                # await trading(sell_max, is_buy=False, demo=True)
                pass

            # await self.check_my_order(buy_max, sell_max)

        datetime_obj = datetime.datetime.now()
        current_time = datetime_obj.today()
        if self.last_run is not None:
            if str(current_time).find(settings.strtime_send_message) != 0:
                return None
            if self.last_send_message is not None and current_time.hour == self.last_send_message.hour and \
                            current_time.day == self.last_send_message.day:
                return None
        self.message = self._message
        self.last_run = datetime.datetime.today()
