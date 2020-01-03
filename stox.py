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
import argparse, datetime
from time import perf_counter
from sklearn.metrics import mean_absolute_error, explained_variance_score
from sklearn.preprocessing import MinMaxScaler
from dataset import DataSet
from regressor import Regressor
from lib import market, dump_dataset

pd.set_option('mode.chained_assignment', None)

now = datetime.datetime.now()
day_of_week = now.strftime("%a").upper()
day_of_week = 'FRI' if (day_of_week == 'SAT' or day_of_week == 'SUN') else day_of_week
timestamp = now.strftime("%Y-%m-%d-%H-%M-%S")

parser = argparse.ArgumentParser()
parser.add_argument('--ticker', default=None, help='Single ticker code, or _MOCK_EASY or _MOCK_HARD for mock tests')
parser.add_argument('--ratio', default=5, help='Denominator of train/test split ratio. Default is 5, meaning a 80/20 percent train/test split.')
parser.add_argument('--size', default=256, help='Model size. For tree-based regressors it is the number of estimator trees to build, for neural nets it is used as a coefficient for the layer widths. Default: 256.')
parser.add_argument('--seed', default=6, help='Seed for initialising the model weights with')
parser.add_argument('--verbose', default=1, help='Integer greater than zero. Greater this number, more info is printed during run. Default: 1.')
parser.add_argument('--lookback', default=9, help='The number of periods for look-back features. Default: 9.')
parser.add_argument('--lookfwd', default=1, help='The number of periods into the future to predict at. Default: 1.')
parser.add_argument('--startyear', default=1970, help='Only use samples newer than the start of the year given. Can be used for reducing the dataset size where there are memory/time constraints. Default: 1970.')
parser.add_argument('--resample', default=f'W-{day_of_week}', help="Period size. 'no' to turn off resampling, or any pandas-format resampling specification. Default is weekly resampling on the current workday")
parser.add_argument('--regressor', default='LGB', help='String alias for the regressor model to use, as defined in regressor.py. Default: LGB')
parser.add_argument('--dump', dest='dump_only', action='store_true', help='Dump the dataset to CSV and exit. Default: no dump') ; parser.set_defaults(dump_only=False)

TEST_RATIO = 1 / int(parser.parse_args().ratio)
SIZE = int(parser.parse_args().size) # Trees
SEED = int(parser.parse_args().seed)
VERBOSE = int(parser.parse_args().verbose)
LOOKBACK = int(parser.parse_args().lookback)
LOOKFWD = int(parser.parse_args().lookfwd)
START_YEAR = parser.parse_args().startyear
RESAMPLE = parser.parse_args().resample
REGRESSOR = parser.parse_args().regressor
DUMP = parser.parse_args().dump_only

VAL_SPLIT = True if (REGRESSOR in ['KTF'] or DUMP) else False

MIN_TEST_SAMPLES = 10 # minimum number of test samples required for an individual ticker to bother calculating its alpha and making predictions

ticker = parser.parse_args().ticker
tickers = [ticker] if ticker else market.all_stocks()

# companies = market.companies() # columns: Company name,ASX code,GICS industry group
# sectors = market.sectors()

ds = DataSet(tickers=tickers, lookback=LOOKBACK, lookfwd=LOOKFWD, start_year=START_YEAR, resample=RESAMPLE).data
ds = ds[ds.future != 0].dropna()

features = list(ds.columns)
features.remove('future') # remove the target variable from features, duh

tds = { 'X_train': [], 'X_val': [], 'X_test': [], 'y_train': [], 'y_val': [], 'y_test': [] }
predictors = None

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

    val_start_index = split_index + LOOKBACK
    n_val_test_samples = len(td) - (val_start_index + 1)
    val_samples = int(n_val_test_samples / 2)
    val_end_index = val_start_index + val_samples

    test_start_index = val_start_index + val_samples + LOOKBACK

    if not VAL_SPLIT:
        tds['X_train'].append(td.iloc[0:split_index][features])
        tds['y_train'].append(td.iloc[0:split_index]['future'])

        tds['X_test'].append(td.iloc[(split_index + LOOKBACK):][features])
        tds['y_test'].append(td.iloc[(split_index + LOOKBACK):]['future'])
    else:
        tds['X_train'].append(td.iloc[0:split_index][features])
        tds['y_train'].append(td.iloc[0:split_index]['future'])

        tds['X_val'].append(td.iloc[val_start_index:val_end_index][features])
        tds['y_val'].append(td.iloc[val_start_index:val_end_index]['future'])

        tds['X_test'].append(td.iloc[test_start_index:][features])
        tds['y_test'].append(td.iloc[test_start_index:]['future'])

X_train = pd.concat(tds['X_train'], axis = 0)
y_train = pd.concat(tds['y_train'], axis = 0)

X_val = pd.concat(tds['X_val'], axis = 0) if len(tds['X_val']) > 0 else pd.DataFrame()
y_val = pd.concat(tds['y_val'], axis = 0) if len(tds['y_val']) > 0 else pd.DataFrame()

X_test = pd.concat(tds['X_test'], axis = 0)
y_test = pd.concat(tds['y_test'], axis = 0)

print   (   'X_train:', X_train.shape, 'X_val:', X_val.shape, 'X_test:', X_test.shape,
            'y_train:', y_train.shape, 'y_val:', y_val.shape, 'y_test:', y_test.shape
        )

if DUMP:
    dump_dataset.dump_to_csv(X_train, y_train, X_val, y_val, X_test, y_test)

regressor = Regressor(kind=REGRESSOR, size=SIZE, seed=SEED, verbosity=VERBOSE, X_val=X_val, y_val=y_val)
model = regressor.model

if regressor.needs_feature_scaling:
    from sklearn.compose import ColumnTransformer
    from sklearn.preprocessing import PowerTransformer, MinMaxScaler, OneHotEncoder
    from sklearn.pipeline import Pipeline

    num_scaler = Pipeline([
        ('transformer', PowerTransformer(method='yeo-johnson', standardize=True)),
        ('scaler', MinMaxScaler(feature_range=(-1,1))) ])

    preprocessor = ColumnTransformer(transformers=[
        ('numerical', num_scaler, X_train.select_dtypes(include=['float64']).columns ),
        ('categorical', OneHotEncoder(), X_train.select_dtypes(include=['category']).columns ) ],
        n_jobs=-1)

    preprocessor.fit(X_train)

    n_categoricals = len(preprocessor.named_transformers_['categorical'].get_feature_names())
    regressor.input_dim = n_categoricals + len(X_train.select_dtypes(include=['float64']).columns)

    time_start = perf_counter()
    model.fit(preprocessor.transform(X_train), y_train.to_numpy())
else:
    time_start = perf_counter()
    model.fit(X_train, y_train)

print('Training took', round(perf_counter() - time_start, 2), 'seconds')

if VERBOSE > 0 and regressor.supports_feature_importance:
    fi = pd.DataFrame(model.feature_importances_, index=features, columns=['importance'])
    print(fi)

predictors = predictors.set_index('ticker').sort_index()

results = pd.DataFrame()
for t, p in predictors.groupby(level=0):
    predicted_at = p['date'].values[0]
    predictor = p.drop('date', axis=1)

    if p.isnull().values.any():
        if VERBOSE > 0:
            print('Not predicting', t, 'as it has NaN in its predictor')
            if VERBOSE > 2:
                print(p)
        continue

    try:
        xt, yt, xT, yT = X_train.xs(t, level=1, drop_level=False), y_train.xs(t, level=1, drop_level=False), X_test.xs(t, level=1, drop_level=False), y_test.xs(t, level=1, drop_level=False)

        if regressor.needs_feature_scaling:
            xt = preprocessor.transform(xt)
            xT = preprocessor.transform(xT)
    except KeyError:
        continue

    if len(xT) < MIN_TEST_SAMPLES:
        if VERBOSE > 0:
            print('Not predicting', t, f'as it has less than {MIN_TEST_SAMPLES} test samples')
        continue

    predictions = model.predict(xT)
    results.at[t, 'predicted_at'] = predicted_at
    results.at[t, 'prediction'] = model.predict(preprocessor.transform(predictor)) if regressor.needs_feature_scaling else model.predict(predictor)[0]
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
overall_predictions = model.predict(preprocessor.transform(X_test)) if regressor.needs_feature_scaling else model.predict(X_test)
overall_volatility = round(abs(y_test).mean(), 4)
overall_error = round(mean_absolute_error(y_test, overall_predictions), 4)
print('Overall volatility:', overall_volatility, ', error:', overall_error, ', alpha:', round((overall_volatility / overall_error - 1) * 100, 2))
