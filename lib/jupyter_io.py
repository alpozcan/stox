#!/usr/bin/env python3
# Helper functions for Jupyter notebooks

import pandas as pd
import os, glob
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.realpath(__file__)) + '/../'
DATABASE = f'sqlite:///{BASE_DIR}/db/stox.db'

def read_results(silent=False):
    result_files = glob.glob(f'{BASE_DIR}results/*.csv')
    latest_result_file = max(result_files, key=os.path.getctime)
    if not silent:
        print('results from', latest_result_file.split('/')[-1])
    return pd.read_csv( latest_result_file,
                        index_col=[0], parse_dates=['predicted_at'] )

def read_predictions():
    predictions_file = f'{BASE_DIR}/predictions/predictions_on_test.csv.xz'
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
                                DATABASE,
                                index_col=['date'], parse_dates=['date'] )
    data = data.resample('D').pad()
    return data
