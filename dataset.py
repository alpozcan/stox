#!/usr/bin/env python3

# DataSet class for Stox

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


import numpy as np
import pandas as pd
import talib as ta
from talib import abstract
import multiprocessing, os
from lib import market, mock

BASE_DIR = os.path.dirname(os.path.realpath(__file__))

HIGH_OUTLIER = 890 # percentage
LOW_OUTLIER = -89 # percentage
MIN_NUMERICAL_CARDINALITY = 6 # minimum cardinality for a feature to be considered numerical rather than categorical

class DataSet:
    """ This class encapsulates the whole dataset, with DB I/O and preprocessing functions """
    def __init__(self, tickers, lookback, lookfwd, start_year=1960, imputate=True, resample='no', ta=True, patterns=True):
        self.tickers = tickers
        self.lookback = lookback
        self.lookfwd = lookfwd
        self.start_year = start_year
        self.imputate = imputate
        self.resample = resample
        self.ta = ta
        self.patterns = patterns

        self.d_index, self.index_features = {}, {}
        self.d_index['US'] = self.get_index_data('US/^GSPC')
        self.index_features['US'] = self.generate_ta_features(self.d_index['US'], 'i')

        self.multi_ts_data()

    def get_index_data(self, index_csv):
        return self.preprocess_ts(pd.read_csv(  f'{BASE_DIR}/data/indices/{index_csv}.csv.xz',
                                                usecols=[0,1,2,3,4,6],
                                                parse_dates=True,
                                                skiprows=[0],
                                                names=['date', 'open', 'high', 'low', 'close', 'volume'],
                                                index_col=['date']))

    def preprocess_ts(self, d):
        """ Preprocess time series data """
        d.index = pd.to_datetime(d.index)

        # gap detection
        dates = d.index.to_series()
        gaps = (dates.diff() / pd.to_timedelta('365 days')).fillna(0)
        gaps = gaps[gaps > 1]
        if len(gaps) > 0:
            last_segment_start = gaps.index[-1]
            d = d.loc[d.index >= last_segment_start]

        # imputation
        if self.imputate:
            # d.close.replace(to_replace=0, method='ffill') # didn't change score with current data
            d.open[d.open == 0 | d.open.isnull()] = d.close.shift(1) # fill in missing open from previous close
            # d.open[d.open == 0] = d.close # for values that the above didn't work, fill in from close. Didn't change score with current data
            if 'high' in d.columns:
                d.high[(d.high == 0 | d.high.isnull()) & (d.close > d.open)] = d.close
                d.high[(d.high == 0 | d.high.isnull()) & (d.close <= d.open)] = d.open
            if 'low' in d.columns:
                d.low[(d.low == 0 | d.low.isnull()) & (d.close > d.open)] = d.open
                d.low[(d.low == 0 | d.low.isnull()) & (d.close <= d.open)] = d.close

        # pad (forward fill) for weekend days so that resampling to longer periods don't result in gaps
        d = d.resample('D').pad()
        d.at[d.index.weekday > 4, 'volume'] = 0

        # resample
        if self.resample != 'no':
            for c in d.columns:
                if c == 'open':
                    d[c] = d[c].resample(self.resample).first()
                elif c == 'high':
                    d[c] = d[c].resample(self.resample).max()
                elif c == 'low':
                    d[c] = d[c].resample(self.resample).min()
                elif c == 'close':
                    d[c] = d[c].resample(self.resample).last()
                elif c == 'volume':
                    d[c] = d[c].resample(self.resample).sum()
            d.dropna(inplace=True)

        # calculate nominal price and deltas
        d['price'] = (d['open'] + d['close']) / 2
        d['pc'] = (d['price'].pct_change() * 100)
        d.dropna(inplace=True)

        return d

    def generate_ta_features(self, data, prefix=''):
        features = []
        for i in range(2, (self.lookback + 1)):
            features.extend([
                (abstract.Function('AROONOSC')(data, timeperiod=i), f'{prefix}AROONOSC_{i}'),
                (abstract.Function('ATR')(data, timeperiod=i) / data['price'], f'{prefix}ATR_{i}'),
                (abstract.Function('CORREL')(data, timeperiod=i), f'{prefix}CORREL_{i}'),
                (abstract.Function('BETA')(data, timeperiod=i), f'{prefix}BETA_{i}'),
                (abstract.Function('CMO')(data, timeperiod=i), f'{prefix}CMO_{i}'),
                (abstract.Function('CCI')(data, timeperiod=i), f'{prefix}CCI_{i}')
            ])
            if i >= 6: # these indicators don't work well with very small period sizes
                features.extend([
                    (abstract.Function('STOCHF')(data, fastk_period=i, fastd_period=int(round(i * 3 / 5)))['fastk'], f'{prefix}STOCHF_K_{i}'),
                    (abstract.Function('STOCH')(data, fastk_period=i, slowk_period=int(round(i * 3 / 5)), slowd_period=int(round(i * 3 / 5)))['slowd'], f'{prefix}STOCH_D_{i}'),
                    (abstract.Function('STOCH')(data, fastk_period=i, slowk_period=int(round(i * 3 / 5)), slowd_period=int(round(i * 3 / 5)))['slowk'], f'{prefix}STOCH_K_{i}'),
                    (abstract.Function('ULTOSC')(data, timeperiod1=int(round(i / 3)), timeperiod2=int(round(i / 2)), timeperiod3=i), f'{prefix}ULTOSC_{i}'),
                    (abstract.Function('ADOSC')(data, fastperiod=int(round(i * 3 / 10)), slowperiod=i), f'{prefix}ADOSC_{i}')
                ])

        features.extend([
            (abstract.Function('HT_TRENDMODE')(data), f'{prefix}HT_TRENDMODE'), # other HT_ functions cause extra drops
            (abstract.Function('MFI')(data), f'{prefix}MFI'),
            (abstract.Function('BOP')(data), f'{prefix}BOP')
        ])

        if self.patterns:
            for pattern in ta.get_function_groups()['Pattern Recognition']:
                features.append((abstract.Function(pattern)(data), prefix + pattern))

        return features

    def ts_data(self, ticker): # price changes of both the security and the market
        """ Fetch time series data for the requested ticker and generate features """
        d_ticker = None
        country = ticker[-2:]
        if not ticker.startswith('_MOCK'):
            d_ticker = self.preprocess_ts(pd.read_sql_query(    f"""
                                                                SELECT * FROM `{ticker}` 
                                                                WHERE date > '{self.start_year}-01-01' 
                                                                ORDER BY date ASC
                                                                """,
                                                                f'sqlite:////var/stox.db',
                                                                index_col=['date']))
        elif ticker.startswith('_MOCK_EASY'):
            print('Generating predictable data...')
            d_ticker = self.preprocess_ts(mock.generatePredictableData())
        elif ticker.startswith('_MOCK_HARD'):
            print('Generating unpredictable data...')
            d_ticker = self.preprocess_ts(mock.generateRandomData())

        if len(d_ticker) <= self.lookback:
            return pd.DataFrame()

        # Feature generation
        features = [
            (d_ticker['price'], 'price'),
            (d_ticker['pc'], 'spc'),
            # TODO: calculate 'polarity' based on directions of spc & mpc, like 1 if they're both - or +, -1 otherwise
            (d_ticker['open'], 'open'),
            (d_ticker['close'], 'close'),
            (d_ticker['volume'] / d_ticker['volume'].mean(), 'volume'),

            (self.d_index[country]['pc'], 'ipc'),
            (d_ticker['pc'] - self.d_index[country]['pc'], 'spc_minus_ipc'),
            # (self.d_index['volume'] / self.d_index['volume'].mean(), 'ivolume')
            ]

        d_ticker['ticker'] = ticker # will be used as index
        features.append((d_ticker['ticker'], 'ticker'))

        # d_ticker['sector'] = sectors.index(companies.loc[ticker]['GICS industry group'])
        # features.append((d_ticker['sector'], 'sector'))

        # d_ticker['week'] = d_ticker.index.to_frame()['date'].dt.week
        # features.append((d_ticker['week'], 'week'))

        if self.ta: # most of these are 'rolling window ribbon', i.e. multiple features for a range of periods up to self.lookback
            features.extend(self.generate_ta_features(d_ticker))

        d = pd.concat([d[0] for d in (features + self.index_features[country])], axis=1, sort=False)
        d.columns = [d[1] for d in (features + self.index_features[country])]

        # Filter out outliers
        d.spc.drop(d.spc[d.spc > HIGH_OUTLIER].index, inplace=True)
        d.spc.drop(d.spc[d.spc < LOW_OUTLIER].index, inplace=True)

        # past values in a rolling window
        for c in ['spc', 'ipc', 'spc_minus_ipc', 'volume']:
            for i in range(2, (self.lookback + 1)):
                d = pd.concat([d, d[c].shift(i).rename(f'past_{c}_{i}')], axis=1)
                d = pd.concat([d, (abstract.Function('LINEARREG_SLOPE')(d, price=c, timeperiod=i)).rename(f'LINEARREG_SLOPE_{c}_{i}')], axis=1)

        predictor = d.tail(1).copy()
        future = d['spc'].shift(self.lookfwd * -1)

        d = pd.concat([d, future.rename('future')], axis=1)
        d = pd.concat([d, predictor], axis=0, sort=False)

        d.drop(['price', 'open', 'close'], axis=1, inplace=True)
        d.volume[d.volume == 0] = np.nan # Get rid of zero-volume samples
        d.future[d.future == 0] = np.nan # Also where the target is zero
        d.dropna(inplace=True)

        return d

    def multi_ts_data(self):
        """ Multiprocessing wrapper for quickly reading data for multiple tickers """
        pool = multiprocessing.Pool(multiprocessing.cpu_count())
        ds = pd.concat(pool.map(self.ts_data, self.tickers), sort=False)

        # convert to categorical types on applicable columns (those with fewer than MIN_NUMERICAL_CARDINALITY cardinality)
        cardinalities = ds.apply(pd.Series.nunique)
        categoricals = list(cardinalities[cardinalities < MIN_NUMERICAL_CARDINALITY].index)
        categorical_type_dict = { c: 'category' for c in categoricals }

        ds = ds.astype(categorical_type_dict, copy=False)
        ds.set_index('ticker', append=True, inplace=True)
        ds.sort_index(inplace=True)

        self.data = ds
