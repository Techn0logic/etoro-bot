from abc import ABCMeta, abstractmethod, abstractproperty
import settings
import aiohttp

class ABCAdvisor():
    __metaclass__ = ABCMeta

    def __init__(self, in_loop, **kwargs):
        if 'messenger' in kwargs:
            kwargs['messenger'].clients.append(self)
        self.message = None
        self.session = aiohttp.ClientSession(loop=in_loop)

    @abstractmethod
    async def loop(self):
        pass

    def get_message(self):
        return self.message
