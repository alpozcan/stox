#!/usr/bin/env python3
import os, sys, pyodbc, argparse
import pandas as pd
import yfinance as yf
from math import isnan

parser = argparse.ArgumentParser()
parser.add_argument('-m', '--markets', default='', help='Comma-separated list of markets. Default : AU')

MARKETS = parser.parse_args().markets
if MARKETS == '':
    print('no markets were given, exiting.')
    sys.exit()

# Configuration
INFO = False # Whether to fetch & insert ticker info
VERBOSE = True
# end Configuration

INDICES_DIR = f'{os.path.dirname(os.path.realpath(__file__))}/../data/indices'
INDICES = [
    { 'market': 'US' , 'ticker_suffix': ''   , 'index_ticker': '^GSPC' , 'file': '/'.join([INDICES_DIR, 'SP500.csv']) },
    { 'market': 'AU' , 'ticker_suffix': '.AX', 'index_ticker': '^AORD' , 'file': '/'.join([INDICES_DIR, 'XAO_Makeup.csv']) },
]

TABLE = '[stocks].[daily]'

conn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};'
                      'SERVER=host;'
                      'DATABASE=stox;'
                      'UID=stox;'
                      'PWD=stox;')
cursor = conn.cursor()

def getCount():
    cursor.execute(f"SELECT COUNT(*) FROM {TABLE}")
    return int(cursor.fetchone()[0])
count = getCount() # initial row count before the inserts

for i in INDICES:
    if i['market'] not in MARKETS:
        continue

    constituents = pd.read_csv(i['file'], header=0, usecols=[0]).iloc[:, 0].tolist()
    tickers = [ i['index_ticker'] ] + [ t + i['ticker_suffix'] for t in constituents ]
    print('Will fetch', len(tickers), 'tickers for', i['index_ticker'])

    for ticker in tickers:
        print('\nfetch', ticker)
        yf_ticker = yf.Ticker(ticker)
        data = yf_ticker.history(period="max", auto_adjust=False).reset_index()

        for day_data in data.iterrows():
            columns = [ None if type(c) == float and isnan(c) else c for c in day_data[1].values ]

            query = f'INSERT INTO {TABLE}([date], [market], [ticker], [open], [high], [low], [close], [volume], [dividend], [split])'
            query +=' VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'

            if VERBOSE:
                print('insert', i['market'], ticker, columns)

            cursor.execute  (   query,
                                columns[0].strftime("%Y%m%d"), # date
                                i['market'],
                                ticker,
                                columns[1], # open
                                columns[2], # high
                                columns[3], # low
                                columns[4], # close
                                # columns[5], # adj close
                                columns[6], # volume
                                columns[7], # dividends
                                columns[8] # splits
                            )

        if INFO:
            info = yf_ticker.info
            print(info)

        conn.commit()

print(getCount() - count, 'rows inserted.')
