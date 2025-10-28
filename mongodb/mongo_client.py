import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

class MongoDBClient:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            mongo_url = os.getenv("MONGO_URL")
            client = MongoClient(mongo_url)
            db = client["civipulsedb"]
            cls._instance = super(MongoDBClient, cls).__new__(cls)
            cls._instance.client = client
            cls._instance.db = db
            cls._instance.complaints = db["complaints"]
        return cls._instance

mongo_client = MongoDBClient()
complaints_collection = mongo_client.complaints
