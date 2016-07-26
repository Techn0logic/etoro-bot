from abc import ABCMeta, abstractmethod, abstractproperty

class ABCStrategy():
    __metaclass__ = ABCMeta

    @abstractmethod
    def __init__(self, balance, instrument, trade_obj):
        pass

    @abstractmethod
    def start(self):
        pass

    @abstractmethod
    def tick(self, asc: float, bid: float, date: str):
        pass

    @abstractmethod
    def finish(self):
        pass
