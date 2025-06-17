# backend/database/models.py

from datetime import datetime
from typing import Optional, Dict, Any

# Base class for all models
class BaseModel:
    def __init__(self, **kwargs):
        # Assign all keyword arguments as attributes
        for key, value in kwargs.items():
            setattr(self, key, value)

    def to_dict(self) -> Dict[str, Any]:
        """Converts the model's attributes to a dictionary, suitable for MongoDB insertion."""
        data = self.__dict__.copy()
        # Convert datetime objects to ISO format strings for consistency if needed,
        # or rely on PyMongo's default handling for datetime objects.
        # For MongoDB, direct datetime objects are usually preferred.
        return data

class LogEntry(BaseModel):
    def __init__(self,
                 timestamp: datetime,
                 host: str,
                 source: str,
                 level: str,
                 message: str,
                 source_ip_host: Optional[str] = None,
                 destination_ip_host: Optional[str] = None,
                 raw_log: Optional[str] = None,
                 **kwargs):
        super().__init__(**kwargs)

        self.timestamp = timestamp
        self.host = host
        self.source = source
        self.level = level
        self.message = message
        self.source_ip_host = source_ip_host
        self.destination_ip_host = destination_ip_host
        self.raw_log = raw_log

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """
        Creates a LogEntry instance from a dictionary (e.g., from MongoDB).
        Handles converting MongoDB's _id to 'id' if present, and ensures timestamp is datetime.
        """
        # Remove '_id' from data if present and store it as 'id' for the object if needed
        # Or you can just pass everything and let the LogEntry constructor handle it
        log_id = data.pop('_id', None) # Remove MongoDB's _id if it exists
        
        # Ensure timestamp is a datetime object
        if isinstance(data.get('timestamp'), str):
            data['timestamp'] = datetime.fromisoformat(data['timestamp']) # Adjust format if needed

        # Create LogEntry instance
        log_entry = cls(
            timestamp=data.get('timestamp'),
            host=data.get('host'),
            source=data.get('source'),
            level=data.get('level'),
            message=data.get('message'),
            source_ip_host=data.get('source_ip_host'),
            destination_ip_host=data.get('destination_ip_host'),
            raw_log=data.get('raw_log')
        )
        # If you want to keep the MongoDB _id as 'id' on the object
        if log_id:
            log_entry.id = str(log_id) # Convert ObjectId to string for easier handling
        return log_entry


    def to_dict(self) -> Dict[str, Any]:
        """
        Converts the LogEntry object to a dictionary for database storage.
        Handles datetime objects for MongoDB compatibility.
        """
        data = {
            "timestamp": self.timestamp,
            "host": self.host,
            "source": self.source,
            "level": self.level,
            "message": self.message,
            "source_ip_host": self.source_ip_host,
            "destination_ip_host": self.destination_ip_host,
            "raw_log": self.raw_log
        }
        # Filter out None values if you don't want them stored explicitly
        return {k: v for k, v in data.items() if v is not None}


class Alert(BaseModel):
    def __init__(self,
                 timestamp: datetime,
                 severity: str,
                 description: str,
                 source_ip_host: Optional[str] = None,
                 status: str = "Open",
                 assigned_to: Optional[str] = None,
                 comments: Optional[list] = None,
                 rule_name: Optional[str] = None,
                 log_ids: Optional[list] = None, # List of _id from related logs
                 **kwargs):
        super().__init__(**kwargs)

        self.timestamp = timestamp
        self.severity = severity
        self.description = description
        self.source_ip_host = source_ip_host
        self.status = status
        self.assigned_to = assigned_to
        self.comments = comments if comments is not None else []
        self.rule_name = rule_name
        self.log_ids = log_ids if log_ids is not None else []

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """
        Creates an Alert instance from a dictionary (e.g., from MongoDB).
        """
        alert_id = data.pop('_id', None)

        if isinstance(data.get('timestamp'), str):
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])

        alert = cls(
            timestamp=data.get('timestamp'),
            severity=data.get('severity'),
            description=data.get('description'),
            source_ip_host=data.get('source_ip_host'),
            status=data.get('status', 'Open'),
            assigned_to=data.get('assigned_to'),
            comments=data.get('comments'),
            rule_name=data.get('rule_name'),
            log_ids=data.get('log_ids')
        )
        if alert_id:
            alert.id = str(alert_id)
        return alert

    def to_dict(self) -> Dict[str, Any]:
        """
        Converts the Alert object to a dictionary for database storage.
        """
        data = {
            "timestamp": self.timestamp,
            "severity": self.severity,
            "description": self.description,
            "source_ip_host": self.source_ip_host,
            "status": self.status,
            "assigned_to": self.assigned_to,
            "comments": self.comments,
            "rule_name": self.rule_name,
            "log_ids": self.log_ids
        }
        return {k: v for k, v in data.items() if v is not None or k in ['comments', 'log_ids']}