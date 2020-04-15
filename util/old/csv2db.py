#!/usr/bin/env python3
import pandas as pd
from os import listdir
from os.path import isfile, join
import sys, pyodbc
from csv import reader

if len(sys.argv) < 3:
    print('Usage: csv2db.py <csv_input_dir> <file_extension_filter>')
    sys.exit(1)

in_dir = sys.argv[1]
ext = sys.argv[2]

TABLE = '[stocks_asx].[daily]'

conn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};'
                      'SERVER=localhost;'
                      'DATABASE=stox;'
                      'UID=stox;'
                      'PWD=stox;')
cursor = conn.cursor()

files = [ '/'.join([in_dir, f]) for f in listdir(in_dir) if isfile(join(in_dir, f)) and f.endswith(ext) ]

for f in files:
    print('reading', f, '...\n')
    with open(f, 'r') as csvfile:
        rdr = reader(csvfile)
        for row in rdr:
            date = row[1]
            ticker = row[0]
            open_ = row[2]
            high = row[3]
            low = row[4]
            close = row[5]
            volume = row[6]

            if len(ticker) > 3: # 'BEAR' encountered
                continue

            query = f'INSERT INTO {TABLE}([date], [ticker], [open], [high], [low], [close], [volume])\n'
            query += 'VALUES\n'
            query += f"""({','.join([   "'" + date + "'",
                                        "'" + ticker + "'",
                                        open_,
                                        high,
                                        low,
                                        close,
                                        volume
                                    ])});\n"""
            print(query)
            cursor.execute(query)

        conn.commit()
