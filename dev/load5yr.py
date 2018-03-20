# ----------------------------------
# Dependencies
# ----------------------------------
import sys
import datetime
import pandas as pd
import numpy as np

# Imports the method used for connecting to DBs
from sqlalchemy import create_engine

# Imports the methods needed to abstract classes into tables
from sqlalchemy.ext.declarative import declarative_base

# Allow us to declare column types
from sqlalchemy import Column, Integer, String, Float, DateTime

firstarg = sys.argv[1]
secondarg = sys.argv[2]

# ----------------------------------
# pull in CSV data
# ----------------------------------
file_name = "./data/5_year_dc_weather_mod.csv"
df = pd.read_csv(file_name)

# ----------------------------------
# Create Class
# ----------------------------------

# Sets an object to utilize the default declarative base in SQL Alchemy
Base = declarative_base()

# Creates Classes which will serve as the anchor points for our Tables
class MyRecord(Base):
    __tablename__ = 'fiveYear'
    id = Column(Integer, primary_key=True)
    date = Column(DateTime)
    precipitation = Column(Float)
    temp_max = Column(Float)
    temp_min = Column(Float)
    wind = Column(Float)
    weather = Column(String(255))

# Create Database Connection
# ----------------------------------
# Creates a connection to our DB using the database Connect Engine
if firstarg.lower() == 'p':
    engine = create_engine('postgresql://postgres:' + secondarg + '@localhost:5432/Project_2')
else:
    engine = create_engine('mysql://root:' + secondarg + '@localhost:3306/Project_2')

conn = engine.connect()

# Create a "Metadata" Layer That Abstracts our SQL Database
# ----------------------------------
# Create (if not already in existence) the tables associated with our classes.
Base.metadata.create_all(engine)

# Create a Session Object to Connect to DB
# ----------------------------------
# Session is a temporary binding to our DB
from sqlalchemy.orm import Session
session = Session(bind=engine)

# Add Records to the Appropriate DB
# ----------------------------------
# Use the SQL ALchemy methods to run simple "INSERT" statements using the classes and objects
for index, row in df.iterrows():
    myrecord = MyRecord(date = row[0],
                        precipitation = row[1],
                        temp_max = row[2],
                        temp_min = row[3],
                        wind = row[4],
                        weather = row[5])

    session.add(myrecord)

session.commit()

# Query the Tables
# ----------------------------------
# Perform a simple query of the database
#dog_list = session.query(Dog)
#for doggy in dog_list:
#    print(doggy.name)

#cat_list = session.query(Cat)
#for kitty in cat_list:
#    print(kitty.name)
