# backend/database/db_client.py

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure
from bson.objectid import ObjectId
from datetime import datetime

from backend.config import Config
from backend.database.models import LogEntry, Alert

class SiemDatabase:
    def __init__(self, config: Config):
        self.config = config
        self.client = None
        self.db = None
        self.logs_collection = None
        self.alerts_collection = None

        print(f"Attempting to connect to MongoDB client for {self.config.MONGO_URI}...")
        try:
            self.client = MongoClient(self.config.MONGO_URI, serverSelectionTimeoutMS=5000)
            self.client.admin.command('ping')
            self.db = self.client[self.config.DB_NAME]
            self.logs_collection = self.db[self.config.LOGS_COLLECTION_NAME]
            self.alerts_collection = self.db[self.config.ALERTS_COLLECTION_NAME]
            print("Successfully connected to MongoDB Atlas.")

            # COMMENT OUT THESE LINES AGAIN
            # self.logs_collection.create_index("timestamp", -1)
            # self.alerts_collection.create_index("timestamp", -1)
            # self.alerts_collection.create_index("status")
            # self.alerts_collection.create_index("severity")

            self._mock_logs_storage = []
            self._mock_alerts_storage = []

        except ConnectionFailure as e:
            print(f"ERROR: MongoDB ConnectionFailure. Ensure MongoDB is running and accessible from Render. Error: {e}")
            self._initialize_mock_database()
        except OperationFailure as e:
            print(f"ERROR: MongoDB OperationFailure (e.g., authentication/permissions). Error: {e}")
            self._initialize_mock_database()
        except Exception as e:
            print(f"ERROR: An unexpected error occurred during MongoDB connection: {type(e).__name__}: {e}")
            self._initialize_mock_database()

        if self.client is None:
            self._initialize_mock_database()
    # ... (rest of the class methods)