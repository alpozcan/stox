#!/usr/bin/env python3
import pandas as pd
from time import sleep
from os import path
from random import shuffle
from alpha_vantage.timeseries import TimeSeries
import sys

BASE_DIR = path.dirname(path.realpath(__file__))
KEY='IOJ838PQYYIG9JCQ'
SLEEP = 12
ATTEMPTS = 5

index_constituents = { }
index_constituents['AU'] = open('../data/indices/AU/XAO_Makeup.csv') # workaround LookupError: unknown encoding: mbcs
index_constituents['US'] = open('../data/indices/US/SP500.csv')

tickers = []
for c, csv in index_constituents.items():
    index_tickers = pd.read_csv(csv, usecols=[0], skiprows=[0]).iloc[:,0].tolist()
    for ticker in index_tickers:
        tickers.append({ 'ticker': ticker, 'country_suffix': ('_' + c), 'symbol_suffix': ('.AX' if c == 'AU' else '') })

def get_ts(ticker, osize='compact'):
    ts = TimeSeries(key=KEY, output_format='pandas')
    return ts.get_daily_adjusted(ticker, outputsize=osize)

shuffle(tickers)
tickers = [{ 'ticker': '^SPX' , 'country_suffix': '', 'symbol_suffix': '' }] + tickers
tickers = [{ 'ticker': '^AORD', 'country_suffix': '', 'symbol_suffix': '' }] + tickers
print(tickers)
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
    tsdata_file = '../data/equities/' + f"{t['country_suffix']}/" + t['ticker'] + t['country_suffix'] + '.csv'
    tsdata, metadata = None, None
    fetch_size = 'compact' if path.exists(tsdata_file) else 'full'
    print('\nFetching', t['ticker'] + t['symbol_suffix'], f'({counter} of {n_tickers})', 'attempt', ': ', end = '')
    for attempt in range(ATTEMPTS):
        print((attempt + 1), end = ' ')
        try:
            tsdata, metadata = av.get_ts(t['ticker'] + t['symbol_suffix'], osize=fetch_size)
        except:
            if attempt == ATTEMPTS:
                print('giving up.')
                break
            else:
                sleep(SLEEP)
                continue
        print('Fetched', len(tsdata), 'rows.')
        break
    if isinstance(tsdata, pd.DataFrame) and len(tsdata) > 0:
        # add the ticker column
        tsdata['ticker'] = t['ticker'] + t['country_suffix']
        cols = tsdata.columns.tolist()
        cols = cols[-1:] + cols[:-1] # make ticker the first column
        tsdata = tsdata[cols]

        print(tsadata)
        sys.exit()

        tsdata.columns = [ 'ticker', 'date', 'open', 'high', 'low', 'close', 'volume' ]
        write_csv(tsdata, tsdata_file)

    sleep(SLEEP / 2)
    counter += 1

# Cleanup TS data for companies removed from index
# file.glob data/*.csv, remove if not in [tickers]

print('done')
