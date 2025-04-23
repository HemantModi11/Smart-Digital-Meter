from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

# Connect to MongoDB
client = MongoClient(os.getenv("MONGO_URI"))
db = client["smart_meter_db"]

# Collections
users_collection = db["users"]
devices_collection = db["devices"]
bills_collection = db["bills"]
notifications_collection = db["notifications"]
thresholds_collection = db["thresholds"]