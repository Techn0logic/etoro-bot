from interfaces.messenger import ABCMessenger

class SmtpAlert(ABCMessenger):

    async def send(self, message, recipients):
        print(message, recipients)