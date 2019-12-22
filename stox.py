#!/usr/bin/env python3

# Stox, a prediction engine for financial time series data

# Copyright (C) 2019 Gokalp Ozcan

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
import argparse, datetime, sys
from sklearn.metrics import mean_absolute_error, explained_variance_score
from lightgbm import LGBMRegressor
import dataset
from lib import market

pd.set_option('mode.chained_assignment', None)

now = datetime.datetime.now()
day_of_week = now.strftime("%a").upper()
day_of_week = 'FRI' if (day_of_week == 'SAT' or day_of_week == 'SUN') else day_of_week
timestamp = now.strftime("%Y-%m-%d-%H-%M-%S")

parser = argparse.ArgumentParser()
parser.add_argument('--ticker', default=None, help='single ticker code, or _MOCK_EASY or _MOCK_HARD for mock tests')
parser.add_argument('--index', default='XAO', help='one of the keys of stock indices as defined in data/indices.yml, to populate the dataset with. Default: XAO')
parser.add_argument('--ratio', default=5, help='denominator of train/test split ratio. Default is 5, meaning a 80/20 percent train/test split.')
parser.add_argument('--size', default=240, help='Number of estimator trees to build. Default: 240.')
parser.add_argument('--seed', default=6, help='Seed for initialising the model weights with')
parser.add_argument('--verbose', default=1, help='Integer greater than zero. Greater this number, more info is printed during run. Default: 1.')
parser.add_argument('--lookback', default=6, help='The number of periods for look-back features. Default: 6.')
parser.add_argument('--lookfwd', default=1, help='The number of periods into the future to predict at. Default: 1.')
parser.add_argument('--resample', default=f'W-{day_of_week}', help="Period size. 'no' for daily, or any pandas-format resampling specification. Default is weekly resampling on the current workday")

INDEX = parser.parse_args().index
TEST_RATIO = 1 / int(parser.parse_args().ratio)
SIZE = int(parser.parse_args().size) # Trees
SEED = int(parser.parse_args().seed)
VERBOSE = int(parser.parse_args().verbose)
LOOKBACK = int(parser.parse_args().lookback)
LOOKFWD = int(parser.parse_args().lookfwd)
RESAMPLE = parser.parse_args().resample

ticker = parser.parse_args().ticker
tickers = [ticker] if ticker else market.index_participants(index=INDEX)

companies = market.companies() # columns: Company name,ASX code,GICS industry group
sectors = market.sectors()

ds = dataset.DataSet(tickers=tickers, lookback=LOOKBACK, lookfwd=LOOKFWD, resample=RESAMPLE).data
# ds.to_csv('debug_data.csv', index=True) # Uncomment to dump all features into a CSV file for debugging.
features = list(ds.columns)
features.remove('future') # remove the target variable from features, duh

tds, predictors = { 'X_train': [], 'X_test': [], 'y_train': [], 'y_test': [] }, None

if VERBOSE > 0:
    print(ds.info(memory_usage='deep'))
    print(ds.describe())

for t, td in ds.groupby(level=1):
    if t in tickers:
        predictor = td.xs(t, level=1).tail(1).drop(['future'], axis=1).reset_index()
        predictor['ticker'] = t
        if predictors is None:
            predictors = predictor # init the dataframe
        else:
            predictors = pd.concat([predictors, predictor], axis=0, ignore_index=True)

    td.drop(td.tail(1).index,inplace=True) # remove the predictor from the bottom of the dataframe

    date_from = pd.to_datetime(td.index.levels[0].values[0]).strftime('%Y-%m-%d')
    date_to = pd.to_datetime(td.index.levels[0].values[-1]).strftime('%Y-%m-%d')
    split_index = int(len(td) * (1 - TEST_RATIO))

    tds['X_train'].append(td.iloc[0:split_index][features])
    tds['X_test'].append(td.iloc[(split_index + LOOKFWD):][features])
    tds['y_train'].append(td.iloc[0:split_index]['future'])
    tds['y_test'].append(td.iloc[(split_index + LOOKFWD):]['future'])

    if VERBOSE > 2:
        print(t, ':', len(tds['X_train'][-1]), 'train,', len(tds['X_test'][-1]), 'test samples')

X_train = pd.concat(tds['X_train'], axis = 0)
X_test = pd.concat(tds['X_test'], axis = 0)
y_train = pd.concat(tds['y_train'], axis = 0)
y_test = pd.concat(tds['y_test'], axis = 0)

print('X_train:', X_train.shape, 'X_test:', X_test.shape, 'y_train:', y_train.shape, 'y_test:', y_test.shape)

model = LGBMRegressor(boosting_type='gbdt', class_weight=None, colsample_bytree=1.0,
                    importance_type='split', learning_rate=0.1, max_depth=-1,
                    min_child_samples=20, min_child_weight=0.001, min_split_gain=0.001,
                    n_estimators=SIZE, n_jobs=-1, num_leaves=127, objective='mae',
                    random_state=SEED, reg_alpha=0.001, reg_lambda=0.0, silent=False,
                    subsample=1.0, subsample_for_bin=200000, subsample_freq=0, verbosity=VERBOSE)

if VERBOSE > 0:
    print(model)

model.fit(X_train, y_train)

if VERBOSE > 0:
    fi = pd.DataFrame(model.feature_importances_, index=features, columns=['importance'])
    print(fi)

predicted_at = predictors['date'].max() # the latest sample is the one we'll use to predict on
predicted_for = datetime.timedelta(days=LOOKFWD) if RESAMPLE == 'no' else datetime.timedelta(days=LOOKFWD * 7)
print('Predicting from', predicted_at, 'for', predicted_at + predicted_for)
predictors = predictors[predictors['date'] == predicted_at] # drop all older samples as we want to predict only on latest data
predictors = predictors.drop('date', axis=1).set_index('ticker').sort_index()
results = pd.DataFrame()
for t, p in predictors.groupby(level=0):
    try:
        xt, yt, xT, yT = X_train.xs(t, level=1, drop_level=False), y_train.xs(t, level=1, drop_level=False), X_test.xs(t, level=1, drop_level=False), y_test.xs(t, level=1, drop_level=False)
    except KeyError:
        continue
    predictions = model.predict(xT)
    results.at[t, 'predicted_at'] = predicted_at.strftime('%b%d')
    results.at[t, 'prediction'] = model.predict(p)[0]
    results.at[t, 'volatility'] = abs(yT).mean()
    results.at[t, 'MAE'] = mean_absolute_error(yT, predictions)
    results.at[t, 'alpha'] = (results.loc[t, 'volatility'] / results.loc[t, 'MAE'] - 1) * 100
    results.at[t, 'var_score'] = explained_variance_score(yT, predictions)
    results.at[t, 'train_samples'] = xt.shape[0]
    results.at[t, 'test_samples'] = xT.shape[0]
    results.at[t, 'potential'] = results.loc[t, 'prediction'] * results.loc[t, 'var_score'] * \
                                 (results.loc[t, 'alpha'] if results.loc[t, 'alpha'] > 0 else 0)


results = results.sort_values('potential', ascending=False).round(2)
print(results, results.describe(), sep='\n')
results.to_csv(f'results/{timestamp}.csv')

# print overall results
overall_predictions = model.predict(X_test)
overall_volatility = round(abs(y_test).mean(), 4)
overall_error = round(mean_absolute_error(y_test, overall_predictions), 4)
print('Overall volatility:', overall_volatility, ', error:', overall_error, ', alpha:', round((overall_volatility / overall_error - 1) * 100, 2))
