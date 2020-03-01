#!/usr/bin/env python3

# Helper functions for Jupyter notebooks

# Copyright (C) 2017-2020 Gokalp Ozcan

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import pandas as pd
import os, glob

BASE_DIR = os.path.dirname(os.path.realpath(__file__)) + '/../'

def read_results():
    result_files = glob.glob(f'{BASE_DIR}results/*.csv')
    latest_result_file = max(result_files, key=os.path.getctime)
    print('reading results from', latest_result_file)
    return pd.read_csv( latest_result_file,
                        index_col=[0] )

def read_predictions():
    return pd.read_csv( f'{BASE_DIR}/predictions_on_test/predictions.csv.xz',
                        index_col=[0, 1], parse_dates=True )

def read_ticker_price_data(ticker, from_date):
    data = pd.read_sql_query(   f"""
                                SELECT `date`, `open`, `close` FROM `{ticker}` 
                                WHERE date >= '{from_date}'  
                                ORDER BY date ASC
                                """,
                                f'sqlite:////var/stox/stox.db',
                                index_col=['date'] )
    data.index = pd.to_datetime(data.index)
    data = data.resample('D').pad()
    return data
