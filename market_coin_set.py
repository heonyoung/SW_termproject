import pymongo 
from pymongo import MongoClient
from datetime import datetime

cluster = MongoClient("mongodb+srv://royirene:xAndluojC4zCYCnq@heon.mwtmi5w.mongodb.net/?retryWrites=true&w=majority")
db = cluster["term_project"]
collection = db["market_coin_amount"]

collection.update_one({}, {"$set": {"market_coin": 100}})