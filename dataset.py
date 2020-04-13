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
import multiprocessing, os, logging
from lib.db import db_connection
import lib.tickers as ticker_lists
from lib.suppress_stdout_stderr import suppress_stdout_stderr
import pyodbc
from fbprophet import Prophet

logging.getLogger('fbprophet').setLevel(logging.WARNING)

BASE_DIR = os.path.dirname(os.path.realpath(__file__))

TABLE = '[stox].[stocks].[daily]'

HIGH_OUTLIER = 890 # percentage
LOW_OUTLIER = -89 # percentage

class DataSet:
    """ This class encapsulates the whole dataset, with DB I/O and preprocessing functions """
    def __init__(self, tickers, lookback, lookfwd, predicate="date >= '1960-01-01'", imputate=True, resample='no', ta=True, patterns=True, keep_predictors=False):
        self.tickers = tickers
        self.markets = set(t[0] for t in tickers)
        self.lookback = lookback
        self.lookfwd = lookfwd
        self.predicate = predicate
        self.imputate = imputate
        self.resample = resample
        self.ta = ta
        self.patterns = patterns
        self.keep_predictors = keep_predictors

        self.d_index, self.index_features = { }, { }
        for i in ticker_lists.indices():
            market = i[0]
            if market in self.markets:
                self.d_index[market] = self.ts_data(i, market_index=True)
                self.index_features[market] = self.generate_ta_features(self.d_index[market], 'i_')

        self.multi_ts_data()

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
            d.close.replace(to_replace=[0, np.nan, None], method='ffill', inplace=True)
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

        # No column except 'volume' can have a zero value
        # assert 0 not in (d.iloc[:,:-1]).values

        # calculate nominal price and deltas
        d['price'] = (d['open'] + d['close']) / 2
        d['gap']    = d['open'] - d['close'].shift(1)
        d['spread'] = d['high'] - d['low']
        d['pc'] = (d['price'].pct_change() * 100)

        if len(d.dropna()) <= self.lookback:
            return

        # fbprophet predictions as a feature
        dp = pd.concat([d.index.to_series(), d.close], axis=1)
        dp.columns = ['ds', 'y']
        with suppress_stdout_stderr():
            m = Prophet(seasonality_mode='multiplicative').fit(dp)
        ftr = m.make_future_dataframe(periods=self.lookfwd, freq=self.resample)
        forecast = (m.predict(ftr).shift(-self.lookfwd))[['ds', 'yhat']]
        forecast.columns = ['date', 'forecast']
        forecast.set_index('date', inplace=True)
        d = pd.concat([d, forecast], axis=1)
        d['forecast'] = d['forecast'] / d['close']
        d.dropna(inplace=True)

        return d

    def generate_ta_features(self, data, prefix=''):
        prefix = 'f_' + prefix
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

            for c in ['close', 'volume']:
                features.append((abstract.Function('LINEARREG_SLOPE')(data, price=c, timeperiod=i), f'{prefix}LINEARREG_SLOPE_{c}_{i}'))

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

    def ts_data(self, ticker, market_index=False): # price changes of both the security and the market
        """ Fetch time series data for the requested ticker and generate features """
        dbconn = db_connection()
        query = f"""
                SELECT * FROM {TABLE} 
                WHERE {self.predicate}
                    AND market = '{ticker[0]}' 
                    AND ticker = '{ticker[1]}' 
                ORDER BY date ASC
                """
        data = pd.read_sql_query(   query,
                                    dbconn,
                                    index_col=['date'])
        dbconn.close()
        d_ticker = self.preprocess_ts(data)

        if market_index:
            return d_ticker

        if d_ticker is None:
            return pd.DataFrame()

        # Feature generation
        features = [
            (d_ticker['price'], 'price'),
            # price over its max() or min() would result in data leak
            # (d_ticker['price'] / d_ticker['price'].mean(), 'f_price'), # potential data leak. Negligable difference in score, so commented out to be safe.
            (d_ticker['gap'] / d_ticker['price'], 'f_gap'),
            (d_ticker['spread'] / d_ticker['price'], 'f_spread'),
            (d_ticker['pc'], 'f_spc'),
            (d_ticker['open'], 'open'),
            (d_ticker['close'], 'close'),
            ((d_ticker['volume'] / d_ticker['volume'].mean()) * (d_ticker['price'] / d_ticker['price'].mean()), 'f_volume'),
            (d_ticker['forecast'], 'f_forecast'),

            (self.d_index[ticker[0]]['pc'], 'f_ipc'),
            (d_ticker['pc'] - self.d_index[ticker[0]]['pc'], 'f_spc_minus_ipc'),
            # TODO: calculate 'polarity' based on directions of spc & mpc, like 1 if they're both - or +, -1 otherwise
            # (self.d_index[ticker[0]]['volume'] / self.d_index[ticker[0]]['volume'].mean(), 'f_ivolume')
            ]

        d_ticker['ticker'] = '_'.join([ticker[0], ticker[1]]) # will be used as index
        features.append((d_ticker['ticker'], 'ticker'))

        # d_ticker['sector'] = sectors.index(companies.loc[ticker]['GICS industry group'])
        # features.append((d_ticker['sector'], 'sector'))

        # d_ticker['week'] = d_ticker.index.to_frame()['date'].dt.week
        # features.append((d_ticker['week'], 'week'))

        if self.ta: # most of these are 'rolling window ribbon', i.e. multiple features for a range of periods up to self.lookback
            features.extend(self.generate_ta_features(d_ticker))

        d = pd.concat([d[0] for d in (features + self.index_features[ticker[0]])], axis=1, sort=False)
        d.columns = [d[1] for d in (features + self.index_features[ticker[0]])]

        # Filter out outliers
        d.f_spc.drop(d.f_spc[d.f_spc > HIGH_OUTLIER].index, inplace=True)
        d.f_spc.drop(d.f_spc[d.f_spc < LOW_OUTLIER].index, inplace=True)

        # past values in a rolling window
        for c in ['f_spc', 'f_ipc', 'f_spc_minus_ipc', 'f_volume']:
            for i in range(2, (self.lookback + 1)):
                d = pd.concat([d, d[c].shift(i).rename(f'f_past_{c[2:]}_{i}')], axis=1)

        predictor = d[d.f_spc.notnull()].tail(1).copy()

        # calculate and insert the target variable column
        future = (d['price'].shift(self.lookfwd * -1) / d['price'] - 1) * 100

        d = pd.concat([d, future.rename('future')], axis=1)
        # d = pd.concat([d, predictor], axis=0, sort=False)

        # debug
        # if ticker[1] == 'ANZ':
        #     d.to_csv(f'{BASE_DIR}/debug-feature-dump-{ticker[1]}.csv')

        d.f_volume[d.f_volume == 0] = np.nan # Get rid of zero-volume samples
        # d.future[d.future == 0] = np.nan # Also where the target is zero
        d.dropna(inplace=True)
        if self.keep_predictors:
            d = pd.concat([d, predictor], axis=0, sort=False)

        return d

    def multi_ts_data(self):
        """ Multiprocessing wrapper for quickly reading data for multiple tickers """
        pool = multiprocessing.Pool(multiprocessing.cpu_count())
        ds = pd.concat(pool.map(self.ts_data, self.tickers), sort=False)
        pool.close()
        pool.join()

        ds.set_index('ticker', append=True, inplace=True)
        ds.sort_index(inplace=True)

        self.data = ds
