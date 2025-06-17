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

            # Ensure these index creations remain commented out as per previous solution
            # They should be created manually in MongoDB Atlas for now.
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

        # This check is correct as it determines if the client was successfully initialized
        if self.client is None:
            self._initialize_mock_database()

    def _initialize_mock_database(self):
        print("Conceptual: In-memory database initialized (no actual MongoDB connection).")
        # You might want to populate some dummy data here for testing the mock DB
        # if not self._mock_logs_storage: # Add some mock data if not already populated
        #     self._mock_logs_storage.append(LogEntry(
        #         timestamp=datetime.now(),
        #         source="System",
        #         level="INFO",
        #         message="Mock log entry 1 for testing."
        #     ).to_dict())
        # if not self._mock_alerts_storage:
        #     self._mock_alerts_storage.append(Alert(
        #         timestamp=datetime.now(),
        #         severity="High",
        #         description="Mock Alert: Unusual login activity.",
        #         source_ip_host="192.168.1.100",
        #         status="Open"
        #     ).to_dict())

    def insert_log(self, log_data: dict) -> str:
        """Inserts a new log entry into the database."""
        # CHANGED: Use 'is not None' for collection checks
        if self.logs_collection is not None:
            log_entry = LogEntry(**log_data)
            result = self.logs_collection.insert_one(log_entry.to_dict())
            return str(result.inserted_id)
        else:
            # For mock DB, assign a dummy ID
            new_id = str(ObjectId())
            log_data['_id'] = new_id
            self._mock_logs_storage.append(log_data)
            return new_id

    def get_recent_logs(self, limit: int = 100) -> list[LogEntry]:
        """Fetches the most recent log entries."""
        # CHANGED: Use 'is not None' for collection checks
        if self.logs_collection is not None:
            logs_data = list(self.logs_collection.find().sort("timestamp", -1).limit(limit))
            return [LogEntry.from_dict(log) for log in logs_data]
        else:
            return [LogEntry.from_dict(log) for log in self._mock_logs_storage[:limit]]

    def filter_logs(self, filter_text: str = None, source: str = None, level: str = None) -> list[LogEntry]:
        """Filters log entries based on criteria."""
        query = {}
        if filter_text:
            query["$or"] = [
                {"message": {"$regex": filter_text, "$options": "i"}},
                {"source": {"$regex": filter_text, "$options": "i"}},
                {"level": {"$regex": filter_text, "$options": "i"}}
            ]
        if source and source != "All Sources":
            query["source"] = source
        if level and level != "All Levels":
            query["level"] = level

        # CHANGED: Use 'is not None' for collection checks
        if self.logs_collection is not None:
            logs_data = list(self.logs_collection.find(query).sort("timestamp", -1).limit(1000)) # Adjust limit as needed
            return [LogEntry.from_dict(log) for log in logs_data]
        else:
            # Mock filtering logic
            filtered_mock_logs = [
                log for log in self._mock_logs_storage
                if (not filter_text or filter_text.lower() in log.get('message', '').lower() or \
                                      filter_text.lower() in log.get('source', '').lower() or \
                                      filter_text.lower() in log.get('level', '').lower()) and \
                   (not source or source == "All Sources" or log.get('source') == source) and \
                   (not level or level == "All Levels" or log.get('level') == level)
            ]
            return [LogEntry.from_dict(log) for log in filtered_mock_logs]

    def insert_alert(self, alert_data: dict) -> str:
        """Inserts a new alert entry into the database."""
        # CHANGED: Use 'is not None' for collection checks
        if self.alerts_collection is not None:
            alert_entry = Alert(**alert_data)
            result = self.alerts_collection.insert_one(alert_entry.to_dict())
            return str(result.inserted_id)
        else:
            new_id = str(ObjectId())
            alert_data['_id'] = new_id
            self._mock_alerts_storage.append(alert_data)
            return new_id

    def get_open_alerts(self, severity: str = None) -> list[Alert]:
        """Fetches alerts that are currently open."""
        query = {"status": {"$ne": "Closed"}} # 'status' not equal to 'Closed'
        if severity:
            query["severity"] = severity

        # CHANGED: Use 'is not None' for collection checks
        if self.alerts_collection is not None:
            alerts_data = list(self.alerts_collection.find(query).sort("timestamp", -1))
            return [Alert.from_dict(alert) for alert in alerts_data]
        else:
            filtered_mock_alerts = [
                alert for alert in self._mock_alerts_storage
                if alert.get('status') != 'Closed' and (not severity or alert.get('severity') == severity)
            ]
            return [Alert.from_dict(alert) for alert in filtered_mock_alerts]

    def update_alert_status(self, alert_id: str, new_status: str) -> bool:
        """Updates the status of a specific alert."""
        # CHANGED: Use 'is not None' for collection checks
        if self.alerts_collection is not None:
            try:
                result = self.alerts_collection.update_one(
                    {"_id": ObjectId(alert_id)},
                    {"$set": {"status": new_status, "updated_at": datetime.now()}}
                )
                return result.modified_count > 0
            except Exception as e:
                print(f"Error updating alert status: {e}")
                return False
        else:
            for i, alert in enumerate(self._mock_alerts_storage):
                if str(alert.get('_id')) == alert_id:
                    self._mock_alerts_storage[i]['status'] = new_status
                    self._mock_alerts_storage[i]['updated_at'] = datetime.now()
                    return True
            return False

    def get_alert_by_id(self, alert_id: str) -> Alert | None:
        """Fetches a single alert by its ID."""
        # CHANGED: Use 'is not None' for collection checks
        if self.alerts_collection is not None:
            alert_data = self.alerts_collection.find_one({"_id": ObjectId(alert_id)})
            return Alert.from_dict(alert_data) if alert_data else None
        else:
            for alert in self._mock_alerts_storage:
                if str(alert.get('_id')) == alert_id:
                    return Alert.from_dict(alert)
            return None

    def get_critical_alerts_count(self) -> int:
        # CHANGED: Use 'is not None' for collection checks
        if self.alerts_collection is not None:
            return self.alerts_collection.count_documents({"severity": "Critical", "status": {"$ne": "Closed"}})
        else:
            return sum(1 for alert in self._mock_alerts_storage if alert.get('severity') == 'Critical' and alert.get('status') != 'Closed')

    def get_unassigned_alerts_count(self) -> int:
        # CHANGED: Use 'is not None' for collection checks
        if self.alerts_collection is not None:
            return self.alerts_collection.count_documents({"status": "Open"})
        else:
            return sum(1 for alert in self._mock_alerts_storage if alert.get('status') == 'Open')

    # Placeholder for a more comprehensive dashboard metrics function if needed
    # You might calculate EPS and top sources within api.py or add more specific
    # methods here for database queries.
    def get_total_logs_count(self) -> int:
        # CHANGED: Use 'is not None' for collection checks
        if self.logs_collection is not None:
            return self.logs_collection.count_documents({})
        else:
            return len(self._mock_logs_storage)

    def get_alert_trend_data(self, days: int = 7) -> list[int]:
        """Generates alert trend data for the last 'days'."""
        # CHANGED: Use 'is not None' for collection checks
        if self.alerts_collection is not None:
            # This would be a more complex aggregation query in a real scenario
            # For simplicity, returning mock data or basic count for now.
            # You'd group by day and count alerts for each day.
            # Example:
            # pipeline = [
            #     {"$match": {"timestamp": {"$gte": datetime.now() - timedelta(days=days)}}},
            #     {"$group": {"_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$timestamp"}}, "count": {"$sum": 1}}},
            #     {"$sort": {"_id": 1}}
            # ]
            # results = list(self.alerts_collection.aggregate(pipeline))
            # Process results to fill 0 for days without alerts.
            return [0] * days # Placeholder
        else:
            return [0] * days # Mock data for now