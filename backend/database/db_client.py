# backend/database/db_client.py

from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import ConnectionFailure, OperationFailure
from backend.database.models import LogEntry, Alert, NetworkFlowEntry
from backend.config import Config
from datetime import datetime, timedelta
from bson.objectid import ObjectId
import re
from typing import Optional, List, Dict, Any

class SiemDatabase:
    def __init__(self, config: Config):
        self.config = config
        self.client = None
        self.db = None
        self._connect()

        # Initialize mock storage if real DB connection fails
        # CORRECTED: Changed 'if not self.db:' to 'if self.db is None:'
        if self.db is None:
             print("WARNING: Using mock database storage. Please ensure MongoDB is running for persistence.")
             self._mock_logs_storage = []
             self._mock_alerts_storage = []
             self._mock_network_flows_storage = [] # NEW MOCK STORAGE
             self._mock_id_counter = 1 # Unified ID counter for mock data

    def _connect(self):
        """Establishes connection to MongoDB Atlas."""
        try:
            print(f"Attempting to connect to MongoDB client...")
            self.client = MongoClient(self.config.MONGODB_URI, serverSelectionTimeoutMS=5000)
            self.client.admin.command('ping') # Test connection
            self.db = self.client[self.config.MONGODB_DB_NAME]

            # Assign collections after successful connection
            self.logs_collection = self.db[self.config.LOGS_COLLECTION_NAME]
            self.alerts_collection = self.db[self.config.ALERTS_COLLECTION_NAME]
            self.network_flows_collection = self.db["network_flows"]

            print("Successfully connected to MongoDB Atlas.")
        except ConnectionFailure as e:
            print(f"MongoDB connection failed: {e}. Falling back to mock storage.")
            self.client = None
            self.db = None
        except Exception as e:
            print(f"An unexpected error occurred during MongoDB connection: {e}. Falling back to mock storage.")
            self.client = None
            self.db = None

    def insert_log(self, log_entry: LogEntry) -> Optional[ObjectId]:
        """
        Inserts a LogEntry object into the logs collection.
        :param log_entry: An instance of LogEntry.
        :return: The ID of the inserted document (ObjectId or mock ID).
        """
        if not isinstance(log_entry, LogEntry):
            raise TypeError("Expected a LogEntry object for insertion.")

        # CORRECTED: Changed 'if self.db:' to 'if self.db is not None:'
        if self.db is not None: # Using real MongoDB
            try:
                result = self.logs_collection.insert_one(log_entry.to_dict())
                return result.inserted_id
            except OperationFailure as e:
                print(f"Failed to insert log into MongoDB: {e}")
                return None
        else: # Using mock storage
            mock_id = ObjectId() # Simulate ObjectId for consistency
            log_entry._id = mock_id # Assign mock ID to object
            self._mock_logs_storage.append(log_entry)
            return mock_id

    def insert_alert(self, alert_entry: Alert) -> Optional[ObjectId]:
        """
        Inserts an Alert object into the alerts collection.
        :param alert_entry: An instance of Alert.
        :return: The ID of the inserted document (ObjectId or mock ID).
        """
        if not isinstance(alert_entry, Alert):
            raise TypeError("Expected an Alert object for insertion.")

        # CORRECTED: Changed 'if self.db:' to 'if self.db is not None:'
        if self.db is not None: # Using real MongoDB
            try:
                result = self.alerts_collection.insert_one(alert_entry.to_dict())
                return result.inserted_id
            except OperationFailure as e:
                print(f"Failed to insert alert into MongoDB: {e}")
                return None
        else: # Using mock storage
            mock_id = ObjectId() # Simulate ObjectId for consistency
            alert_entry._id = mock_id # Assign mock ID to object
            self._mock_alerts_storage.append(alert_entry)
            return mock_id

    def insert_network_flow(self, flow_entry: NetworkFlowEntry) -> Optional[ObjectId]:
        """
        Inserts a NetworkFlowEntry object into the network_flows collection.
        :param flow_entry: An instance of NetworkFlowEntry.
        :return: The ID of the inserted document (ObjectId or mock ID).
        """
        if not isinstance(flow_entry, NetworkFlowEntry):
            raise TypeError("Expected a NetworkFlowEntry object for insertion.")

        # CORRECTED: Changed 'if self.db:' to 'if self.db is not None:'
        if self.db is not None: # Using real MongoDB
            try:
                result = self.network_flows_collection.insert_one(flow_entry.to_dict())
                return result.inserted_id
            except OperationFailure as e:
                print(f"Failed to insert network flow into MongoDB: {e}")
                return None
        else: # Using mock storage
            mock_id = ObjectId() # Simulate ObjectId for consistency
            flow_entry._id = mock_id # Assign mock ID to object
            self._mock_network_flows_storage.append(flow_entry)
            return mock_id

    def get_logs_by_criteria(self, query: Dict[str, Any], limit: int = 100) -> List[LogEntry]:
        """
        Retrieves logs matching specific criteria.
        Returns a list of LogEntry objects.
        """
        # CORRECTED: Changed 'if self.db:' to 'if self.db is not None:'
        if self.db is not None: # Using real MongoDB
            try:
                cursor = self.logs_collection.find(query).sort("timestamp", DESCENDING).limit(limit)
                return [LogEntry.from_dict(doc) for doc in cursor]
            except Exception as e:
                print(f"Error querying logs by criteria: {e}")
                return []
        else: # Using mock storage (basic filtering)
            results = []
            for log_entry in self._mock_logs_storage:
                match = True
                for key, value in query.items():
                    if key == "timestamp":
                        # For timestamp, expect {"$gte": datetime_object}
                        if "$gte" in value and log_entry.timestamp < value["$gte"]:
                            match = False
                            break
                    elif key == "message":
                        if "$regex" in value:
                            if not re.search(value["$regex"], log_entry.message, re.IGNORECASE if "$options" in value and "i" in value["$options"] else 0):
                                match = False
                                break
                    elif hasattr(log_entry, key) and getattr(log_entry, key) != value:
                        match = False
                        break
                if match:
                    results.append(log_entry)
            results.sort(key=lambda x: x.timestamp, reverse=True)
            return results[:limit]

    def get_recent_logs(self, limit: int = 20) -> List[LogEntry]:
        """Retrieves the most recent logs."""
        # CORRECTED: Changed 'if self.db:' to 'if self.db is not None:'
        if self.db is not None:
            try:
                cursor = self.logs_collection.find().sort("timestamp", DESCENDING).limit(limit)
                return [LogEntry.from_dict(doc) for doc in cursor]
            except Exception as e:
                print(f"Error getting recent logs: {e}")
                return []
        else:
            return sorted(self._mock_logs_storage, key=lambda x: x.timestamp, reverse=True)[:limit]

    def get_open_alerts(self, severity: Optional[str] = None) -> List[Alert]:
        """Retrieves open alerts, optionally filtered by severity."""
        query = {"status": "Open"}
        if severity:
            query["severity"] = severity
        
        # CORRECTED: Changed 'if self.db:' to 'if self.db is not None:'
        if self.db is not None:
            try:
                cursor = self.alerts_collection.find(query).sort("timestamp", DESCENDING)
                return [Alert.from_dict(doc) for doc in cursor]
            except Exception as e:
                print(f"Error getting open alerts: {e}")
                return []
        else:
            results = [alert for alert in self._mock_alerts_storage if alert.status == "Open"]
            if severity:
                results = [alert for alert in results if alert.severity == severity]
            return sorted(results, key=lambda x: x.timestamp, reverse=True)

    def get_all_alerts(self) -> List[Alert]:
        """Retrieves all alerts."""
        # CORRECTED: Changed 'if self.db:' to 'if self.db is not None:'
        if self.db is not None:
            try:
                cursor = self.alerts_collection.find().sort("timestamp", DESCENDING)
                return [Alert.from_dict(doc) for doc in cursor]
            except Exception as e:
                print(f"Error getting all alerts: {e}")
                return []
        else:
            return sorted(self._mock_alerts_storage, key=lambda x: x.timestamp, reverse=True)

    def get_recent_network_flows(self, limit: int = 20) -> List[NetworkFlowEntry]:
        """Retrieves recent network flow entries."""
        # CORRECTED: Changed 'if self.db:' to 'if self.db is not None:'
        if self.db is not None:
            try:
                cursor = self.network_flows_collection.find().sort("timestamp", DESCENDING).limit(limit)
                return [NetworkFlowEntry.from_dict(doc) for doc in cursor]
            except Exception as e:
                print(f"Error getting recent network flows: {e}")
                return []
        else:
            return sorted(self._mock_network_flows_storage, key=lambda x: x.timestamp, reverse=True)[:limit]

    def filter_logs(self, filter_text: str = '', source: str = 'All Sources', level: str = 'All Levels', limit: int = 100) -> List[LogEntry]:
        """Filters logs based on text, source, and level."""
        query = {}
        if filter_text:
            query["message"] = {"$regex": filter_text, "$options": "i"} # Case-insensitive regex
        if source != 'All Sources':
            query["source"] = source
        if level != 'All Levels':
            query["level"] = level
        
        return self.get_logs_by_criteria(query, limit)

    def update_alert_status(self, alert_id: str, new_status: str) -> bool:
        """Updates the status of an alert by its ID."""
        # CORRECTED: Changed 'if self.db:' to 'if self.db is not None:'
        if self.db is not None:
            try:
                # Convert string ID to ObjectId for MongoDB query
                object_alert_id = ObjectId(alert_id)
                result = self.alerts_collection.update_one(
                    {"_id": object_alert_id},
                    {"$set": {"status": new_status, "timestamp": datetime.now()}} # Update timestamp on change
                )
                return result.matched_count > 0
            except Exception as e:
                print(f"Error updating alert status: {e}")
                return False
        else: # Mock update
            for alert in self._mock_alerts_storage:
                # Compare string representation of ObjectId (from mock ID or real _id converted to str)
                if str(alert._id) == alert_id:
                    alert.status = new_status
                    alert.timestamp = datetime.now() # Update mock timestamp
                    return True
            return False

    def close(self):
        """Closes the MongoDB connection."""
        if self.client: # This check is fine for the client object
            self.client.close()
            print("MongoDB connection closed.")