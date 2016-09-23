import aiohttp
import asyncio
import json
from my_logging import logger as logging
from datetime import datetime
import settings
import helpers

LAST_REQUEST = None
REQUEST_COUNT = 0

async def trader_list(session, activeweeksmin=30, blocked=False, bonusonly=False, copyinvestmentpctmax=0,
                      gainmax=80, gainmin=5, highleveragepctmax=12, istestaccount=False, lastactivitymax=7,
                      optin=True, page=1, pagesize=500, period='OneYearAgo', profitablemonthspctmin=65,
                      riskscoremax=4, riskscoremin=1, sort='-gain', tradesmin=15, weeklyddmin=-10,
                      weeklyddmax=-3, dailyddmin=-7, dailyddmax=-1):
    list_trades_url = 'https://www.etoro.com/sapi/rankings/rankings/?client_request_id={client_request_id}&' \
                  'activeweeksmin={activeweeksmin}&blocked={blocked}&bonusonly={bonusonly}&copyinvestmentpctmax=' \
                  '{copyinvestmentpctmax}&gainmax={gainmax}&gainmin={gainmin}&' \
                  'highleveragepctmax={highleveragepctmax}&istestaccount={istestaccount}&lastactivitymax=' \
                  '{lastactivitymax}&optin={optin}&page={page}&pagesize={pagesize}&period={period}&' \
                  'profitablemonthspctmin={profitablemonthspctmin}&riskscoremax={riskscoremax}&' \
                  'riskscoremin={riskscoremin}&sort={sort}&tradesmin={tradesmin}&' \
                  'weeklyddmin={weeklyddmin}&weeklyddmax={weeklyddmax}&dailyddmax={dailyddmax}' \
                  '&dailyddmin={dailyddmin}'.format(client_request_id=helpers.device_id(),
                                                    activeweeksmin=activeweeksmin,
                                                    blocked='false' if not blocked else 'true', bonusonly=bonusonly,
                                                    copyinvestmentpctmax=copyinvestmentpctmax, gainmax=gainmax,
                                                    gainmin=gainmin, highleveragepctmax=highleveragepctmax,
                                                    istestaccount=istestaccount, lastactivitymax=lastactivitymax,
                                                    optin='false' if not optin else 'true', page=page,
                                                    pagesize=pagesize, period=period,
                                                    profitablemonthspctmin=profitablemonthspctmin,
                                                    riskscoremax=riskscoremax, riskscoremin=riskscoremin,
                                                    sort=sort, tradesmin=tradesmin,
                                                    weeklyddmax=weeklyddmax, weeklyddmin=weeklyddmin,
                                                    dailyddmin=dailyddmin, dailyddmax=dailyddmax)
    return await get(session, list_trades_url)

async def get_history(instrument_id=1, count=1000):
    url = 'https://candle.etoro.com/candles/desc.json/ThirtyMinutes/{}/{}'.format(count, instrument_id)
    #url = 'https://candle.etoro.com/candles/desc.json/FiveMinutes/1000/1'
    async with aiohttp.ClientSession() as session:
        data = await get(session, url)
    return data

async def instruments_rate(session):
    url = 'https://www.etoro.com/sapi/trade-real/instruments/?client_request_id={}' \
          '&InstrumentDataFilters=Activity,Rates,TradingData'.format(helpers.device_id())
    return await get(session, url)

async def instruments(session):
    url = 'https://api.etorostatic.com/sapi/instrumentsmetadata/V1.1/instruments'
    return await get(session, url)

async def user_info(session, login):
    url = 'https://www.etoro.com/api/logininfo/v1.1/users/{}?client_request_id={}'.format(login, helpers.device_id())
    return await get(session, url)

async def user_portfolio(session, user_id):
    url = 'https://www.etoro.com/sapi/trade-real/portfolios/public?client_request_id={}&cid={}'.format(
        helpers.device_id(), user_id)
    return await get(session, url)

async def watch_list(session):
    url = 'https://www.etoro.com/api/watchlist/v1/watchlists?client_request_id={}&doNotReturnBadRequest=true'.format(
        helpers.device_id()
    )
    return await get(session, url)

async def get(session, url, json_flag=True, recursion_level=1):
    global LAST_REQUEST
    global REQUEST_COUNT
    if recursion_level > 10:
        logging.error('Recursion is too deep')
        raise Exception('Recursion is too deep')
    if LAST_REQUEST is not None:
        dif_datetime = datetime.now() - LAST_REQUEST
        if dif_datetime.seconds < 1:
            REQUEST_COUNT += 1
    if REQUEST_COUNT > 2:
        REQUEST_COUNT = 0
        logging.debug('I am sleep')
        await asyncio.sleep(1)
    LAST_REQUEST = datetime.now()
    logging.debug('Get query to {url}'.format(url=url.split('?')[0]))
    headers = helpers.get_cache('headers')
    cookies = helpers.get_cache('cookies')
    try:
        with aiohttp.Timeout(10):
            async with session.get(url, headers=headers) as response:
                data = await response.json()
    except (asyncio.TimeoutError, aiohttp.errors.ServerDisconnectedError, aiohttp.errors.ClientOSError,
            aiohttp.errors.ClientResponseError):
        logging.debug('Query Error. Level {}'.format(recursion_level))
        await asyncio.sleep(2*recursion_level)
        return get(session, url, json_flag=json_flag, recursion_level=(recursion_level +1 ))
    except json.decoder.JSONDecodeError:
        logging.debug('Json decode error. Level {}'.format(recursion_level))
        await asyncio.sleep(2*recursion_level)
        return get(session, url, json_flag=json_flag, recursion_level=(recursion_level +1 ))
    return data

async def close_order(session, position_id, price=None, demo=True):
    logging.info('Order was closed. Price: {}'.format(price))
    account_type = 'demo' if demo else 'real'
    headers = helpers.get_cache('headers')
    if price is None:
        url = 'https://www.etoro.com/sapi/trade-{account_type}/exit-orders?client_request_id={client_id}'.format(
            client_id=helpers.device_id(), account_type=account_type
        )
        payload = {
            'PendingClosePositionID': position_id
        }
        async with session.post(url, data=json.dumps(payload), headers=headers) as response:
            resp = await response.json()
    else:
        url = 'https://www.etoro.com/sapi/trade-{account_type}/positions/{position_id}?' \
          'client_request_id={client_id}&ClientViewRate={price}' \
          '&PositionID={position_id}'.format(position_id=position_id, client_id=helpers.device_id(), price=price,
                                             account_type=account_type)
        async with session.delete(url, headers=headers) as response:
            resp = await response.json()
    return resp


async def order(session, InstrumentID, ClientViewRate, IsBuy=True, IsTslEnabled=False, Leverage=1, Amount=25, demo=True):
    logging.info('Order is opened. Instrument: {}. IsBuy: {}'.format(InstrumentID, IsBuy))
    url = 'https://www.etoro.com/sapi/trade-{account_type}/positions?client_request_id={}'.format(helpers.device_id(),
                                                                                                  account_type='demo' if demo else 'real')
    stop_loss = (ClientViewRate * 1.4) if not IsBuy else (ClientViewRate * 0.6)
    take_profit = (ClientViewRate * 1.4) if IsBuy else (ClientViewRate * 0.6)
    headers = helpers.get_cache('headers')
    payload = {
        'Amount': Amount,
        'ClientViewRate': ClientViewRate,
        'InstrumentID': InstrumentID,
        'IsBuy': IsBuy,
        'IsTslEnabled': IsTslEnabled,
        'Leverage': Leverage,
        'StopLossRate': stop_loss,
        'TakeProfitRate': take_profit,
    }
    async with session.post(url, data=json.dumps(payload), headers=headers) as response:
        resp = await response.json()
    return resp


async def login(session, account_type='Demo', only_info=False):
    url = 'https://www.etoro.com/api/sts/v2/login/?client_request_id={}'.format(helpers.device_id())
    payload = settings.payload
    params = {'client_request_id': helpers.device_id(),
              'conditionIncludeDisplayableInstruments': False,
              'conditionIncludeMarkets': False,
              'conditionIncludeMetadata': False,
              }
    headers = {'content-type': 'application/json;charset=UTF-8',
               'AccountType': account_type,
               'ApplicationIdentifier': 'ReToro',
               'ApplicationVersion': 'vp3079',
               'X-CSRF-TOKEN': 'k%7cuGYP%7ci9dVOhujYx0ZsTw%5f%5f',
               'X-DEVICE-ID': helpers.device_id()
               }
    helpers.set_cache('headers', headers)
    if not only_info:
        with aiohttp.Timeout(10):
            async with session.post(url,
                                    data=json.dumps(payload),
                                    headers=headers) as response:
                assert response.status == 201
                login_content_josn = await response.read()
        login_content = json.loads(login_content_josn.decode('utf-8'))
        headers['Authorization'] = login_content['accessToken']
        helpers.set_cache('headers', headers)
        cookies_dict = helpers.cookies_parse(response.cookies)
        helpers.set_cache('cookies', cookies_dict)
    with aiohttp.Timeout(10):
        async with session.get('https://www.etoro.com/api/logininfo/v1.1/logindata' ,params=params,
                                headers=headers) as response:
            login_info = await response.json()
    return login_info
