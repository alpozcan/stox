#!/usr/bin/env python3
"""
    Dump datasets split into train/validate/test to be used with H2O's AutoML
"""
import argparse
import pandas as pd
from dataset import DataSet
from lib import market

pd.set_option('mode.chained_assignment', None)

parser = argparse.ArgumentParser()
parser.add_argument('--lookback', default=6, help='The number of periods for look-back features. Default: 6.')
parser.add_argument('--lookfwd', default=1, help='The number of periods into the future to predict at. Default: 1.')
parser.add_argument('--resample', default=f'M', help="Period size. 'no' to turn off resampling, or any pandas-format resampling specification. Default is M.")

LOOKBACK = int(parser.parse_args().lookback)
LOOKFWD = int(parser.parse_args().lookfwd)
RESAMPLE = parser.parse_args().resample

VALIDATE_FROM = '2010-01-01' # Train/test split cutoff date
TEST_FROM = '2015-01-01' # Train/test split cutoff date

tickers = market.all_stocks()

ds_train = DataSet(tickers=tickers, lookback=LOOKBACK, lookfwd=LOOKFWD, predicate=f"date < '{VALIDATE_FROM}'", resample=RESAMPLE).data
print('\n--------------------------- Train dataset ---------------------------')
print(ds_train.describe())
print(ds_train.info(memory_usage='deep'))
ds_train.to_csv(f'ds_dump/stox-dataset-train-{LOOKBACK}-{LOOKFWD}-{RESAMPLE}.csv.gz')
del ds_train

ds_val = DataSet(tickers=tickers, lookback=LOOKBACK, lookfwd=LOOKFWD, predicate=f"date >= '{VALIDATE_FROM}' AND date < '{TEST_FROM}'", resample=RESAMPLE).data
print('\n------------------------ Validation dataset -------------------------')
print(ds_val.describe())
print(ds_val.info(memory_usage='deep'))
ds_val.to_csv(f'ds_dump/stox-dataset-val-{LOOKBACK}-{LOOKFWD}-{RESAMPLE}.csv.gz')
del ds_val

ds_test = DataSet(tickers=tickers, lookback=LOOKBACK, lookfwd=LOOKFWD, predicate=f"date >= '{TEST_FROM}'", resample=RESAMPLE).data
print('\n--------------------------- Test dataset ----------------------------')
print(ds_test.describe())
print(ds_test.info(memory_usage='deep'))
ds_test.to_csv(f'ds_dump/stox-dataset-test-{LOOKBACK}-{LOOKFWD}-{RESAMPLE}.csv.gz')
del ds_test
