from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure
from backend.database.models import LogEntry, Alert
from backend.config import Config
from datetime import datetime, timedelta
from bson.objectid import ObjectId # Import ObjectId for querying by ID

class SiemDatabase:
    def __init__(self, config: Config):
        self.config = config
        self.client = None
        self.db = None
        self._connect()

    def _connect(self):
        """Establishes connection to MongoDB Atlas."""
        try:
            print(f"Attempting to connect to MongoDB client for {self.config.MONGODB_URI.split('@')[-1]}...")
            self.client = MongoClient(self.config.MONGODB_URI, serverSelectionTimeoutMS=5000)
            self.client.admin.command('ping') # Test connection
            self.db = self.client[self.config.MONGODB_DB_NAME]
            print("Successfully connected to MongoDB Atlas.")
        except ConnectionFailure as e:
            print(f"MongoDB connection failed: {e}")
            self.client = None
            self.db = None
        except Exception as e:
            print(f"An unexpected error occurred during MongoDB connection: {e}")
            self.client = None
            self.db = None

    def insert_log(self, log_entry: LogEntry):
        """
        Inserts a LogEntry object into the logs collection.
        :param log_entry: An instance of LogEntry.
        :return: The ID of the inserted document.
        """
        # --- THIS IS THE CRUCIAL CHANGE ---
        # The method now directly accepts a LogEntry object.
        # It converts the LogEntry object to a dictionary using .to_dict() before inserting.
        if not isinstance(log_entry, LogEntry):
            raise TypeError("Expected a LogEntry object for insertion.")
        try:
            result = self.db.logs.insert_one(log_entry.to_dict())
            return result.inserted_id
        except OperationFailure as e:
            print(f"Failed to insert log: {e}")
            return None

    def get_recent_logs(self, limit: int = 100):
        """
        Retrieves the most recent log entries.
        :param limit: Maximum number of logs to retrieve.
        :return: A list of LogEntry objects.
        """
        try:
            cursor = self.db.logs.find().sort("timestamp", -1).limit(limit)
            return [LogEntry(**doc) for doc in cursor] # Convert dict to LogEntry object
        except OperationFailure as e:
            print(f"Failed to retrieve recent logs: {e}")
            return []

    def filter_logs(self, filter_text: str = None, source: str = None, level: str = None, start_time: datetime = None, end_time: datetime = None):
        """
        Filters logs based on text, source, level, and time range.
        :param filter_text: Text to search in message, host, or source.
        :param source: Filter by log source.
        :param level: Filter by log level.
        :param start_time: Start of the time range.
        :param end_time: End of the time range.
        :return: A list of LogEntry objects.
        """
        query = {}
        if filter_text:
            # Case-insensitive search across multiple fields
            query['$or'] = [
                {"message": {"$regex": filter_text, "$options": "i"}},
                {"host": {"$regex": filter_text, "$options": "i"}},
                {"source": {"$regex": filter_text, "$options": "i"}}
            ]
        if source and source != "All Sources":
            query["source"] = source
        if level and level != "All Levels":
            query["level"] = level

        time_query = {}
        if start_time:
            time_query["$gte"] = start_time
        if end_time:
            time_query["$lte"] = end_time
        if time_query:
            query["timestamp"] = time_query

        try:
            cursor = self.db.logs.find(query).sort("timestamp", -1)
            return [LogEntry(**doc) for doc in cursor]
        except OperationFailure as e:
            print(f"Failed to filter logs: {e}")
            return []

    def insert_alert(self, alert: Alert):
        """
        Inserts an Alert object into the alerts collection.
        :param alert: An instance of Alert.
        :return: The ID of the inserted document.
        """
        # --- THIS IS ALSO A CRUCIAL CHANGE ---
        # The method now directly accepts an Alert object.
        # It converts the Alert object to a dictionary using .to_dict() before inserting.
        if not isinstance(alert, Alert):
            raise TypeError("Expected an Alert object for insertion.")
        try:
            result = self.db.alerts.insert_one(alert.to_dict())
            return result.inserted_id
        except OperationFailure as e:
            print(f"Failed to insert alert: {e}")
            return None

    def get_open_alerts(self, severity: str = None):
        """
        Retrieves open alerts, optionally filtered by severity.
        :param severity: Optional severity level to filter by.
        :return: A list of Alert objects.
        """
        query = {"status": "Open"}
        if severity:
            query["severity"] = severity
        try:
            cursor = self.db.alerts.find(query).sort("timestamp", -1)
            return [Alert(**doc) for doc in cursor]
        except OperationFailure as e:
            print(f"Failed to retrieve open alerts: {e}")
            return []

    def update_alert_status(self, alert_id: str, new_status: str):
        """
        Updates the status of a specific alert by its ID.
        :param alert_id: The string ID of the alert.
        :param new_status: The new status to set (e.g., "Closed", "Acknowledged").
        :return: True if updated, False otherwise.
        """
        try:
            # MongoDB stores _id as ObjectId
            obj_id = ObjectId(alert_id)
            result = self.db.alerts.update_one(
                {"_id": obj_id},
                {"$set": {"status": new_status, "last_updated": datetime.now()}}
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"Failed to update alert status for ID {alert_id}: {e}")
            return False

    def get_all_alerts(self):
        """
        Retrieves all alerts, regardless of status.
        :return: A list of Alert objects.
        """
        try:
            cursor = self.db.alerts.find().sort("timestamp", -1)
            return [Alert(**doc) for doc in cursor]
        except OperationFailure as e:
            print(f"Failed to retrieve all alerts: {e}")
            return []

    def get_logs_within_time_range(self, start_time: datetime, end_time: datetime):
        """
        Retrieves logs within a specific time range.
        :param start_time: The start of the time range (datetime object).
        :param end_time: The end of the time range (datetime object).
        :return: A list of LogEntry objects.
        """
        query = {
            "timestamp": {
                "$gte": start_time,
                "$lte": end_time
            }
        }
        try:
            cursor = self.db.logs.find(query).sort("timestamp", 1)
            return [LogEntry(**doc) for doc in cursor]
        except OperationFailure as e:
            print(f"Failed to retrieve logs in time range: {e}")
            return []

    def get_alerts_within_time_range(self, start_time: datetime, end_time: datetime):
        """
        Retrieves alerts within a specific time range.
        :param start_time: The start of the time range (datetime object).
        :param end_time: The end of the time range (datetime object).
        :return: A list of Alert objects.
        """
        query = {
            "timestamp": {
                "$gte": start_time,
                "$lte": end_time
            }
        }
        try:
            cursor = self.db.alerts.find(query).sort("timestamp", 1)
            return [Alert(**doc) for doc in cursor]
        except OperationFailure as e:
            print(f"Failed to retrieve alerts in time range: {e}")
            return []

    def close(self):
        """Closes the MongoDB connection."""
        if self.client:
            self.client.close()
            print("MongoDB connection closed.")