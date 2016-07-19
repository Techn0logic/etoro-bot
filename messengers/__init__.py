from messengers.smtp import SmtpAlert
from interfaces.messenger import ABCMessenger
from settings import messenger, recipients
import sys

class Messenger(ABCMessenger):

    async def send(self, message):
        if hasattr(sys.modules[__name__], messenger):
            my_messenger = getattr(sys.modules[__name__], messenger)()
        await my_messenger.send(message, recipients)