import asyncio
from my_logging import logger as logging
from concurrent.futures import ThreadPoolExecutor
from advisors.etoro_advisor import EtoroAdvisor
from advisors.yahoo_advisor import YahooAdvisor
from advisors.strategy_advisor import StrategyAdvisor
from messengers import MessageManager
import time
# from science import cluster


if '__main__' == __name__:
    try:
        def messages_listen():
            while not loop.is_closed():
                messages = []
                for client in messenger.clients:
                    if client.get_message():
                        messages.append(client.get_message())
                        client.message = ''
                if messages:
                    messenger.send(messages, title='Мои финансы')
                time.sleep(1)
        executor = ThreadPoolExecutor()

        loop = asyncio.get_event_loop()
        messenger = MessageManager(loop)
        messenger.clients = []

        etoro = EtoroAdvisor(loop, messenger=messenger)
        yahoo = YahooAdvisor(loop, messenger=messenger)
        strategy = StrategyAdvisor(loop, messenger=messenger)
        while True:
            tasks = [
                loop.create_task(etoro.loop()),
                loop.create_task(yahoo.loop()),
                loop.create_task(strategy.loop()),
                loop.create_task(strategy.fast_grow()),
            ]
            asyncio.ensure_future(loop.run_in_executor(executor, messages_listen))
            loop.run_until_complete(asyncio.wait(tasks))
    except KeyboardInterrupt:
        loop.close()
        logging.info('Exit')
