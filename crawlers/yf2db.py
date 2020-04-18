#!/usr/bin/env python3
import os, sys, pyodbc, argparse
import pandas as pd
import yfinance as yf
from math import isnan

parser = argparse.ArgumentParser()
parser.add_argument('-m', '--markets', default='', help='Comma-separated list of markets. Default : AU')
parser.add_argument('-v', '--verbose', default=False, help='Enable verbose mode. Default: False', action='store_true')
parser.add_argument('-i', '--fetch-info', default=False, help='Whether to fetch & insert ticker info. Default: False', action='store_true')

MARKETS = parser.parse_args().markets
VERBOSE = parser.parse_args().verbose
INFO = parser.parse_args().fetch_info

if MARKETS == '':
    print('no markets were given, exiting.')
    sys.exit()

INDICES_DIR = f'{os.path.dirname(os.path.realpath(__file__))}/../data/indices'
INDICES = [
    { 'market': 'US' , 'ticker_suffix': ''   , 'index_ticker': '^GSPC' , 'file': '/'.join([INDICES_DIR, 'SP500.csv']), 'skiprows': None },
    { 'market': 'AU' , 'ticker_suffix': '.AX', 'index_ticker': '^AORD' , 'file': '/'.join([INDICES_DIR, 'XAO_Makeup.csv']), 'skiprows': [0] },
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

def RowExists(key):
    cursor.execute(f""" SELECT COUNT(*) FROM {TABLE}
                        WHERE   date   = '{key[0]}'
                            AND market = '{key[1]}'
                            AND ticker = '{key[2]}'
                    """)
    return True if int(cursor.fetchone()[0]) == 1 else False

def getRow(key):
    cursor.execute(f""" SELECT * FROM {TABLE}
                        WHERE   date   = '{key[0]}'
                            AND market = '{key[1]}'
                            AND ticker = '{key[2]}'
                    """)
    result = cursor.fetchone()
    return [ str(result[0]).replace('-','') ] + [ str(c) for c in result[1:3] ] + [ (float(c) if c is not None else None) for c in result[3:] ]

initial_count = getCount() # initial row count before the inserts
num_inserted, num_updated, num_skipped = 0, 0, 0

for i in INDICES:
    if i['market'] not in MARKETS:
        continue

    constituents = pd.read_csv(i['file'], skiprows=i['skiprows'], header=0, usecols=[0]).iloc[:, 0].tolist()
    tickers = [ i['index_ticker'] ] + [ t + i['ticker_suffix'] for t in constituents ]
    print('Will fetch', len(tickers), 'tickers for', i['index_ticker'])

    for ticker in tickers:
        if VERBOSE:
            print('----------', 'fetching', ticker, '----------')

        yf_ticker = yf.Ticker(ticker)
        data = yf_ticker.history(period="max", auto_adjust=False).reset_index()

        for day_data in data.iterrows():
            columns = [ None if type(c) == float and isnan(c) else c for c in day_data[1].values ]

            new_values = [
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
            ]

            if RowExists(new_values[:3]):
                old_values = getRow(new_values[:3])
                if (new_values == old_values):
                    if VERBOSE:
                        print('SKIP', new_values, sep='\t')
                    num_skipped += 1
                else:
                    if VERBOSE:
                        print('UPDATE', new_values, sep='\t')
                        print('   old:', old_values)

                    query =f""" UPDATE {TABLE} SET [open] = ?, [high] = ?, [low] = ?, [close] = ?, [volume] = ?, [dividend] = ?, [split] = ?
                                WHERE   [date]   = ? AND [market] = ? AND [ticker] = ? """
                    cursor.execute(query, *new_values[3:], *new_values[:3])
                    num_updated += 1
            else:
                if VERBOSE:
                    print('INSERT', new_values, sep='\t')

                query =f""" INSERT INTO {TABLE}([date], [market], [ticker], [open], [high], [low], [close], [volume], [dividend], [split])
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?) """
                cursor.execute(query, *new_values)
                num_inserted += 1

        if INFO:
            info = yf_ticker.info
            print(info)

        conn.commit()

print('yf2db.py:', num_inserted, 'rows inserted,', num_updated, 'rows updated,', num_skipped, 'skipped.')
assert (getCount() - initial_count) == num_inserted
