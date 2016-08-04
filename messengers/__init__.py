from messengers.smtp import SmtpAlert
from interfaces.messenger import ABCMessenger
from settings import messenger, recipients
import sys


class MessageManager(ABCMessenger):

    def __init__(self, loop):
        self.loop = loop

    def send(self, message=[], title=''):
        if hasattr(sys.modules[__name__], messenger):
            my_messenger = getattr(sys.modules[__name__], messenger)(self.loop)
        my_messenger.send("\r\n\r\n".join(message), title=title, recipients=recipients[messenger])