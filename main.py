import asyncio
import aiohttp
import logging

import helpers
import etoro

logging.basicConfig(level=logging.INFO)

if '__main__' == __name__:
    loop = asyncio.get_event_loop()
    agregate_data = {'Buy': {}, 'Sell': {}}
    with aiohttp.ClientSession(loop=loop) as session:
        content = loop.run_until_complete(etoro.login(session))
        helpers.set_cache('login_info', content)
        portfolio = content["AggregatedResult"]["ApiResponses"]["PrivatePortfolio"]["Content"]["ClientPortfolio"]
        logging.info('Balance: {}'.format(portfolio["Credit"]))
        instruments = helpers.get_cache('instruments')
        if not instruments:
            instruments = loop.run_until_complete(etoro.instruments(session))
            helpers.set_cache('instruments', instruments)
        instruments = {instrument['InstrumentID']: instrument for instrument in instruments['InstrumentDisplayDatas']}
        instruments_rate = helpers.get_cache('instruments_rate')
        if not instruments_rate:
            instruments = loop.run_until_complete(etoro.instruments_rate(session))
            helpers.set_cache('instruments_rate', instruments)
        instruments_rate = {instrument['InstrumentID']: instrument for instrument in instruments_rate['Rates']}
        for position in portfolio["Positions"]:
            logging.info('My order: {}. My price: {}. Current Ask: {}. Direct: {}'.format(
                instruments[position["InstrumentID"]]['SymbolFull'], position["OpenRate"],
                instruments_rate[position["InstrumentID"]]["Ask"], 'Byu' if position["IsBuy"] else 'Sell'))
        list_traders = helpers.get_cache('list_traders')
        if not list_traders:
            list_traders = loop.run_until_complete(etoro.trader_list(session, gainmin=0, profitablemonthspctmin=35))
            helpers.set_cache('list_traders', list_traders)
        logging.info('Traders was found: {}'.format(list_traders['TotalRows']))
        traders = helpers.get_cache('traders')
        if not traders:
            traders = []
            for trader in list_traders['Items']:
                trader_info = loop.run_until_complete(etoro.user_info(session, trader['UserName']))
                traders.append(trader_info)
            helpers.set_cache('traders', traders)
        for trader in traders:
            portfolio = helpers.get_cache('trader_portfolios/{}'.format(trader['realCID']))
            if not portfolio:
                portfolio = loop.run_until_complete(etoro.user_portfolio(session, trader['realCID']))
                helpers.set_cache('trader_portfolios/{}'.format(trader['realCID']), portfolio)
            for position in portfolio['AggregatedPositions']:
                if position['Direction'] in agregate_data:
                    if position['InstrumentID'] not in agregate_data[position['Direction']]:
                        agregate_data[position['Direction']][position['InstrumentID']] = 0
                    agregate_data[position['Direction']][position['InstrumentID']] += 1
    buy_max = {'count': 0, 'ids': []}
    for instr_id in agregate_data['Buy']:
        if buy_max['count'] < agregate_data['Buy'][instr_id]:
            buy_max['count'] = agregate_data['Buy'][instr_id]
            buy_max['ids'] = [instr_id]
        if buy_max['count'] == agregate_data['Buy'][instr_id]:
            if instr_id not in buy_max['ids']:
                buy_max['ids'].append(instr_id)

    sell_max = {'count': 0, 'ids': []}
    for instr_id in agregate_data['Sell']:
        if sell_max['count'] < agregate_data['Sell'][instr_id]:
            sell_max['count'] = agregate_data['Sell'][instr_id]
            sell_max['ids'] = [instr_id]
        if buy_max['count'] == agregate_data['Sell'][instr_id]:
            if instr_id not in sell_max['ids']:
                sell_max['ids'].append(instr_id)

    for id in buy_max['ids']:
        if id in instruments:
            print('Buy:', instruments[id]['SymbolFull'], sell_max['count'])

    for id in sell_max['ids']:
        if id in instruments:
            print('Sell:', instruments[id]['SymbolFull'], sell_max['count'])
('\n'
 'При сделке, необходимо запоминать на основании каких трейдеров было решено войти на рынок.\n'
 'Отслеживать сделки этих трейдов по купленным\проданным инструментам.\n'
 'В случае сброса этих инструментов следовать трейдерам.\n')