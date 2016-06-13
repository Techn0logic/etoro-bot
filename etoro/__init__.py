import aiohttp
import json
import logging

import settings
import helpers

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


async def instruments_rate(session):
    url = 'https://www.etoro.com/sapi/trade-real/instruments/?client_request_id={}' \
          '&InstrumentDataFilters=Activity,Rates'.format(helpers.device_id())
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

async def get(session, url, json=True):
    logging.info('Get query to {url}'.format(url=url.split('?')[0]))
    headers = helpers.get_cache('headers')
    cookies = helpers.get_cache('cookies')
    with aiohttp.Timeout(10):
        async with session.get(url, headers=headers) as response:
            if json:
                data = await response.json()
            else:
                data = await response.read()
    return data


async def login(session):
    login_info = None
    url = 'https://www.etoro.com/api/sts/v2/login/?client_request_id={}'.format(helpers.device_id())
    payload = settings.payload
    params = {'client_request_id': helpers.device_id(),
              'conditionIncludeDisplayableInstruments': False,
              'conditionIncludeMarkets': False,
              'conditionIncludeMetadata': False,
              }
    headers = {'content-type': 'application/json;charset=UTF-8',
               'AccountType': 'Demo',# Demo
               'ApplicationIdentifier': 'ReToro',
               'ApplicationVersion': 'vp3079',
               'X-CSRF-TOKEN': 'k%7cuGYP%7ci9dVOhujYx0ZsTw%5f%5f',
               'X-DEVICE-ID': helpers.device_id()
               }
    helpers.set_cache('headers', headers)
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