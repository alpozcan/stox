#!/usr/bin/env python3
# DB wrappers

import pyodbc, sqlalchemy, urllib

CONN_STRING = """
DRIVER={ODBC Driver 17 for SQL Server};
SERVER=host;
DATABASE=stox;
UID=stox;
PWD=stox;
"""

def db_connection():
    return pyodbc.connect(CONN_STRING)

def db_engine():
    return sqlalchemy.create_engine(f"mssql+pyodbc:///?odbc_connect={urllib.parse.quote_plus(CONN_STRING)}", fast_executemany=True)
