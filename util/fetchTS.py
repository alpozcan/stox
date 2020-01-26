#!/usr/bin/env python3
import pandas as pd
from time import sleep
from os import path
from random import shuffle
from alpha_vantage.timeseries import TimeSeries
import sys

BASE_DIR = path.dirname(path.realpath(__file__))
SLEEP = 12
ATTEMPTS = 5

index_constituents = { }
index_constituents['AU'] = open('../data/indices/AU/XAO_Makeup.csv') # workaround LookupError: unknown encoding: mbcs
index_constituents['US'] = open('../data/indices/US/SP500.csv')

tickers = []
for c, csv in index_constituents.items():
    index_tickers = pd.read_csv(csv, usecols=[0], skiprows=[0]).iloc[:,0].tolist()
    for ticker in index_tickers:
        tickers.append({ 'ticker': ticker, 'country_suffix': c, 'symbol_suffix': ('.AX' if c == 'AU' else '') })

def get_ts(ticker, osize='compact'):
    ts = TimeSeries(output_format='pandas')
    return ts.get_daily_adjusted(ticker, outputsize=osize) # TODO: get_daily_adjusted instead

# get_daily columns:
# ['1. open', '2. high', '3. low', '4. close', '5. volume']

# get_daily_adjusted columns:
# ['1. open', '2. high', '3. low', '4. close', '5. adjusted close',
#        '6. volume', '7. dividend amount', '8. split coefficient']

# shuffle(tickers)
tickers = [{ 'ticker': '^SPX' , 'country_suffix': '', 'symbol_suffix': '' }] + tickers
tickers = [{ 'ticker': '^AORD', 'country_suffix': '', 'symbol_suffix': '' }] + tickers
n_tickers = len(tickers)

def write_csv(data, csvfile):
    if path.exists(csvfile):
        with open(csvfile, 'r') as f:
            olddata = pd.read_csv(f, index_col=0)

        newdata = data[~data.index.isin(olddata.index)]

        with open(csvfile, 'a') as f:
            newdata.to_csv(f, header=False)
        print('appended', len(newdata), 'row(s)')
    else:
        data.to_csv(csvfile)
        print('wrote', len(data), 'rows to the new file', csvfile)

# Fetch timeseries data from AlphaVantage
counter = 0
for t in tickers:
    tsdata_file = '../data/equities/' + f"{t['country_suffix']}/" + t['ticker'] + '_' + t['country_suffix'] + '.csv'
    if t['ticker'].startswith('^'):
        tsdata_file = '../data/indices/' + t['ticker'] + '.csv'
    tsdata, metadata = None, None
    fetch_size = 'compact' if path.exists(tsdata_file) else 'full'
    print('\nFetching', t['ticker'] + t['symbol_suffix'], f'({counter} of {n_tickers})', 'attempt', ': ', end = '')
    for attempt in range(ATTEMPTS):
        print((attempt + 1), end = ' ')
        try:
            tsdata, metadata = get_ts(t['ticker'] + t['symbol_suffix'], osize=fetch_size)
        except Exception as e:
            print(e)
            if attempt == ATTEMPTS:
                print('giving up.')
                break
            else:
                sleep(SLEEP)
                continue
        print('Fetched', len(tsdata), 'rows.')
        break
    if isinstance(tsdata, pd.DataFrame) and len(tsdata) > 0:
        write_csv(tsdata, tsdata_file)

    sleep(SLEEP / 2)
    counter += 1

# Cleanup TS data for companies removed from index
# file.glob data/*.csv, remove if not in [tickers]

print('done')
