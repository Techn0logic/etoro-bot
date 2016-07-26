class BackTesting(object):
    def __init__(self, dataframe, class_strategy, balance, instrument, trade_obj):
        if dataframe:
            if 'asc' not in dataframe[0]:
                raise Exception('Option asc was not found in dataframe')
            if 'bid' not in dataframe[0]:
                raise Exception('Option bid was not found in dataframe')
            if 'date' not in dataframe[0]:
                raise Exception('Option date was not found in dataframe')
            object_strategy = class_strategy(balance, instrument, trade_obj)
            if hasattr(object_strategy, 'tick'):
                start = getattr(object_strategy, 'start')
                start(dataframe[0]['asc'], dataframe[0]['bid'], dataframe[0]['date'])
                method_tick = getattr(object_strategy, 'tick')
                for data in dataframe:
                    method_tick(data['asc'], data['bid'], data['date'])
                getattr(object_strategy, 'finish')(dataframe[-1]['asc'], dataframe[-1]['bid'], dataframe[-1]['date'])
            else:
                raise Exception('Method tick was not found')
        else:
            raise Exception('Dataframe is empty!')