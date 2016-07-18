import asyncio
from my_logging import logger as logging
from concurrent.futures import ProcessPoolExecutor
from advisors.etoro_advisor import EtoroAdvisor



if '__main__' == __name__:
    try:
        executor = ProcessPoolExecutor(1)
        loop = asyncio.get_event_loop()

        etoro = EtoroAdvisor(loop)
        # asyncio.ensure_future(loop.run_in_executor(executor, etoro.etoro_loop))
        coroutine = etoro.etoro_loop()
        loop.run_until_complete(coroutine)
    except KeyboardInterrupt:
        logging.info('Exit')
