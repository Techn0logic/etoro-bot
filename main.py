import asyncio
import aiohttp
import json

async def fetch_page(session, url):
    url = 'https://www.etoro.com/api/sts/v2/login/?client_request_id=4ca2b203-414e-4c23-82ff-851192b06c65'
    payload = {'Password': 'hgf658y09bd', 'UserLoginIdentifier': 'kislenko-artem', 'Username': 'kislenko-artem',}
    # cookies = dict(cookies_are='working')
    headers = {'content-type': 'application/json;charset=UTF-8',
               'AccountType': 'Real',
               'ApplicationIdentifier': 'ReToro',
               'ApplicationVersion': 'vp3079',
               'X-CSRF-TOKEN': 'k%7cuGYP%7ci9dVOhujYx0ZsTw%5f%5f',
               'X-DEVICE-ID': 'ee2838e3-831c-477a-be99-a3a90d372a88'
               }

    with aiohttp.Timeout(10):
        async with session.post(url,
                                data=json.dumps(payload),
                                headers=headers) as response:
            assert response.status == 201
            login_content_josn = await response.read()
    login_content = json.loads(login_content_josn.decode('utf-8'))
    params = {'client_request_id': '75d399e3-a7fb-489a-a0b3-b7ef2d9fed23',
              'conditionIncludeDisplayableInstruments': False,
              'conditionIncludeMarkets': False,
              'conditionIncludeMetadata': False,
              }
    headers['Authorization'] = login_content['accessToken']
    with aiohttp.Timeout(10):
        async with session.get('https://www.etoro.com/api/logininfo/v1.1/logindata' ,params=params,
                                headers=headers) as response:
            login_info = await response.read()
    print(login_info)

loop = asyncio.get_event_loop()
with aiohttp.ClientSession(loop=loop) as session:
    content = loop.run_until_complete(
        fetch_page(session, 'https://www.etoro.com/api/sts/v2/login/?client_request_id=b878533a-862d-4ff6-965e-54a3e35f663f'))
    print(content)