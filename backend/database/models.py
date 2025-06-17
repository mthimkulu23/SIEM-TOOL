# backend/database/models.py

from datetime import datetime

class LogEntry:
    """
    Represents a single parsed log event.
    This structure maps directly to documents in the 'logs' collection in MongoDB.
    """
    def __init__(self, timestamp: datetime, host: str, source: str, level: str, message: str, raw_log: str, ip_address: str = None, _id: str = None):
        self._id = _id # MongoDB's unique identifier (will be set after insertion)
        self.timestamp = timestamp
        self.host = host
        self.source = source      # e.g., 'Firewall', 'SSHD', 'Apache', 'Application'
        self.level = level        # e.g., 'INFO', 'WARN', 'ERROR', 'ALERT', 'CRITICAL', 'AUTH'
        self.message = message
        self.raw_log = raw_log    # The original, unparsed log string
        self.ip_address = ip_address # Extracted IP address, if any

    def to_dict(self):
        """
        Converts the LogEntry object to a dictionary suitable for MongoDB insertion.
        MongoDB handles datetime objects directly.
        """
        data = {
            "timestamp": self.timestamp,
            "host": self.host,
            "source": self.source,
            "level": self.level,
            "message": self.message,
            "raw_log": self.raw_log,
            "ip_address": self.ip_address
        }
        if self._id:
            data["_id"] = self._id
        return data

    @staticmethod
    def from_dict(data: dict):
        """
        Creates a LogEntry object from a dictionary retrieved from MongoDB.
        Assumes '_id' is present if retrieved from DB.
        """
        return LogEntry(
            _id=str(data.get("_id")), # Convert ObjectId to string
            timestamp=data["timestamp"],
            host=data["host"],
            source=data["source"],
            level=data["level"],
            message=data["message"],
            raw_log=data["raw_log"],
            ip_address=data.get("ip_address")
        )

class Alert:
    """
    Represents a security alert triggered by SIEM rules.
    This structure maps directly to documents in the 'alerts' collection in MongoDB.
    """
    def __init__(self, alert_type: str, severity: str, timestamp: datetime, description: str, source_ip_host: str, status: str = "Open", related_logs: list = None, _id: str = None):
        self._id = _id # MongoDB's unique identifier
        self.alert_type = alert_type      # e.g., 'Multiple Failed Logins', 'Unusual Traffic'
        self.severity = severity          # e.g., 'Low', 'Medium', 'High', 'Critical'
        self.timestamp = timestamp
        self.description = description
        self.source_ip_host = source_ip_host # IP address or hostname related to the alert
        self.status = status              # e.g., 'Open', 'Closed', 'Investigating'
        self.related_logs = related_logs if related_logs is not None else [] # List of MongoDB _id's of related log entries

    def to_dict(self):
        """
        Converts the Alert object to a dictionary suitable for MongoDB insertion.
        """
        data = {
            "alert_type": self.alert_type,
            "severity": self.severity,
            "timestamp": self.timestamp,
            "description": self.description,
            "source_ip_host": self.source_ip_host,
            "status": self.status,
            "related_logs": self.related_logs
        }
        if self._id:
            data["_id"] = self._id
        return data

    @staticmethod
    def from_dict(data: dict):
        """
        Creates an Alert object from a dictionary retrieved from MongoDB.
        """
        return Alert(
            _id=str(data.get("_id")), # Convert ObjectId to string
            alert_type=data["alert_type"],
            severity=data["severity"],
            timestamp=data["timestamp"],
            description=data["description"],
            source_ip_host=data["source_ip_host"],
            status=data.get("status", "Open"),
            related_logs=data.get("related_logs", [])
        )
