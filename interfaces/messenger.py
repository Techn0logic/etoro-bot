from abc import ABCMeta, abstractmethod, abstractproperty

class ABCMessenger():
    __metaclass__ = ABCMeta

    @abstractmethod
    async def send(self, message: str, recipients: dict = []):
        pass
