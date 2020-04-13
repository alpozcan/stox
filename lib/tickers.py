#!/usr/bin/env python3

# Functions for supplying various lists of stock market tickers to use in filtering data

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