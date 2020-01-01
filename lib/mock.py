#!/usr/bin/env python3

# Data generation functions for mock testing of model performance within stox

# Copyright (C) 2017-2020 Gokalp Ozcan

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

COLUMNS = ['date', 'ticker', 'open', 'high', 'low', 'close', 'volume']

def generatePredictableData(length=20000):
    """ Generates monotonous data that is very predictable """
    data = pd.DataFrame(columns=COLUMNS)
    t = '_MOCK_EASY'
    d = datetime.strptime('Jan 1 1970', '%b %d %Y')

    for i in range(length):
        d = d + timedelta(days=1)
        o = (i + 1) / 1000
        h = o * 1.005
        l = o * 0.995
        c = o * 1.01
        v = int(c * 1000)

        data.loc[i] = pd.Series({'date': d, 'ticker': t, 'open': o, 'high': h, 'low': l, 'close': c, 'volume': v })

    return data.set_index('date')

def generateRandomData(length=20000):
    """ Generates gaussian-distributed random data that should be unpredictable """
    data = pd.DataFrame(columns=COLUMNS)
    t = '_MOCK_HARD'
    d = datetime.strptime('Jan 1 1970', '%b %d %Y')

    old_c = 100000
    for i in range(length):
        # old_c = 100000 # comment this out to base the new price on previous day
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
