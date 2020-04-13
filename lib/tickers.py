#!/usr/bin/env python3
# Functions for supplying various lists of stock market tickers to use in filtering data

import pandas as pd
import os
from lib.db import db_connection

BASE_DIR = os.path.dirname(os.path.realpath(__file__))

def all():
    dbconn = db_connection()
    tickers =   pd.read_sql_query(
                    """
                    SELECT DISTINCT market, ticker FROM [stox].[stocks].[daily]
                    WHERE SUBSTRING(ticker,1,1) <> '^'
                    """,
                    dbconn
                )
    dbconn.close()

    return [ (mt[1][0], mt[1][1],) for mt in tickers.iterrows() ]

def by_market(market_list):
    dbconn = db_connection()
    tickers =   pd.read_sql_query(
                    f"""
                    SELECT DISTINCT market, ticker FROM [stox].[stocks].[daily]
                    WHERE market IN({','.join(market_list)}) AND SUBSTRING(ticker,1,1) <> '^'
                    """,
                    dbconn
                )
    dbconn.close()

    return [ (mt[1][0], mt[1][1],) for mt in tickers.iterrows() ]

def indices():
    dbconn = db_connection()
    tickers =   pd.read_sql_query(
                    """
                    SELECT DISTINCT market, ticker FROM [stox].[stocks].[daily]
                    WHERE SUBSTRING(ticker,1,1) = '^'
                    """,
                    dbconn
                )
    dbconn.close()

    return [ (mt[1][0], mt[1][1],) for mt in tickers.iterrows() ]