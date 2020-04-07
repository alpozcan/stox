#!/usr/bin/env python3
import pandas as pd
import sqlalchemy as sa
from os import listdir
from os.path import isfile, join
import sys
from datetime import date

df = pd.read_csv(
                 '../data/equities/US/aapl_us.txt.xz',
                 usecols=range(6),
                 parse_dates=True,
                 skiprows=[0],
                 names=['date', 'open', 'high', 'low', 'close', 'volume'],
                )

df['date'] = pd.to_datetime(df['date'])
df.set_index('date', inplace=True)


df = df.resample('D').pad()
df.at[df.index.weekday > 4, 'volume'] = 0

for c in df.columns:
    if c == 'open':
        df[c] = df[c].resample('M').first()
    elif c == 'high':
        df[c] = df[c].resample('M').max()
    elif c == 'low':
        df[c] = df[c].resample('M').min()
    elif c == 'close':
        df[c] = df[c].resample('M').last()
    elif c == 'volume':
        df[c] = df[c].resample('M').sum()

df.dropna(inplace=True)
print(df)
