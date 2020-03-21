#!/usr/bin/env python3
import pandas as pd
import sqlalchemy as sa
from os import listdir
from os.path import isfile, join
import sys
from datetime import date

if len(sys.argv) < 2:
    print('Usage: csv2db.py <file>')
    sys.exit(1)

in_file = sys.argv[1]

files = [ in_file ]
tickers = [ f.split('.')[0] for f in files ]

engine = sa.create_engine('sqlite:////home/a/code/stox/db/stox.db', echo=False)

for f, t in zip(files, tickers):
    print(f, 'as', t)
    try:
        df = pd.read_csv(
            in_file,
            usecols=[0,1,2,3,4,6],
            parse_dates=True,
            skiprows=[0],
            names=['date', 'open', 'high', 'low', 'close', 'volume'],
        )
        df['date'] = pd.to_datetime(df['date']).dt.date
        df.set_index('date', inplace=True)
    except pd.errors.EmptyDataError:
        continue

    # try:
    #     engine.execute(f'DROP TABLE {t}')

    # except (sa.exc.ProgrammingError, sa.exc.OperationalError):
    #     continue

    try:
        df.to_sql(
            t,
            con=engine,
            if_exists='replace',
            index_label=['date'],
            dtype={
                'date'  : sa.types.Date,
                'open'  : sa.types.Numeric(precision=18, scale=8),
                'high'  : sa.types.Numeric(precision=18, scale=8),
                'low'   : sa.types.Numeric(precision=18, scale=8),
                'close' : sa.types.Numeric(precision=18, scale=8),
                'volume': sa.types.BigInteger,
            }
        )
    except sa.exc.OperationalError:
        engine.execute(f'DROP TABLE {t}')
        print(f'Error in {t}, table dropped!')
        continue
