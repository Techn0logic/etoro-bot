# Author: Gael Varoquaux gael.varoquaux@normalesup.org
# License: BSD 3 clause

import datetime

import numpy as np
import matplotlib.pyplot as plt
try:
    from matplotlib.finance import quotes_historical_yahoo
except ImportError:
    from matplotlib.finance import quotes_historical_yahoo_ochl as quotes_historical_yahoo
from matplotlib.collections import LineCollection

from sklearn import cluster, covariance, manifold
import time


start = time.time()
###############################################################################
# Retrieve the data from Internet

# Choose a time period reasonnably calm (not too long ago so that we get
# high-tech firms, and before the 2008 crash)
d1 = datetime.datetime(2016, 7, 1)
d2 = datetime.datetime(2016, 7, 30)

# kraft symbol has now changed from KFT to MDLZ in yahoo
symbol_dict = {
    'AAPL': 'Apple',
    'TWTR': 'Twitter',
    'CBS': 'CBS',
    'GOOG': 'Google',
    'FB': 'FaceBook',
    'MSFT': 'Microsoft',
    'NVDA': 'Nvidia',
    'CSCO': 'Cisco',
    'YHOO': 'Yahoo',
    'AMZN': 'Amazon',
    'INTC': 'Intel',
    'EBAY': 'Ebay',
    'YNDX': 'Yandex',
    'QIWI': 'Qiwi',
    'TSLA': 'Tesla',
    'EA': 'Electronic Arts',
    'ADBE': 'Adobe',
    'BIDU': 'Baidu',
    'AAL': 'American Airlines',
    'NTDOY': 'Nintendo',
}

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

for i in range(n_labels + 1):
    print('Cluster %i: %s' % ((i + 1), ', '.join(names[labels == i])))

