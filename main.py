import asyncio
from my_logging import logger as logging
from concurrent.futures import ThreadPoolExecutor
from advisors.etoro_advisor import EtoroAdvisor
from advisors.yahoo_advisor import YahooAdvisor
from advisors.strategy_advisor import StrategyAdvisor
from messengers import MessageManager
import time
import settings
# from science import cluster


if '__main__' == __name__:
    try:
        is_running = True

        def messages_listen():
            while is_running:
                messages = []
                for client in messenger.clients:
                    message = client.get_message()
                    if message is not None and message:
                        messages.append(message)
                        client.message = ''
                if messages and not settings.debug:
                    messenger.send(messages, title='Мои финансы')
                time.sleep(1)
        executor = ThreadPoolExecutor()

        loop = asyncio.get_event_loop()
        messenger = MessageManager(loop)
        messenger.clients = []

        etoro = EtoroAdvisor(loop, messenger=messenger)
        yahoo = YahooAdvisor(loop, messenger=messenger)
        strategy = StrategyAdvisor(loop, messenger=messenger)
        while is_running:
            tasks = [
                loop.create_task(etoro.loop()),
                loop.create_task(yahoo.loop()),
                loop.create_task(strategy.loop()),
                loop.create_task(strategy.fast_change_detect()),
                # loop.create_task(strategy.check_fast_orders()),
            ]
            asyncio.ensure_future(loop.run_in_executor(executor, messages_listen))
            loop.run_until_complete(asyncio.wait(tasks))
    except KeyboardInterrupt:
        logging.info('Exit')
        is_running = False
        try:
            loop.close()
        except: pass


