import pymongo 
from pymongo import MongoClient
from datetime import datetime

cluster = MongoClient("mongodb+srv://royirene:xAndluojC4zCYCnq@heon.mwtmi5w.mongodb.net/?retryWrites=true&w=majority")
db = cluster["term_project"]
collection = db["trade_his"]
logged_in = db["logged_in"]
user = db["info"]
#logged_in.update_one({},{"$set": {"logged_in":0}})
#pos = {"market_coin" : 100,"market_price" : 100}
#collection.insert_one(pos)
logged_in.update_one({"logged_in":1},{"$set":{"logged_in" : 0}})
#result = collection.find()
#for i in result:
#    print(i["logged_in"])
#now = datetime.now()
#current_time_year = now.year
#current_time_month = now.month
#current_time_day = now.day
#current_time_hour = now.hour
#current_time_minute = now.minute
#current_time_second = now.second

#pos = {"buy" : "박현도", "cell" : "정헌영","amount_coin": 10, "ppc" : 100, "year" : current_time_year, "month" : current_time_month, "day" : current_time_day, "hour" : current_time_hour, "minute" : current_time_minute, "second" : current_time_second}
#collection.insert_one(pos)

#post = {"_id_":0, "id":"WoongSup", "pw": "92"}

#result = collection.find({"name": name2 })
#for i in result:   print(i)


#collection.insert_one(post)
#db.info.update_one({"_id_" : 0},
#{
#    $set: {"_id_": 1}})
#collection.update_one({id:"Woongsup"}, {$set : {pw : "kingisback"}})

#collection.update_one({"id": "kingisback"}, {"$set": {"pw": "kingisback"}})

#result = collection.find({"id" : "WoongSup"})
#for tmp in result:
    #print(tmp)
    
