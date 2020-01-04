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
import multiprocessing
from lib import market, mock

HIGH_OUTLIER = 890 # percentage
LOW_OUTLIER = -89 # percentage

MIN_NUMERICAL_CARDINALITY = 6 # minimum cardinality for a feature to be considered numerical rather than categorical

class DataSet:
    """ This class encapsulates the whole dataset, with DB I/O and preprocessing functions """
    def __init__(self, tickers, lookback, lookfwd, start_year=1970, imputate=True, resample='no', ta=True, patterns=True):
        self.tickers = tickers
        self.lookback = lookback
        self.lookfwd = lookfwd
        self.start_year = start_year
        self.imputate = imputate
        self.resample = resample
        self.ta = ta
        self.patterns = patterns

        self.d_market = { }
        self.d_market['AU'] = self.preprocess_ts(pd.read_sql_query( f"""
                                                                    SELECT date, open, close FROM `indices` 
                                                                    WHERE ticker='XAO[AU]' 
                                                                    AND date > '{self.start_year}-01-01' 
                                                                    ORDER BY date ASC
                                                                    """,
                                                                    'sqlite:///data/stox.db',
                                                                    index_col=['date']))
        self.d_market['US'] = self.preprocess_ts(pd.read_sql_query( f"""
                                                                    SELECT date, open, close FROM `indices` 
                                                                    WHERE ticker='SPX[US]' 
                                                                    AND date > '{self.start_year}-01-01' 
                                                                    ORDER BY date ASC
                                                                    """,
                                                                    'sqlite:///data/stox.db',
                                                                    index_col=['date']))

        self.multi_ts_data()

    def preprocess_ts(self, d):
        """ Preprecess time series data """
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

    def ts_data(self, ticker): # price changes of both the security and the market
        """ Fetch time series data for the requested ticker and generate features """
        d_ticker = None
        if not ticker.startswith('_MOCK'):
            d_ticker = self.preprocess_ts(pd.read_sql_query(    f"""
                                                                SELECT * FROM `equities` 
                                                                WHERE ticker='{ticker}' 
                                                                AND date > '{self.start_year}-01-01' 
                                                                ORDER BY date ASC
                                                                """,
                                                                'sqlite:///data/stox.db',
                                                                index_col=['date']))
        elif ticker == '_MOCK_EASY':
            print('Generating predictable data...')
            d_ticker = self.preprocess_ts(mock.generatePredictableData())
        elif ticker == '_MOCK_HARD':
            print('Generating unpredictable data...')
            d_ticker = self.preprocess_ts(mock.generateRandomData())

        country = ticker[ticker.find("[")+1:ticker.find("]")]

        # Feature generation
        features = [
            (d_ticker['price'], 'price'),
            (d_ticker['pc'], 'spc'),
            (self.d_market[country]['pc'], 'mpc'),
            (d_ticker['pc'] - self.d_market[country]['pc'], 'spc_minus_mpc'),
            # TODO: calculate 'polarity' based on directions of spc & mpc, like 1 if they're both - or +, -1 otherwise
            (d_ticker['open'], 'open'),
            (d_ticker['close'], 'close'),
            (d_ticker['volume'] / d_ticker['volume'].mean(), 'volume')
            ]

        d_ticker['ticker'] = ticker # will be used as index
        features.append((d_ticker['ticker'], 'ticker'))

        # d_ticker['sector'] = sectors.index(companies.loc[ticker]['GICS industry group'])
        # features.append((d_ticker['sector'], 'sector'))

        d_ticker['week'] = d_ticker.index.to_frame()['date'].dt.week
        features.append((d_ticker['week'], 'week'))

        if self.ta and len(d_ticker) > self.lookback: # most of these are 'rolling window ribbon', i.e. multiple features for a range of periods up to self.lookback
            for i in range(2, (self.lookback + 1)):
                features.extend([
                    (abstract.Function('AROONOSC')(d_ticker, timeperiod=i), f'AROONOSC_{i}'),
                    (abstract.Function('ATR')(d_ticker, timeperiod=i) / d_ticker['price'], f'ATR_{i}'),
                    (abstract.Function('CORREL')(d_ticker, timeperiod=i), f'CORREL_{i}'),
                    (abstract.Function('BETA')(d_ticker, timeperiod=i), f'BETA_{i}'),
                    (abstract.Function('CMO')(d_ticker, timeperiod=i), f'CMO_{i}'),
                    (abstract.Function('CCI')(d_ticker, timeperiod=i), f'CCI_{i}')
                ])
                if i >= 6: # these indicators don't work well with very small period sizes
                    features.extend([
                        (abstract.Function('STOCHF')(d_ticker, fastk_period=i, fastd_period=int(round(i * 3 / 5)))['fastk'], f'STOCHF_K_{i}'),
                        (abstract.Function('STOCH')(d_ticker, fastk_period=i, slowk_period=int(round(i * 3 / 5)), slowd_period=int(round(i * 3 / 5)))['slowd'], f'STOCH_D_{i}'),
                        (abstract.Function('STOCH')(d_ticker, fastk_period=i, slowk_period=int(round(i * 3 / 5)), slowd_period=int(round(i * 3 / 5)))['slowk'], f'STOCH_K_{i}'),
                        (abstract.Function('ULTOSC')(d_ticker, timeperiod1=int(round(i / 3)), timeperiod2=int(round(i / 2)), timeperiod3=i), f'ULTOSC_{i}'),
                        (abstract.Function('ADOSC')(d_ticker, fastperiod=int(round(i * 3 / 10)), slowperiod=i), f'ADOSC_{i}')
                    ])

            features.extend([
                (abstract.Function('HT_TRENDMODE')(d_ticker), 'HT_TRENDMODE'), # other HT_ functions cause extra drops
                (abstract.Function('MFI')(d_ticker), 'MFI'),
                (abstract.Function('BOP')(d_ticker), 'BOP')
            ])

            if self.patterns:
                for pattern in ta.get_function_groups()['Pattern Recognition']:
                    features.append((abstract.Function(pattern)(d_ticker), pattern))

        d = pd.concat([d[0] for d in features], axis=1, sort=False)
        d.columns = [d[1] for d in features]

        d.volume[d.volume == 0] = np.nan # Get rid of zero-volume samples

        # Filter out outliers
        d.spc.drop(d.spc[d.spc > HIGH_OUTLIER].index, inplace=True)
        d.spc.drop(d.spc[d.spc < LOW_OUTLIER].index, inplace=True)

        for c in ['spc', 'mpc', 'spc_minus_mpc', 'volume']:
            for i in range(2, (self.lookback + 1)):
                # past values in a rolling window
                past = d[c].shift(i)
                d = pd.concat([d, past.rename(f'past_{c}_{i}')], axis=1)
                # linear regression slopes
                d = pd.concat([d, (abstract.Function('LINEARREG_SLOPE')(d, price=c, timeperiod=i)).rename(f'LINEARREG_SLOPE_{c}_{i}')], axis=1)

        predictor = d.tail(1).copy()
        future = d['spc'].shift(self.lookfwd * -1)

        d = pd.concat([d, future.rename('future')], axis=1).dropna()
        d = pd.concat([d, predictor], axis=0, sort=False)
        d.drop(['price', 'open', 'close'], axis=1, inplace=True)

        return d

    def multi_ts_data(self):
        """ Multiprocessing wrapper for quickly reading data for multiple tickers """
        pool = multiprocessing.Pool(multiprocessing.cpu_count())
        ds = pd.concat(pool.map(self.ts_data, self.tickers), sort=False)
        
        # convert to categorical types on applicable columns (those with fewer than MIN_NUMERICAL_CARDINALITY cardinality)
        cardinalities = ds.apply(pd.Series.nunique)
        categoricals = list(cardinalities[cardinalities < MIN_NUMERICAL_CARDINALITY].index)
        categorical_type_dict = { c: 'category' for c in categoricals }
        
        self.data = ds.astype(categorical_type_dict).set_index('ticker', append=True).sort_index()
