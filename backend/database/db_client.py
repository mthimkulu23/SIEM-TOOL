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

            # TEMPORARILY COMMENT OUT THESE LINES
            # self.logs_collection.create_index("timestamp", -1)
            # self.alerts_collection.create_index("timestamp", -1)
            # self.alerts_collection.create_index("status")
            # self.alerts_collection.create_index("severity")

            # Ensure mock data is cleared/not used if real connection succeeds
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


    def _initialize_mock_database(self):
        print("Conceptual: In-memory database initialized (no actual MongoDB connection).")
        self._mock_logs_storage = []
        self._mock_alerts_storage = []

    # ... (rest of the methods remain the same, ensure the real MongoDB logic is uncommented and uses the 'if self.collection:' check)
    def insert_log(self, log_entry: LogEntry) -> str | None:
        log_dict = log_entry.to_dict()
        if self.logs_collection: # Check if real connection was made
            result = self.logs_collection.insert_one(log_dict)
            log_entry._id = str(result.inserted_id) # Update the object with the real ID
            return log_entry._id
        else: # Fallback to mock if no real connection
            mock_id = str(len(self._mock_logs_storage) + 1)
            log_dict["_id"] = mock_id
            self._mock_logs_storage.append(log_dict)
            log_entry._id = mock_id
            return mock_id

    # Make sure insert_alert, get_recent_logs, get_all_logs, get_open_alerts, update_alert_status
    # also have their real MongoDB code uncommented and wrapped in 'if self.collection:' checks.