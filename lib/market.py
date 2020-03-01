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

def all_stocks():
    tickers = pd.Series(data=pd.read_sql_query(
        "SELECT name FROM sqlite_master WHERE type='table' AND ((name LIKE '%_US') OR (name LIKE '%_AU'));",
        'sqlite:///{BASE_DIR}/../db/stox.db',
    )['name']).tolist()
    print(len(tickers), 'tickers')

    return tickers

def au_stocks():
    tickers = pd.Series(data=pd.read_sql_query(
        "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%_AU';",
        'sqlite:///{BASE_DIR}/../db/stox.db',
    )['name']).tolist()
    print(len(tickers), 'tickers')

    return tickers

def us_stocks():
    tickers = pd.Series(data=pd.read_sql_query(
        "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%_US';",
        'sqlite:///{BASE_DIR}/../db/stox.db',
    )['name']).tolist()
    print(len(tickers), 'tickers')

    return tickers
