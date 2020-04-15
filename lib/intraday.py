#!/usr/bin/env python3
# Intraday data loading and other functions

import pandas as pd
import os, re
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.realpath(__file__))
INDICES_DIR = BASE_DIR + '/../data/indices'
XAO_FILE     = INDICES_DIR + '/XAO_Makeup.csv'
INDICES_FILE = INDICES_DIR + '/Market_Indices.csv'
HEADER_REGEX = re.compile(r'Download CSV\s+(.+\s.+\s.+\s.+)\s(.+\s[AP]M)')
COLUMNS = [ 'date', 'market', 'ticker', 'open', 'high', 'low', 'close', 'volume', 'dividend', 'split' ]
INDEX_COLUMNS = [ 'date', 'market', 'ticker' ]

def parse():
    constituent_csv_data = pd.read_csv(XAO_FILE, skiprows=1)

    with open(XAO_FILE) as f:
        constituent_ts_match = HEADER_REGEX.search(f.readline()).groups()

    ticker = constituent_csv_data['Code'] + '.AX'
    open_  = constituent_csv_data['Open ($)']
    high   = constituent_csv_data['High ($)']
    low    = constituent_csv_data['Low ($)']
    close  = constituent_csv_data['Last ($)']
    volume = constituent_csv_data['Volume'].str.replace(' ', '', regex=False).str.replace(',', '', regex=False).astype('int')
    
    date = datetime.strptime(constituent_ts_match[0], '%a %d %b %Y').date()
    dates = pd.Series(len(ticker) * [date])
    time = constituent_ts_match[1]

    markets = pd.Series(len(ticker) * ['AU'])
    dividends = pd.Series(len(ticker) * [0.])
    splits = pd.Series(len(ticker) * [0.])

    xdata = pd.concat([dates, markets,   ticker,   open_,  high,   low,   close,   volume,   dividends,  splits], axis=1)
    xdata.columns = COLUMNS
    xdata.set_index(INDEX_COLUMNS, inplace=True)

    with open(INDICES_FILE) as f:
        indices_ts_match = HEADER_REGEX.search(f.readline()).groups()
    
    i_date = datetime.strptime(indices_ts_match[0], '%a %d %b %Y').date()
    assert i_date == date # sanity check to ensure the two files are from the same day

    i_csv_data = pd.read_csv(INDICES_FILE, skiprows=1, nrows=4)
    xao_row = i_csv_data[i_csv_data.Code == 'XAO']
    i_close = xao_row['Last ($)'].str.replace(' ', '', regex=False).str.replace(',', '', regex=False).astype('float64').values[0]
    i_open = i_close - xao_row['Change ($)'].values[0]
    if i_close < i_open:
        i_low = i_close
        i_high = i_open
    else:
        i_high = i_close
        i_low = i_open

    xao_sample = pd.DataFrame([[i_date, 'AU', '^AORD', i_open, i_high, i_low, i_close, 876699001.6, 0.0, 0.0]], columns=COLUMNS)
    xao_sample.set_index(INDEX_COLUMNS, inplace=True)
    xdata = pd.concat([xdata, xao_sample])

    print('Parsed intraday data from', date, time)
    return xdata
