#!/usr/bin/env python3
import pandas as pd
import sqlalchemy as sa
from sqlalchemy import *
from sqlalchemy.engine import create_engine
from sqlalchemy.schema import *
from os import listdir
from os.path import isfile, join
import sys
from datetime import date

if len(sys.argv) < 3:
    print('Usage: csv2db.py <csv_input_dir> <file_extension_filter>')
    sys.exit(1)

in_dir = sys.argv[1]
ext = sys.argv[2]

files = [ f for f in listdir(in_dir) if isfile(join(in_dir, f)) and f.endswith(ext) ]
tickers = [ '.'.join(f.split('.')[:-1]).upper() for f in files ]
tickers = [ '^GSPC', '^AORD' ]
engine = create_engine('druid://localhost:8889/druid/v2/sql/')

for f, t in zip(files, tickers):
    print(f, 'as', t)
    try:
        df = pd.read_csv(
            (join(in_dir, f)),
            usecols=[0,1,2,3,5,6],
            parse_dates=True,
            skiprows=[0],
            names=['date', 'open', 'high', 'low', 'close', 'volume'],
        )
        df['date'] = pd.to_datetime(df['date']).dt.date
        df['ticker'] = t
        df.set_index(['date', 'ticker'], inplace=True)
    except pd.errors.EmptyDataError:
        continue

    # try:
    #     engine.execute(f'DROP TABLE {t}')

    # except (sa.exc.ProgrammingError, sa.exc.OperationalError):
    #     continue

    try:
        df.to_sql(
            'equities',
            con=engine,
            if_exists='append',
            index_label=['date', 'ticker'],
            dtype={
                'date'  : sa.types.Date,
                'ticker': sa.types.String,
                'open'  : sa.types.Numeric(precision=18, scale=8),
                'high'  : sa.types.Numeric(precision=18, scale=8),
                'low'   : sa.types.Numeric(precision=18, scale=8),
                'close' : sa.types.Numeric(precision=18, scale=8),
                'volume': sa.types.BigInteger,
            }
        )
    except sa.exc.OperationalError:
        # engine.execute(f'DROP TABLE {t}')
        # print(f'Error in {t}, table dropped!')
        print(f'Error in {t}')
        continue
