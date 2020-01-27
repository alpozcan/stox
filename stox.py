#!/usr/bin/env python3

# Stox, a prediction engine for financial time series data

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
import argparse, datetime, os, sys
from zipfile import ZipFile
from time import perf_counter
from sklearn.metrics import mean_absolute_error, explained_variance_score
from sklearn.preprocessing import MinMaxScaler
from dataset import DataSet
from regressor import Regressor
from lib import market

BASE_DIR = os.path.dirname(os.path.realpath(__file__))
pd.set_option('mode.chained_assignment', None)

if __name__ == '__main__':
    now = datetime.datetime.now()
    day_of_week = now.strftime("%a").upper()
    day_of_week = 'FRI' if day_of_week in ['SAT', 'SUN'] else day_of_week
    timestamp = now.strftime("%Y-%m-%d-%H-%M-%S")

    parser = argparse.ArgumentParser()
    parser.add_argument('--ratio', default=5, help='Denominator of train/test split ratio. Default is 5, meaning a 80/20 percent train/test split.')
    parser.add_argument('--size', default=256, help='Model size. For tree-based regressors it is the number of estimator trees to build, for neural nets it is used as a coefficient for the layer widths. Default: 256.')
    parser.add_argument('--seed', default=6, help='Seed for initialising the model weights with')
    parser.add_argument('--verbose', default=1, help='Integer greater than zero. Greater this number, more info is printed during run. Default: 1.')
    parser.add_argument('--lookback', default=6, help='The number of periods for look-back features. Default: 6.')
    parser.add_argument('--lookfwd', default=1, help='The number of periods into the future to predict at. Default: 1.')
    parser.add_argument('--resample', default=f'W-{day_of_week}', help="Period size. 'no' to turn off resampling, or any pandas-format resampling specification. Default is weekly resampling on the current workday")
    parser.add_argument('--regressor', default='LGB', help='String alias for the regressor model to use, as defined in regressor.py. Default: LGB')

    TEST_RATIO = 1 / int(parser.parse_args().ratio)
    SIZE = int(parser.parse_args().size) # Trees
    SEED = int(parser.parse_args().seed)
    VERBOSE = int(parser.parse_args().verbose)
    LOOKBACK = int(parser.parse_args().lookback)
    LOOKFWD = int(parser.parse_args().lookfwd)
    RESAMPLE = parser.parse_args().resample
    REGRESSOR = parser.parse_args().regressor

    SPLIT_DATE = '2016-01-01' # Train/test split cutoff date
    MIN_TEST_SAMPLES = 10 # minimum number of test samples required for an individual ticker to bother calculating its alpha and making predictions

    tickers = market.all_stocks() # if not MOCK else market.all_stocks() + ['_MOCK_EASY[AU]', '_MOCK_EASY[US]', '_MOCK_HARD[AU]', '_MOCK_HARD[US]']

    ds_train = DataSet(tickers=tickers, lookback=LOOKBACK, lookfwd=LOOKFWD, predicate=f"date < '{SPLIT_DATE}'", resample=RESAMPLE).data
    if VERBOSE > 0:
        print('\n--------------------------- Train dataset ---------------------------')
        print(ds_train.describe())
        print(ds_train.info(memory_usage='deep'))

    ds_test = DataSet(tickers=tickers, lookback=LOOKBACK, lookfwd=LOOKFWD, predicate=f"date >= '{SPLIT_DATE}'", resample=RESAMPLE).data
    if VERBOSE > 0:
            print('\n--------------------------- Test dataset ----------------------------')
            print(ds_test.describe())
            print(ds_test.info(memory_usage='deep'))

    features = list(ds_train.columns)
    features.remove('future') # remove the target variable from features, duh

    predictors = None
    for t, td in ds_test.groupby(level=1):
        if len(td) < MIN_TEST_SAMPLES:
            continue # too few test samples to predict confidently
        predictor = td.xs(t, level=1).tail(1).drop(['future'], axis=1).reset_index()
        predictor['ticker'] = t
        if predictors is None:
            predictors = predictor # init the dataframe
        else:
            predictors = pd.concat([predictors, predictor], axis=0, ignore_index=True)

    X_train = ds_train[features]
    y_train = ds_train['future']

    X_test = ds_test[features]
    y_test = ds_test['future']

    print   (   'X_train:', X_train.shape, 'X_test:', X_test.shape,
                'y_train:', y_train.shape, 'y_test:', y_test.shape )

    model = Regressor(kind=REGRESSOR, size=SIZE, seed=SEED, verbosity=VERBOSE).model

    time_start_tr = perf_counter()
    model.fit(X_train, y_train)
    print('Training took', round(perf_counter() - time_start_tr, 2), 'seconds')

    if VERBOSE > 0:
        fi = pd.DataFrame(model.feature_importances_, index=features, columns=['importance'])
        print(fi.sort_values('importance', ascending=False))

    predictors.set_index('ticker', inplace=True)
    predictors.sort_index(inplace=True)

    results = pd.DataFrame()
    for t, p in predictors.groupby(level=0):
        if VERBOSE > 2:
            print(p)

        predicted_at = p['date'].values[0]
        predictor = p.drop('date', axis=1)

        if p.isnull().values.any():
            if VERBOSE > 0:
                print('Not predicting', t, 'as it has NaN in its predictor')
                if VERBOSE > 2:
                    print(p)
            continue

        try:
            xT, yT = X_test.xs(t, level=1, drop_level=False), y_test.xs(t, level=1, drop_level=False)
        except KeyError:
            continue

        predictions = model.predict(xT)
        results.at[t, 'predicted_at'] = predicted_at
        results.at[t, 'prediction'] = model.predict(predictor)[0]
        results.at[t, 'volatility'] = abs(yT).mean()
        results.at[t, 'MAE'] = mean_absolute_error(yT, predictions)
        results.at[t, 'alpha'] = (results.loc[t, 'volatility'] / results.loc[t, 'MAE'] - 1) * 100
        results.at[t, 'var_score'] = explained_variance_score(yT, predictions)
        results.at[t, 'test_samples'] = xT.shape[0]
        results.at[t, 'potential'] = results.loc[t, 'prediction'] * \
                                    (results.loc[t, 'var_score'] if results.loc[t, 'var_score'] > 0 else 0) * \
                                    (results.loc[t, 'alpha'] if results.loc[t, 'alpha'] > 0 else 0)

    results = results.sort_values('potential', ascending=False).round(2)
    print(results, results.describe(), sep='\n')
    results.to_csv(f'{BASE_DIR}/results/{timestamp}.csv')

    # print overall results
    overall_predictions = model.predict(X_test)
    overall_volatility = round(abs(y_test).mean(), 4)
    overall_error = round(mean_absolute_error(y_test, overall_predictions), 4)
    print('Overall volatility:', overall_volatility, ', error:', overall_error, ', alpha:', round((overall_volatility / overall_error - 1) * 100, 2))
