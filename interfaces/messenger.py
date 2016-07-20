from abc import ABCMeta, abstractmethod, abstractproperty

class ABCMessenger():
    __metaclass__ = ABCMeta

    def __init__(self, loop):
        self.loop = loop

    @abstractmethod
    async def send(self, message: str, recipients: dict=[], title: str=''):
        pass
