import pymongo
from telegram_bot import send_group_message
# from send_sms import send_sms

myclient = None

def connect_to_database():
    try:
        myclient = pymongo.MongoClient("mongodb://localhost:27017/")
        mydb = myclient["track_status"]
        mycol = mydb["transport_status"]
        print("Database Connection Established Successfully.")
        return mycol
    except Exception as e:
        print("Error While Connecting To Database: " + str(e))

async def insert_to_database(data, mycol):
    try:
        existing_data = mycol.find_one({"trackId": data["trackId"]})
        
        if existing_data:
            if existing_data["status"] != data["status"]:
                mycol.update_one({"trackId": data["trackId"]}, {"$set": {"status": data["status"]}})
                print(f"Status updated for trackId {data['trackId']}")
                message = f"Gönderi Durumu Güncellendi!\nSipariş ID: {data['ID']}\nMüşteri Adı: {data['customerName']}\nGönderi Durumu: {data['status']}\nTakip Kodu: {data['trackId']}\nGönderi Takip: https://gonderitakip.ptt.gov.tr/Track/Verify?q={data['trackId']}"
                await send_group_message(message)
            else:
                print(f"Data with trackId {data['trackId']} Already Exists and Status Is The Same.")
        else:
            x = mycol.insert_one(data)
            message = f"Takip Kodu Eklendi!\nSipariş ID: {data['ID']}\nMüşteri Adı: {data['customerName']}\nGönderi Durumu: {data['status']}\nTakip Kodu: {data['trackId']}\nGönderi Takip: https://gonderitakip.ptt.gov.tr/Track/Verify?q={data['trackId']}"
            await send_group_message(message)
            print("Data Inserted Successfully.")
    except Exception as e:
        print("Error While Inserting/Updating Data To Database: " + str(e))

def close_database_connection():
    global myclient
    try:
        if myclient:
            myclient.close()
            print("Database Connection Closed Successfully.")
    except Exception as e:
        print("Error While Closing Database Connection: " + str(e))

def get_all_data(mycol):
    try:
        all_data = mycol.find({}, {"_id":0})
        return all_data
    except Exception as e:
        print("Error While Fetching Data From Database: " + str(e))