import etoro
import settings

from interfaces.advisor import ABCAdvisor
import datetime


class YahooAdvisor(ABCAdvisor):
    def __init__(self, in_loop, **kwargs):
        self.last_run = None
        super().__init__(in_loop, **kwargs)
        self._message = None

    async def loop(self):
        datetime_obj = datetime.datetime.today()
        current_time = datetime_obj.time()
        if str(current_time).find(settings.strtime_send_message) != 0:
            return False
        if self.last_run is not None and current_time.hour == self.last_run.hour and \
                        current_time.day == self.last_run.day:
            return False
        self._message = '\r\nYahoo\r\n\r\n'
        self._message += 'Recommendation\r\n'
        for stock in settings.stocks:
            url = 'https://query2.finance.yahoo.com/v10/finance/quoteSummary/{stock}?formatted=true&crumb=a9I3lxfM3R3&lang=en-US&region=US&modules=upgradeDowngradeHistory%2CrecommendationTrend%2CearningsTrend&corsDomain=finance.yahoo.com'.format(
                stock=stock
            )
            yahoo_data = await etoro.get(self.session, url)
            if yahoo_data is not None:
                data = yahoo_data['quoteSummary']['result'][0]
                recomendations = data['recommendationTrend']['trend']
                self._message += '\r\n{} ({})\r\n'.format(settings.stocks[stock], stock)
                for recomendation in recomendations:
                    self._message += '{period}: strongBuy: {strongBuy}, buy {buy}, sell:{sell}, hold:{hold}, ' \
                                    'strongSell: {strongSell}\r\n'.format(period=recomendation['period'],
                                                                      strongBuy=recomendation['strongBuy'],
                                                                      buy=recomendation['buy'],
                                                                      hold=recomendation['hold'],
                                                                      sell=recomendation['sell'],
                                                                      strongSell=recomendation['strongSell'], )
                earnings = data['earningsTrend']['trend']
                self._message += '\r\nEarning Trend\r\n'
                for earning in earnings:
                    self._message += '{period}: Growth: {growth}, earningsEstimate: {earningsEstimate}\r\n'.format(
                        period=earning['period'], growth=earning['growth']['fmt'] if 'fmt' in earning['growth'] else '',
                        earningsEstimate=earning['earningsEstimate']['avg']['fmt']
                        if 'fmt' in earning['earningsEstimate']['avg'] else 'None')
        self.message = self._message
        self.last_run = datetime.datetime.today()
