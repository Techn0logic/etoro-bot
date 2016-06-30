import asyncio
import aiohttp
import logging

import helpers
import etoro

logging.basicConfig(level=logging.INFO)


async def my_loop(in_loop, aviable_limit=50):

    async def trading(store_max, is_buy=True, demo=True):
        if is_buy:
            rate_type = 'Ask'
        else:
            rate_type = 'Bid'
        for instr_id in store_max['ids']:
            if instr_id in instruments:
                if instr_id in my_portfolio and ((is_buy and my_portfolio[instr_id]['IsBuy']) or
                                                     (not is_buy and not my_portfolio[instr_id]['IsBuy'])):
                    logging.info('You have {} in your portfolio'.format(instruments[instr_id]['SymbolFull']))
                elif instr_id in my_portfolio and ((is_buy and not my_portfolio[instr_id]['IsBuy']) or
                                                       (not is_buy and my_portfolio[instr_id]['IsBuy'])):
                    logging.info('You have backward {} in portfolio'.format(instruments[instr_id]['SymbolFull']))
                    await etoro.close_order(session, my_portfolio[instr_id]['PositionID'],
                                            instruments_rate[instr_id][rate_type], demo=demo)
                else:
                    logging.info('You didn\'t have {} in portfolio'.format(instruments[instr_id]['SymbolFull']))
                    await etoro.order(session, instr_id, instruments_rate[instr_id][rate_type],
                                      Amount=instruments_instrument[instr_id]['MinPositionAmount'],
                                      Leverage=instruments_instrument[instr_id]['Leverages'][0], IsBuy=is_buy,
                                      demo=demo)

    time_out = 5
    not_login = False
    while True:
        aggregate_data = {'Buy': {}, 'Sell': {}}
        my_portfolio = {}
        with aiohttp.ClientSession(loop=in_loop) as session:
            content = await etoro.login(session, only_info=not_login)
            if "AggregatedResult" not in content:
                logging.info('Login fail')
                not_login = False
                continue
            not_login = True
            helpers.set_cache('login_info', content)
            user_portfolio = content["AggregatedResult"]["ApiResponses"]["PrivatePortfolio"]["Content"]["ClientPortfolio"]
            logging.info('Balance: {}'.format(user_portfolio["Credit"]))
            instruments = helpers.get_cache('instruments', (time_out-1))
            if not instruments:
                instruments = await etoro.instruments(session)
                helpers.set_cache('instruments', instruments)
            instruments = {instrument['InstrumentID']: instrument for instrument in
                           instruments['InstrumentDisplayDatas']}
            instruments_rate = helpers.get_cache('instruments_rate', (time_out-1))
            if not instruments_rate:
                instruments_rate = await etoro.instruments_rate(session)
                helpers.set_cache('instruments_rate', instruments_rate)
            instruments_instrument = {instrument['InstrumentID']: instrument for instrument in
                                      instruments_rate['Instruments']}
            instruments_rate = {instrument['InstrumentID']: instrument for instrument in instruments_rate['Rates']}
            for position in user_portfolio["Positions"]:
                my_portfolio[position["InstrumentID"]] = {
                    'IsBuy': position["IsBuy"],
                    'Amount': position["Amount"],
                    'CID': position["CID"],
                    'PositionID': position["PositionID"]
                }
                logging.info('My order: {}. My price: {}. Current Ask: {}. Direct: {}'.format(
                    instruments[position["InstrumentID"]]['SymbolFull'], position["OpenRate"],
                    instruments_rate[position["InstrumentID"]]["Ask"], 'Byu' if position["IsBuy"] else 'Sell'))
            list_traders = helpers.get_cache('list_traders', (time_out-1))
            if not list_traders:
                list_traders = await etoro.trader_list(session, gainmin=0, profitablemonthspctmin=35)
                helpers.set_cache('list_traders', list_traders)
            logging.info('Traders was found: {}'.format(list_traders['TotalRows']))
            traders = helpers.get_cache('traders', (time_out-1))
            if not traders:
                traders = []
                for trader in list_traders['Items']:
                    trader_info = await etoro.user_info(session, trader['UserName'])
                    traders.append(trader_info)
                helpers.set_cache('traders', traders)

            for trader in traders:
                portfolio = helpers.get_cache('trader_portfolios/{}'.format(trader['realCID']), (time_out-1))
                if not portfolio:
                    portfolio = await etoro.user_portfolio(session, trader['realCID'])
                    helpers.set_cache('trader_portfolios/{}'.format(trader['realCID']), portfolio)
                for position in portfolio['AggregatedPositions']:
                    if position['Direction'] in aggregate_data \
                            and instruments_instrument[position['InstrumentID']]['MinPositionAmount'] <= aviable_limit\
                            and instruments_instrument[position['InstrumentID']]['MinPositionAmount'] <= user_portfolio["Credit"]:
                        if position['InstrumentID'] not in aggregate_data[position['Direction']]:
                            aggregate_data[position['Direction']][position['InstrumentID']] = 0
                        aggregate_data[position['Direction']][position['InstrumentID']] += 1
                        break

            buy_max = helpers.get_list_instruments(aggregate_data)
            sell_max = helpers.get_list_instruments(aggregate_data, type='Sell')

            logging.info('buy info {}, sell info {}'.format(buy_max, sell_max))
            if buy_max['count'] > 2:
                await trading(buy_max, is_buy=True, demo=True)

            if sell_max['count'] > 2:
                await trading(sell_max, is_buy=False, demo=True)

            for instrument_id in my_portfolio:
                if instrument_id not in buy_max['ids'] and instrument_id not in sell_max['ids'] or \
                        (instrument_id in buy_max['ids'] and buy_max['count'] <= 1) or \
                        (instrument_id in sell_max['ids'] and sell_max['count'] <= 1):
                    logging.info('Deleting of instrument {}'.format(instruments[instrument_id]['SymbolFull']))
                    price_view = instruments_rate[instrument_id]['Ask'] if my_portfolio[instrument_id]['IsBuy'] else \
                        instruments_rate[instrument_id]['Bid']
                    await etoro.close_order(session, my_portfolio[instrument_id]['PositionID'], price_view)
        logging.info('Sleeping {} min'.format(time_out))
        await asyncio.sleep(time_out*60)

if '__main__' == __name__:
    try:
        loop = asyncio.get_event_loop()
        coroutine = my_loop(loop)
        loop.run_until_complete(coroutine)
    except KeyboardInterrupt:
        logging.info('Exit')
