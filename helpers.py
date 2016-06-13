import string
import random
import os
import json
import time

def id_generator(size=8, chars='absdef' + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


def device_id():
    pattern = "xxxxtxxx-xxxx-4xxx-yxxx-xxxxxxtxxxxx"
    pattern = pattern.replace('t', hex(int(time.time()) % 16).replace('0x', ''))
    pattern_list = list(pattern)
    for key, symblol in enumerate(list(pattern_list)):
        if symblol == 'x' or symblol == 'y':
            n = 16 * random.random()
            if n:
                n = n / 3
            else:
                n = 8
            pattern_list[key] = hex(int(n)).replace('0x', '')
    return "".join(pattern_list)


def set_cache(key: string, data: dict) -> None:
    base_path = os.path.dirname(__file__)
    with open(os.path.join(base_path, 'temp', key), 'w') as fd:
        fd.write(json.dumps(data))
    fd.close()


def cookies_parse(response_cookies):
    cookies_dict = {}
    cookies = response_cookies
    for cookie in str(cookies).split('\r\n'):
        cookie = cookie.split(' ')
        if len(cookie) > 1:
            cookie_list = cookie[1].split('=')
            if len(cookie_list) == 2:
                cookies_dict[cookie_list[0]] = cookie_list[1]
            elif len(cookie_list) > 2:
                cookies_dict[cookie_list[0]] = cookie_list[1]
                for i in range(len(cookie_list) - 2):
                    cookies_dict[cookie_list[0]] += '='
    return cookies_dict


def get_cache(key: string, period: int=1) -> dict:
    base_path = os.path.dirname(__file__)
    path = os.path.join(base_path, 'temp', key)
    if os.path.isfile(path):
        mod_time = time.time() - os.path.getmtime(path)
        if mod_time > period*3600:
            return {}
        with open(path, 'r') as fd:
            file_content = fd.read()
        fd.close()
        return json.loads(file_content)
    else:
        return {}


if '__main__' == __name__:
    print(device_id())
