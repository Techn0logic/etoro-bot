# Author: Gael Varoquaux gael.varoquaux@normalesup.org
# License: BSD 3 clause

import datetime
import numpy as np
try:
    from matplotlib.finance import quotes_historical_yahoo
except ImportError:
    from matplotlib.finance import quotes_historical_yahoo_ochl as quotes_historical_yahoo
from sklearn import cluster, covariance

from settings import stocks

def analysis():
    now = datetime.datetime.now()
    ###############################################################################

    d1 = datetime.datetime(2016, now.month, 1)
    d2 = datetime.datetime(2016, now.month, 30)

    symbol_dict = stocks

    symbols, names = np.array(list(symbol_dict.items())).T

    quotes = [quotes_historical_yahoo(symbol, d1, d2, asobject=True)
              for symbol in symbols]

    open = np.array([q.open for q in quotes]).astype(np.float)
    close = np.array([q.close for q in quotes]).astype(np.float)

    # The daily variations of the quotes are what carry most information
    variation = close - open

    ###############################################################################
    # Learn a graphical structure from the correlations
    edge_model = covariance.GraphLassoCV()

    # standardize the time series: using correlations rather than covariance
    # is more efficient for structure recovery
    X = variation.copy().T
    X /= X.std(axis=0)
    edge_model.fit(X)

    ###############################################################################
    # Cluster using affinity propagation
    _, labels = cluster.affinity_propagation(edge_model.covariance_)
    n_labels = labels.max()

    message = ''

    for i in range(n_labels + 1):
        message += 'Cluster %i: %s\r\n' % ((i + 1), ', '.join(names[labels == i]))

    return message

