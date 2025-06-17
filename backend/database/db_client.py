# backend/database/db_client.py

# from pymongo import MongoClient
# from pymongo.errors import ConnectionFailure
# from bson.objectid import ObjectId # Used to work with MongoDB's _id objects
from datetime import datetime

from backend.config import Config # ADD THIS LINE <<<<<<<<<<<<<<<<<<<<<<<<
from backend.database.models import LogEntry, Alert

class SiemDatabase:
    """
    Handles all database interactions for the SIEM tool.
    Uses MongoDB (conceptual implementation using in-memory lists).
    In a real application, replace list operations with pymongo calls.
    """
    def __init__(self, config: Config):
        self.config = config
        print(f"Conceptual: Initializing MongoDB client for {self.config.MONGO_URI}...")
        # --- Real MongoDB Connection (Uncomment and replace mock lists) ---
        # try:
        #     self.client = MongoClient(self.config.MONGO_URI)
        #     # The ping command is cheap and does not require auth.
        #     self.client.admin.command('ping')
        #     self.db = self.client[self.config.DB_NAME]
        #     self.logs_collection = self.db[self.config.LOGS_COLLECTION_NAME]
        #     self.alerts_collection = self.db[self.config.ALERTS_COLLECTION_NAME]
        #     print("Conceptual: MongoDB connection established.")
        # except ConnectionFailure as e:
        #     print(f"ERROR: Could not connect to MongoDB at {self.config.MONGO_URI}. Please ensure MongoDB is running. {e}")
        #     self.client = None
        #     self.db = None
        #     self.logs_collection = None
        #     self.alerts_collection = None
        # except Exception as e:
        #     print(f"An unexpected error occurred during MongoDB connection: {e}")
        #     self.client = None
        # -----------------------------------------------------------------

        # --- In-memory Mock Database (for conceptual simulation) ---
        self._mock_logs_storage = [] # Stores dicts, not LogEntry objects
        self._mock_alerts_storage = [] # Stores dicts, not Alert objects
        print("Conceptual: In-memory database initialized (no actual MongoDB connection).")

    def insert_log(self, log_entry: LogEntry) -> str | None:
        """
        Inserts a log entry into the logs collection.
        Returns the ID of the inserted document.
        """
        log_dict = log_entry.to_dict()
        # --- Real MongoDB Insertion ---
        # if self.logs_collection:
        #     result = self.logs_collection.insert_one(log_dict)
        #     log_entry._id = str(result.inserted_id) # Update the object with the real ID
        #     return log_entry._id
        # return None
        # --------------------------------

        # --- Mock Insertion ---
        mock_id = str(len(self._mock_logs_storage) + 1)
        log_dict["_id"] = mock_id
        self._mock_logs_storage.append(log_dict)
        log_entry._id = mock_id # Assign the mock ID to the object
        return mock_id
        # --------------------

    def insert_alert(self, alert: Alert) -> str | None:
        """
        Inserts an alert into the alerts collection.
        Returns the ID of the inserted document.
        """
        alert_dict = alert.to_dict()
        # --- Real MongoDB Insertion ---
        # if self.alerts_collection:
        #     result = self.alerts_collection.insert_one(alert_dict)
        #     alert._id = str(result.inserted_id)
        #     return alert._id
        # return None
        # --------------------------------

        # --- Mock Insertion ---
        mock_id = str(len(self._mock_alerts_storage) + 1)
        alert_dict["_id"] = mock_id
        self._mock_alerts_storage.append(alert_dict)
        alert._id = mock_id # Assign the mock ID to the object
        print(f"Conceptual: Alert inserted with ID: {mock_id}")
        return mock_id
        # --------------------

    def get_recent_logs(self, limit: int = 10) -> list[LogEntry]:
        """
        Retrieves the most recent log entries.
        """
        # --- Real MongoDB Retrieval ---
        # if self.logs_collection:
        #     cursor = self.logs_collection.find().sort("timestamp", -1).limit(limit)
        #     return [LogEntry.from_dict(doc) for doc in cursor]
        # return []
        # --------------------------------

        # --- Mock Retrieval ---
        sorted_logs = sorted(self._mock_logs_storage, key=lambda x: x.get('timestamp', datetime.min), reverse=True)
        return [LogEntry.from_dict(doc) for doc in sorted_logs[:limit]]
        # --------------------

    def get_all_logs(self) -> list[LogEntry]:
        """
        Retrieves all log entries (for explorer, potentially filtered in API layer).
        """
        # --- Real MongoDB Retrieval ---
        # if self.logs_collection:
        #     cursor = self.logs_collection.find().sort("timestamp", -1)
        #     return [LogEntry.from_dict(doc) for doc in cursor]
        # return []
        # --------------------------------

        # --- Mock Retrieval ---
        sorted_logs = sorted(self._mock_logs_storage, key=lambda x: x.get('timestamp', datetime.min), reverse=True)
        return [LogEntry.from_dict(doc) for doc in sorted_logs]
        # --------------------

    def get_open_alerts(self, severity: str = None) -> list[Alert]:
        """
        Retrieves active (Open or In Progress) alerts, optionally filtered by severity.
        """
        # --- Real MongoDB Retrieval ---
        # if self.alerts_collection:
        #     query = {"status": {"$in": ["Open", "In Progress"]}}
        #     if severity:
        #         query["severity"] = severity
        #     cursor = self.alerts_collection.find(query).sort("timestamp", -1)
        #     return [Alert.from_dict(doc) for doc in cursor]
        # return []
        # --------------------------------

        # --- Mock Retrieval ---
        filtered_alerts = [
            alert_dict for alert_dict in self._mock_alerts_storage
            if alert_dict.get('status') in ["Open", "In Progress"]
        ]
        if severity:
            filtered_alerts = [
                alert_dict for alert_dict in filtered_alerts
                if alert_dict.get('severity') == severity
            ]
        return sorted([Alert.from_dict(doc) for doc in filtered_alerts], key=lambda x: x.timestamp, reverse=True)
        # --------------------

    def update_alert_status(self, alert_id: str, new_status: str) -> bool:
        """
        Updates the status of a specific alert by its ID.
        """
        # --- Real MongoDB Update ---
        # if self.alerts_collection:
        #     try:
        #         result = self.alerts_collection.update_one(
        #             {"_id": ObjectId(alert_id)},
        #             {"$set": {"status": new_status}}
        #         )
        #         return result.modified_count > 0
        #     except Exception as e:
        #         print(f"Error updating alert {alert_id}: {e}")
        #         return False
        # return False
        # --------------------------------

        # --- Mock Update ---
        for alert_dict in self._mock_alerts_storage:
            if str(alert_dict.get("_id")) == alert_id: # Ensure string comparison for mock IDs
                alert_dict["status"] = new_status
                print(f"Conceptual: Alert {alert_id} status updated to {new_status}")
                return True
        return False
        # --------------------