import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

class DatabaseConnection:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
            db_name = os.getenv("DB_NAME", "pams_db")
            client = MongoClient(uri)
            cls._instance = client[db_name]
        return cls._instance
