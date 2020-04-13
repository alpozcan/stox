#!/usr/bin/env python3
# DB wrappers

import pyodbc

def db_connection():
    return pyodbc.connect   (   'DRIVER={ODBC Driver 17 for SQL Server};'
                                'SERVER=host;'
                                'DATABASE=stox;'
                                'UID=stox;'
                                'PWD=stox;')
