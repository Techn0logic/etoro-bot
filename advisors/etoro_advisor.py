import aiohttp
import asyncio

import random
import json

import helpers
import etoro
from my_logging import logger as logging
from messengers import Messenger

class EtoroAdvisor(object):

    def __init__(self, in_loop):
        self.aggregate_data = {}
        self.trade = {}
        self.time_out = 5
        self.cache_time_value = 20
        self.session = aiohttp.ClientSession(loop=in_loop)
        self.aviable_limit = 50
        self.user_portfolio = {}
        self.instruments = {}
        self.instruments_rate = {}
        self.instruments_instrument = {}
        self.my_portfolio = {}
        self.time_out *= 60
        self.messenger = Messenger()

    @property
    def cache_time(self):
        return random.randint(self.cache_time_value-7, self.cache_time_value)

    def do_somesing(self):
        while True:
            pass

    async def traders_info(self):
        list_traders = helpers.get_cache('list_traders', self.cache_time)
        if not list_traders:
            try:
                list_traders = await etoro.trader_list(self.session, gainmin=0, profitablemonthspctmin=35)
            except (asyncio.TimeoutError, aiohttp.errors.ServerDisconnectedError, aiohttp.errors.ClientOSError, aiohttp.errors.ClientResponseError):
                logging.error('Query Error')
                return False
            except json.decoder.JSONDecodeError:
                logging.error('Json error')
                return False
            helpers.set_cache('list_traders', list_traders)
        logging.info('Traders was found: {}'.format(list_traders['TotalRows']))
        traders = helpers.get_cache('traders', self.cache_time * 10)
        if not traders:
            traders = []
            for trader in list_traders['Items']:
                try:
                    trader_info = helpers.get_cache('trader_portfolios/trader_info_{}'.format(trader['UserName']),
                                                     self.cache_time)
                    if not trader_info:
                        trader_info = await etoro.user_info(self.session, trader['UserName'])
                        helpers.set_cache('trader_portfolios/trader_info_{}'.format(trader['UserName']), trader_info)
                except (asyncio.TimeoutError, aiohttp.errors.ServerDisconnectedError, aiohttp.errors.ClientOSError, aiohttp.errors.ClientResponseError):
                    logging.error('Query Error')
                    return False
                except json.decoder.JSONDecodeError:
                    logging.error('Json decode error')
                    return False
                traders.append(trader_info)
            helpers.set_cache('traders', traders)

        for trader in traders:
            portfolio = helpers.get_cache('trader_portfolios/{}'.format(trader['realCID']), (random.randint(5, self.cache_time)))
            if not portfolio:
                try:
                    portfolio = await etoro.user_portfolio(self.session, trader['realCID'])
                except (asyncio.TimeoutError, aiohttp.errors.ServerDisconnectedError, aiohttp.errors.ClientOSError, aiohttp.errors.ClientResponseError):
                    logging.error('Query Error')
                    break
                except json.decoder.JSONDecodeError:
                    logging.error('Json decode error')
                    return False
                if portfolio:
                    helpers.set_cache('trader_portfolios/{}'.format(trader['realCID']), portfolio)
            if portfolio:
                for position in portfolio['AggregatedPositions']:
                    if position['Direction'] in self.aggregate_data \
                            and self.instruments_instrument[position['InstrumentID']]['MinPositionAmount'] <= self.aviable_limit\
                            and self.instruments_instrument[position['InstrumentID']]['MinPositionAmount'] <= self.user_portfolio["Credit"]:
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
            logging.info('My order: {}. My price: {}. Current Ask: {}. Direct: {}'.format(
                self.instruments[position["InstrumentID"]]['SymbolFull'], position["OpenRate"],
                self.instruments_rate[position["InstrumentID"]]["Ask"], 'Byu' if position["IsBuy"] else 'Sell'))

    async def check_instruments(self):
        self.instruments = helpers.get_cache('instruments', self.cache_time)
        if not self.instruments:
            try:
                self.instruments = await etoro.instruments(self.session)
            except (asyncio.TimeoutError, aiohttp.errors.ServerDisconnectedError, aiohttp.errors.ClientOSError, aiohttp.errors.ClientResponseError):
                logging.error('Query Error')
                return False
            except json.decoder.JSONDecodeError:
                logging.error('Json decode error')
                return False
            helpers.set_cache('instruments', self.instruments)
        self.instruments = {instrument['InstrumentID']: instrument for instrument in
                       self.instruments['InstrumentDisplayDatas']}
        self.instruments_rate = helpers.get_cache('instruments_rate', self.cache_time)
        if not self.instruments_rate:
            try:
                self.instruments_rate = await etoro.instruments_rate(self.session)
            except (asyncio.TimeoutError, aiohttp.errors.ServerDisconnectedError, aiohttp.errors.ClientOSError, aiohttp.errors.ClientResponseError):
                logging.error('Query Error')
                return False
            except json.decoder.JSONDecodeError:
                logging.error('Json decode error')
                return False
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
                logging.info('Deleting of instrument {}'.format(self.instruments[instrument_id]['SymbolFull']))
                price_view = self.instruments_rate[instrument_id]['Ask'] if self.my_portfolio[instrument_id]['IsBuy'] else \
                    self.instruments_rate[instrument_id]['Bid']
                try:
                    await etoro.close_order(self.session, self.my_portfolio[instrument_id]['PositionID'], price_view)
                except (asyncio.TimeoutError, aiohttp.errors.ServerDisconnectedError, aiohttp.errors.ClientOSError, aiohttp.errors.ClientResponseError):
                    logging.error('Query Error')
                    break
                except json.decoder.JSONDecodeError:
                    logging.error('Json decode error')
                    break

    async def login(self):
        if self.session.closed:
            self.session.close()
        content = await etoro.login(self.session)
        return content

    async def etoro_loop(self):

        async def trading(store_max, is_buy=True, demo=True):
            if is_buy:
                rate_type = 'Ask'
            else:
                rate_type = 'Bid'
            for instr_id in store_max['ids']:
                if instr_id in self.instruments:
                    if instr_id in self.my_portfolio and ((is_buy and self.my_portfolio[instr_id]['IsBuy']) or
                                                         (not is_buy and not self.my_portfolio[instr_id]['IsBuy'])):
                        logging.info('You have {} in your portfolio'.format(self.instruments[instr_id]['SymbolFull']))
                    elif instr_id in self.my_portfolio and ((is_buy and not self.my_portfolio[instr_id]['IsBuy']) or
                                                           (not is_buy and self.my_portfolio[instr_id]['IsBuy'])):
                        logging.info('You have backward {} in portfolio'.format(self.instruments[instr_id]['SymbolFull']))
                        try:
                            if instr_id in self.instruments_rate:
                                await etoro.close_order(self.session, self.my_portfolio[instr_id]['PositionID'],
                                                self.instruments_rate[instr_id][rate_type], demo=demo)
                        except (asyncio.TimeoutError, aiohttp.errors.ServerDisconnectedError, aiohttp.errors.ClientOSError, aiohttp.errors.ClientResponseError):
                            logging.error('Error close order')
                            return False
                        except json.decoder.JSONDecodeError:
                            logging.error('Json decode error')
                            return False
                    else:
                        logging.info('You didn\'t have {} in portfolio'.format(self.instruments[instr_id]['SymbolFull']))
                        try:
                            if instr_id in self.instruments_rate:
                                await etoro.order(self.session, instr_id, self.instruments_rate[instr_id][rate_type],
                                          Amount=self.instruments_instrument[instr_id]['MinPositionAmount'],
                                          Leverage=self.instruments_instrument[instr_id]['Leverages'][0], IsBuy=is_buy,
                                          demo=demo)
                        except (asyncio.TimeoutError, aiohttp.errors.ServerDisconnectedError, aiohttp.errors.ClientOSError, aiohttp.errors.ClientResponseError):
                            logging.error('Error order')
                            return False
                        except json.decoder.JSONDecodeError:
                            logging.error('Json decode error')
                            return False


        self.aggregate_data = {'Buy': {}, 'Sell': {}}
        try:
            content = await etoro.login(self.session, only_info=True)
        except (asyncio.TimeoutError, aiohttp.errors.ServerDisconnectedError, aiohttp.errors.ClientOSError, aiohttp.errors.ClientResponseError):
            logging.error('Login fail')
            await asyncio.sleep(self.time_out)
        except json.decoder.JSONDecodeError:
            logging.error('Json decode error')
            await asyncio.sleep(self.time_out)

        helpers.set_cache('login_info', content)

        while "AggregatedResult" not in content:
            try:
                logging.info('Login fail')
                content = await self.login()
            except (asyncio.TimeoutError, aiohttp.errors.ServerDisconnectedError, aiohttp.errors.ClientOSError, aiohttp.errors.ClientResponseError):
                logging.error('Login fail')
                await asyncio.sleep(self.time_out)
            except json.decoder.JSONDecodeError:
                logging.error('Json decode error')
                await asyncio.sleep(self.time_out)

        self.user_portfolio = content["AggregatedResult"]["ApiResponses"]["PrivatePortfolio"]["Content"]["ClientPortfolio"]
        logging.info('Balance: {}'.format(self.user_portfolio["Credit"]))

        await self.check_instruments()
        trader_info_status = await self.traders_info()
        await self.messenger.send('dd')
        if trader_info_status:
            buy_max = helpers.get_list_instruments(self.aggregate_data)
            sell_max = helpers.get_list_instruments(self.aggregate_data, type='Sell')
            if not buy_max and not sell_max:
                return False

            logging.info('buy info {}, sell info {}'.format(buy_max, sell_max))
            if buy_max['count'] > 2:
                # await trading(buy_max, is_buy=True, demo=True)
                pass

            if sell_max['count'] > 2:
                # await trading(sell_max, is_buy=False, demo=True)
                pass

            # await self.check_my_order(buy_max, sell_max)