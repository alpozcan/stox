#!/usr/bin/env python3
import pandas as pd
from os import listdir
from os.path import isfile, join
import sys, pyodbc
from csv import reader

if len(sys.argv) < 2:
    print('Usage: csv2db.py <csv_file>')
    sys.exit(1)

in_file = sys.argv[1]

TABLE = '[stocks_asx].[daily]'
TICKER = 'XAO'
VOLUME = '0'

conn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};'
                      'SERVER=localhost;'
                      'DATABASE=stox;'
                      'UID=stox;'
                      'PWD=stox;')
cursor = conn.cursor()

print('reading', in_file, '...\n')
with open(in_file, 'r') as csvfile:
    rdr = reader(csvfile)
    header=next(rdr)
    for row in rdr:
        if ('null' in row):
            continue

        date = row[0]
        open_ = row[1]
        high = row[2]
        low = row[3]
        close = row[4]

        query = f'INSERT INTO {TABLE}([date], [ticker], [open], [high], [low], [close], [volume])\n'
        query += 'VALUES\n'
        query += f"""({','.join([   "'" + date + "'",
                                    "'" + TICKER + "'",
                                    open_,
                                    high,
                                    low,
                                    close,
                                    VOLUME
                                ])});\n"""
        print(query)

        try:
            cursor.execute(query)
        except pyodbc.IntegrityError:
            continue
        conn.commit()
