import asyncio
from my_logging import logger as logging
from concurrent.futures import ProcessPoolExecutor
from advisors.etoro_advisor import EtoroAdvisor
from advisors.strategy_advisor import StrategyAdvisor

async def eternal_cycle():
    while True:
        # await etoro.loop()
        # await asyncio.sleep(3600 * 24)
        await strategy.loop()
        await asyncio.sleep(2)

if '__main__' == __name__:
    try:
        executor = ProcessPoolExecutor(1)
        loop = asyncio.get_event_loop()

        etoro = EtoroAdvisor(loop)
        strategy = StrategyAdvisor(loop)
        # asyncio.ensure_future(loop.run_in_executor(executor, etoro.etoro_loop))
        loop.run_until_complete(eternal_cycle())
    except KeyboardInterrupt:
        logging.info('Exit')
