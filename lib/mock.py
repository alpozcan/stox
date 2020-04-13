#!/usr/bin/env python3
# Data generation functions for mock testing of model performance within stox

import pandas as pd
import numpy as np
from datetime import date, datetime, timedelta
import random

COLUMNS = ['date', 'ticker', 'open', 'high', 'low', 'close', 'volume']

def generatePredictableData():
    """ Generates monotonous data that is very predictable """
    data = pd.DataFrame(columns=COLUMNS)
    t = '_MOCK_EASY'
    d = datetime.strptime('Jan 1 2000', '%b %d %Y')

    for i in range((datetime.now() - d).days):
        d = d + timedelta(days=1)
        o = (i*i + 1) / 1000
        h = o * 1.005
        l = o * 0.995
        c = o * 1.01
        v = int(c * 1000)

        data.loc[i] = pd.Series({'date': d, 'ticker': t, 'open': o, 'high': h, 'low': l, 'close': c, 'volume': v })

    return data.set_index('date')

def generateRandomData():
    """ Generates gaussian-distributed random data that should be unpredictable """
    data = pd.DataFrame(columns=COLUMNS)
    t = '_MOCK_HARD'
    d = datetime.strptime('Jan 1 2000', '%b %d %Y')

    old_c = 100000
    for i in range((datetime.now() - d).days):
        old_c = 1 # comment this out to base the new price on the previous day
        d = d + timedelta(days=1)
        o = old_c * random.gauss(1, 0.04)
        c = o * random.gauss(1, 0.04)
        h, l = None, None
        if o > c:
            h = o * random.gauss(1.04, 0.039)
            l = c * random.gauss(0.96, 0.039)
        else:
            h = c * random.gauss(1.04, 0.039)
            l = o * random.gauss(0.96, 0.039)
        v = random.randint(100, 1000000)

        old_c = c

        data.loc[i] = pd.Series({'date': d, 'ticker': t, 'open': o, 'high': h, 'low': l, 'close': c, 'volume': v })

    return data.set_index('date')
