# backend/database/db_client.py

from pymongo import MongoClient # UNCOMMENT THIS
from pymongo.errors import ConnectionFailure, OperationFailure # UNCOMMENT THIS
from bson.objectid import ObjectId # UNCOMMENT THIS (needed for _id operations)
from datetime import datetime

from backend.config import Config
from backend.database.models import LogEntry, Alert # Assuming these are properly defined

class SiemDatabase:
    """
    Handles all database interactions for the SIEM tool.
    Uses MongoDB (conceptual implementation using in-memory lists).
    In a real application, replace list operations with pymongo calls.
    """
    def __init__(self, config: Config):
        self.config = config
        self.client = None # Initialize to None
        self.db = None # Initialize to None
        self.logs_collection = None # Initialize to None
        self.alerts_collection = None # Initialize to None

        print(f"Attempting to connect to MongoDB client for {self.config.MONGO_URI}...")
        # --- Real MongoDB Connection (UNCOMMENT THESE LINES) ---
        try:
            # Added serverSelectionTimeoutMS for faster connection failure detection
            self.client = MongoClient(self.config.MONGO_URI, serverSelectionTimeoutMS=5000)
            # The ping command is cheap and does not require auth.
            self.client.admin.command('ping') # This actually attempts to connect
            self.db = self.client[self.config.DB_NAME]
            self.logs_collection = self.db[self.config.LOGS_COLLECTION_NAME]
            self.alerts_collection = self.db[self.config.ALERTS_COLLECTION_NAME]
            print("Successfully connected to MongoDB Atlas.") # Changed print message for clarity

            # Optional: create indexes if they don't exist (good for perf)
            self.logs_collection.create_index("timestamp", -1)
            self.alerts_collection.create_index("timestamp", -1)
            self.alerts_collection.create_index("status")
            self.alerts_collection.create_index("severity")

            # Ensure mock data is cleared/not used if real connection succeeds
            self._mock_logs_storage = []
            self._mock_alerts_storage = []

        except ConnectionFailure as e:
            print(f"ERROR: MongoDB ConnectionFailure. Ensure MongoDB is running and accessible from Render. Error: {e}")
            self._initialize_mock_database() # Fallback to mock
        except OperationFailure as e:
            print(f"ERROR: MongoDB OperationFailure (e.g., authentication/permissions). Error: {e}")
            self._initialize_mock_database() # Fallback to mock
        except Exception as e:
            print(f"ERROR: An unexpected error occurred during MongoDB connection: {type(e).__name__}: {e}")
            self._initialize_mock_database() # Fallback to mock
        # -----------------------------------------------------------------

        # If a real connection was not established, ensure mock is explicitly initialized
        # This print statement should now *only* appear if the try block fails.
        if self.client is None:
            self._initialize_mock_database()


    def _initialize_mock_database(self):
        print("Conceptual: In-memory database initialized (no actual MongoDB connection).")
        self._mock_logs_storage = [] # Reset or keep mock data
        self._mock_alerts_storage = [] # Reset or keep mock data
        # Populate with some mock data for development if needed
        # self._populate_mock_data() # Uncomment if you want to always have mock data on fallback

    # You also need to UNCOMMENT the real MongoDB insertion/retrieval/update logic
    # in the other methods (insert_log, insert_alert, get_recent_logs, etc.)
    # and adjust them to use the if self.logs_collection: / if self.alerts_collection: checks.

    # Example for insert_log:
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

    # Do similar changes for all other methods (insert_alert, get_recent_logs, get_all_logs, get_open_alerts, update_alert_status)
    # UNCOMMENT the MongoDB specific code and ensure it's wrapped in an 'if self.collection_name:' check.
    # Keep the mock fallback in the 'else' block or as the default if the 'if' condition fails.