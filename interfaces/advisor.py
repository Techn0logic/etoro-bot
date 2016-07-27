from abc import ABCMeta, abstractmethod, abstractproperty

class ABCAdvisor():
    __metaclass__ = ABCMeta

    @abstractmethod
    def __init__(self, in_loop):
        pass

    @abstractmethod
    async def loop(self):
        pass
