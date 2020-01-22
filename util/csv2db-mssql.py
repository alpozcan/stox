#!/usr/bin/env python3
import pandas as pd
import sqlalchemy as sa
from os import listdir
from os.path import isfile, join
import sys

if len(sys.argv) < 3:
    print('Usage: csv2db.py <csv_input_dir> <file_extension_filter>')
    sys.exit(1)

in_dir = sys.argv[1]
ext = sys.argv[2]

files = [ f for f in listdir(in_dir) if isfile(join(in_dir, f)) and f.endswith(ext) ]
tickers = [ '.'.join(f.split('.')[:-2]).upper() for f in files ]

assert '_' in tickers[-1] # Make sure it has the country suffix

engine = sa.create_engine("mssql+pymssql://stox:stox@localhost:1433/stox", echo=False)

for f, t in zip(files, tickers):
    print(f, 'as', t)
    try:
        df = pd.read_csv(
            (join(in_dir, f)),
            usecols=range(6),
            parse_dates=True,
            skiprows=[0],
            names=['date', 'open', 'high', 'low', 'close', 'volume'],
        )
        df.set_index('date', inplace=True)
    except pd.errors.EmptyDataError:
        continue

    # try:
    #     engine.execute(f'DROP TABLE {t}')

    # except (sa.exc.ProgrammingError, sa.exc.OperationalError):
    #     continue

    try:
        engine.execute(f"""
            USE [stox]

            CREATE TABLE [dbo].[{t}](
                [date] [date] NOT NULL,
                [open] [decimal](9, 3) NULL,
                [high] [decimal](9, 3) NULL,
                [low] [decimal](9, 3) NULL,
                [close] [decimal](9, 3) NULL,
                [volume] [bigint] NULL,
            CONSTRAINT [PK_equities] PRIMARY KEY CLUSTERED  
            (
                [date] ASC
            )WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
            ) ON [PRIMARY]

            EXEC sp_tableoption '{t}', 'vardecimal storage format', '1'
            """
        )

        df.to_sql(
            t,
            con=engine,
            if_exists='append',
            index_label=['date'],
            dtype={
                'date'  : sa.types.Date,
                'open'  : sa.types.Numeric(precision=9, scale=3),
                'high'  : sa.types.Numeric(precision=9, scale=3),
                'low'   : sa.types.Numeric(precision=9, scale=3),
                'close' : sa.types.Numeric(precision=9, scale=3),
                'volume': sa.types.BigInteger,
            }
        )
    except sa.exc.OperationalError:
        engine.execute(f'DROP TABLE {t}')
        print(f'Error in {t}, table dropped!')
        continue
