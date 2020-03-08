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
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.realpath(__file__)) + '/../'

def read_results(silent=False):
    result_files = glob.glob(f'{BASE_DIR}results/*.csv')
    latest_result_file = max(result_files, key=os.path.getctime)
    if not silent:
        print('results from', latest_result_file.split('/')[-1])
    return pd.read_csv( latest_result_file,
                        index_col=[0], parse_dates=['predicted_at'] )

def read_predictions():
    predictions_file = f'{BASE_DIR}/output/predictions_on_test.csv.xz'
    print('predictions:', datetime.fromtimestamp(os.path.getmtime(predictions_file)))
    return pd.read_csv( predictions_file,
                        index_col=[0, 1], parse_dates=['date'] )

def read_all_predictions():
    """ Combine the last prediction with predictions on test data """
    predictions = read_predictions() # has predictions on test data
    for ticker, result in read_results(silent=True).iterrows():
        predictions.loc[(result.predicted_at, ticker), 'prediction'] = result.prediction
        
    return predictions

def read_ticker_price_data(ticker, from_date):
    data = pd.read_sql_query(   f"""
                                SELECT `date`, `open`, `close`, ((`open`+`close`) / 2) AS `mid_price` 
                                FROM `{ticker}` 
                                WHERE date >= '{from_date}'  
                                ORDER BY date ASC
                                """,
                                f'sqlite:///{BASE_DIR}/db/stox.db',
                                index_col=['date'], parse_dates=['date'] )
    data = data.resample('D').pad()
    return data
