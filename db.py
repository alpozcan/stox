#!/usr/bin/env python3

from sqlalchemy import *
from sqlalchemy.engine import create_engine
from sqlalchemy.schema import *

engine = create_engine('druid://localhost:8889/druid/v2/sql/')

places = Table('places', MetaData(bind=engine), autoload=True)
