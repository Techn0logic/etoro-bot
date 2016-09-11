import asyncio
from my_logging import logger as logging
from concurrent.futures import ProcessPoolExecutor
from advisors.etoro_advisor import EtoroAdvisor
from advisors.yahoo_advisor import YahooAdvisor
from advisors.strategy_advisor import StrategyAdvisor
from messengers import MessageManager
from science import cluster
import datetime
import settings


async def eternal_cycle():
    while True:
        datetime_obj = datetime.datetime.now()
        current_time = datetime_obj.time()
        week_day = datetime_obj.weekday()
        if str(current_time).find(settings.strtime_send_message) >= 0:
            etoro_message = yahoo_message = cluster_message = ''
            try:
                etoro_message = await etoro.loop()
            except Exception as e:
                logging.error(str(e))

            try:
                yahoo_message = await yahoo.loop()
            except Exception as e:
                logging.error(str(e))

            try:
                cluster_message = cluster.analysis()
            except Exception as e:
                logging.error(str(e))

            messenger.send([cluster_message, etoro_message, yahoo_message], title='Рекомендации по инструментам etoro')
        try:
            if week_day != 6 and week_day != 5:
                await strategy.loop()
        except Exception as e:
            logging.error(str(e))
        await asyncio.sleep(5)

if '__main__' == __name__:
    try:
        executor = ProcessPoolExecutor(1)
        loop = asyncio.get_event_loop()
        messenger = MessageManager(loop)
        etoro = EtoroAdvisor(loop)
        yahoo = YahooAdvisor(loop)
        strategy = StrategyAdvisor(loop)
        # asyncio.ensure_future(loop.run_in_executor(executor, etoro.etoro_loop))
        loop.run_until_complete(eternal_cycle())
    except KeyboardInterrupt:
        logging.info('Exit')
