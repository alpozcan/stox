#!/usr/bin/env python3

# Functions for supplying various lists of stock market tickers to use in filtering data

# Copyright (C) 2019 Gokalp Ozcan

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
import yaml

def index_participants(index):
    with open('data/indices.yml', 'r') as file:
        indices = yaml.load(file)
    return indices[index]

# def companies():
#     return pd.read_csv('data/companies/ASXListedCompanies.csv',skiprows=[0,1], index_col='ASX code')

# def sectors():
#     return list(companies()['GICS industry group'].unique())

def all_stocks():
    tickers = pd.Series(data=pd.read_sql_query( 'SELECT DISTINCT ticker FROM `equities`',
                                                'sqlite:///data/stox.db',
                                            )['ticker']
                        ).tolist()
    print(len(tickers), 'tickers')
    
    return tickers
