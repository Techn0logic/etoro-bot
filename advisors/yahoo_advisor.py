import aiohttp
import etoro
import settings

from interfaces.advisor import ABCAdvisor
import datetime


class YahooAdvisor(ABCAdvisor):
    def __init__(self, in_loop, **kwargs):
        if 'messenger' in kwargs:
            kwargs['messenger'].clients.append(self)
        self.session = aiohttp.ClientSession(loop=in_loop)
        self.message = ''

    async def loop(self):
        datetime_obj = datetime.datetime.now()
        current_time = datetime_obj.time()
        if str(current_time).find(settings.strtime_send_message) != 0:
            return False

        self.message = '\r\nYahoo\r\n\r\n'
        self.message += 'Recommendation\r\n'
        for stock in settings.stocks:
            url = 'https://query2.finance.yahoo.com/v10/finance/quoteSummary/{stock}?formatted=true&crumb=a9I3lxfM3R3&lang=en-US&region=US&modules=upgradeDowngradeHistory%2CrecommendationTrend%2CearningsTrend&corsDomain=finance.yahoo.com'.format(
                stock=stock
            )
            yahoo_data = await etoro.get(self.session, url)
            data = yahoo_data['quoteSummary']['result'][0]
            recomendations = data['recommendationTrend']['trend']
            self.message += '\r\n{} ({})\r\n'.format(settings.stocks[stock], stock)
            for recomendation in recomendations:
                self.message += '{period}: strongBuy: {strongBuy}, buy {buy}, sell:{sell}, hold:{hold}, ' \
                                'strongSell: {strongSell}\r\n'.format(period=recomendation['period'],
                                                                  strongBuy=recomendation['strongBuy'],
                                                                  buy=recomendation['buy'],
                                                                  hold=recomendation['hold'],
                                                                  sell=recomendation['sell'],
                                                                  strongSell=recomendation['strongSell'], )
            earnings = data['earningsTrend']['trend']
            self.message += '\r\nEarning Trend\r\n'
            for earning in earnings:
                self.message += '{period}: Growth: {growth}, earningsEstimate: {earningsEstimate}\r\n'.format(
                    period=earning['period'], growth=earning['growth']['fmt'] if 'fmt' in earning['growth'] else '',
                    earningsEstimate=earning['earningsEstimate']['avg']['fmt']
                    if 'fmt' in earning['earningsEstimate']['avg'] else 'None')

    def get_message(self):
        return self.message
