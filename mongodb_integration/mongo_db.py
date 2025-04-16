# mongodb_integration/mongo_db.py

import pymongo
from streamlit import secrets
from bson import Binary

# MongoDB connection setup
mongo_client = pymongo.MongoClient(secrets["mongo"]["uri"])  # URI from secrets
db = mongo_client["braille_db"]  # Database name
collection = db["user_data"]  # Collection name

def save_to_mongo(data):
    """Save the Braille, image, text, and audio data to MongoDB"""
    collection.insert_one(data)
    print("Data saved to MongoDB:", data)
