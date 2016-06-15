import asyncio
import aiohttp
import logging

import helpers
import etoro

logging.basicConfig(level=logging.INFO)


async def my_loop(in_loop):
    aggregate_data = {'Buy': {}, 'Sell': {}}
    my_portfolio = {}
    while True:
        with aiohttp.ClientSession(loop=in_loop) as session:
            content = await etoro.login(session)
            helpers.set_cache('login_info', content)
            portfolio = content["AggregatedResult"]["ApiResponses"]["PrivatePortfolio"]["Content"]["ClientPortfolio"]
            logging.info('Balance: {}'.format(portfolio["Credit"]))
            instruments = helpers.get_cache('instruments')
            if not instruments:
                instruments = await etoro.instruments(session)
                helpers.set_cache('instruments', instruments)
            instruments = {instrument['InstrumentID']: instrument for instrument in
                           instruments['InstrumentDisplayDatas']}
            instruments_rate = helpers.get_cache('instruments_rate')
            if not instruments_rate:
                instruments_rate = await etoro.instruments_rate(session)
                helpers.set_cache('instruments_rate', instruments_rate)
            instruments_instrument = {instrument['InstrumentID']: instrument for instrument in
                                      instruments_rate['Instruments']}
            instruments_rate = {instrument['InstrumentID']: instrument for instrument in instruments_rate['Rates']}
            for position in portfolio["Positions"]:
                my_portfolio[position["InstrumentID"]] = {
                    'IsBuy': position["IsBuy"],
                    'Amount': position["Amount"],
                    'CID': position["CID"],
                    'PositionID': position["PositionID"]
                }
                logging.info('My order: {}. My price: {}. Current Ask: {}. Direct: {}'.format(
                    instruments[position["InstrumentID"]]['SymbolFull'], position["OpenRate"],
                    instruments_rate[position["InstrumentID"]]["Ask"], 'Byu' if position["IsBuy"] else 'Sell'))
            list_traders = helpers.get_cache('list_traders')
            if not list_traders:
                list_traders = await etoro.trader_list(session, gainmin=0, profitablemonthspctmin=35)
                helpers.set_cache('list_traders', list_traders)
            logging.info('Traders was found: {}'.format(list_traders['TotalRows']))
            traders = helpers.get_cache('traders')
            if not traders:
                traders = []
                for trader in list_traders['Items']:
                    trader_info = await etoro.user_info(session, trader['UserName'])
                    traders.append(trader_info)
                helpers.set_cache('traders', traders)
            for trader in traders:
                portfolio = helpers.get_cache('trader_portfolios/{}'.format(trader['realCID']))
                if not portfolio:
                    portfolio = await etoro.user_portfolio(session, trader['realCID'])
                    helpers.set_cache('trader_portfolios/{}'.format(trader['realCID']), portfolio)
                for position in portfolio['AggregatedPositions']:
                    if position['Direction'] in aggregate_data:
                        if position['InstrumentID'] not in aggregate_data[position['Direction']]:
                            aggregate_data[position['Direction']][position['InstrumentID']] = 0
                        aggregate_data[position['Direction']][position['InstrumentID']] += 1
            buy_max = {'count': 0, 'ids': []}
            for instr_id in aggregate_data['Buy']:
                if buy_max['count'] < aggregate_data['Buy'][instr_id]:
                    buy_max['count'] = aggregate_data['Buy'][instr_id]
                    buy_max['ids'] = [instr_id]
                if buy_max['count'] == aggregate_data['Buy'][instr_id]:
                    if instr_id not in buy_max['ids']:
                        buy_max['ids'].append(instr_id)

            sell_max = {'count': 0, 'ids': []}
            for instr_id in aggregate_data['Sell']:
                if sell_max['count'] < aggregate_data['Sell'][instr_id]:
                    sell_max['count'] = aggregate_data['Sell'][instr_id]
                    sell_max['ids'] = [instr_id]
                if buy_max['count'] == aggregate_data['Sell'][instr_id]:
                    if instr_id not in sell_max['ids']:
                        sell_max['ids'].append(instr_id)

            for instr_id in buy_max['ids']:
                if instr_id in instruments:
                    if instr_id in my_portfolio and my_portfolio[instr_id]['IsBuy']:
                        logging.info('You have {} in your portfolio'.format(instruments[instr_id]['SymbolFull']))
                    elif instr_id in my_portfolio and not my_portfolio[instr_id]['IsBuy']:
                        logging.info('You have backward {} in portfolio'.format(instruments[instr_id]['SymbolFull']))
                        await etoro.close_order(session, my_portfolio[instr_id]['PositionID'],
                                                instruments_rate[instr_id]['Ask'])
                    else:
                        logging.info('You didn\'t have {} in portfolio'.format(instruments[instr_id]['SymbolFull']))
                        await etoro.order(session, instr_id, instruments_rate[instr_id]['Ask'],
                                          Amount=instruments_instrument[instr_id]['MinPositionAmount'],
                                          Leverage=instruments_instrument[instr_id]['Leverages'][0])

            for instr_id in sell_max['ids']:
                if instr_id in instruments:
                    if instr_id in my_portfolio and not my_portfolio[instr_id]['IsBuy']:
                        logging.info('You have {} in your portfolio'.format(instruments[instr_id]['SymbolFull']))
                    elif instr_id in my_portfolio and my_portfolio[instr_id]['IsBuy']:
                        logging.info('You have backward {} in portfolio'.format(instruments[instr_id]['SymbolFull']))
                        await etoro.close_order(session, my_portfolio[instr_id]['PositionID'],
                                                instruments_rate[instr_id]['Bid'])
                    else:
                        logging.info('You didn\'t have {} in portfolio'.format(instruments[instr_id]['SymbolFull']))
                        await etoro.order(session, instr_id, instruments_rate[instr_id]['Bid'], IsBuy=False,
                                          Amount=instruments_instrument[instr_id]['MinPositionAmount'],
                                          Leverage=instruments_instrument[instr_id]['Leverages'][0])

            for instrument_id in my_portfolio:
                if instrument_id not in buy_max['ids'] and instrument_id not in sell_max['ids']:
                    logging.info('Deleting of instrument {}'.format(instruments[instrument_id]['SymbolFull']))
                    price_view = instruments_rate[instrument_id]['Ask'] if my_portfolio[instrument_id]['IsBuy'] else \
                        instruments_rate[instrument_id]['Bid']
                    await etoro.close_order(session, my_portfolio[instrument_id]['PositionID'], price_view)
        logging.info('Sleeping {} sec'.format(1300))
        await asyncio.sleep(1300)

if '__main__' == __name__:
    try:
        loop = asyncio.get_event_loop()
        coroutine = my_loop(loop)
        loop.run_until_complete(coroutine)
    except KeyboardInterrupt:
        logging.info('Exit')
