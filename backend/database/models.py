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
                 # Add the new IP fields here with Optional type hinting
                 source_ip_host: Optional[str] = None,
                 destination_ip_host: Optional[str] = None,
                 raw_log: Optional[str] = None,
                 **kwargs):
        super().__init__(**kwargs) # Pass any extra kwargs to BaseModel

        self.timestamp = timestamp
        self.host = host
        self.source = source
        self.level = level
        self.message = message
        self.source_ip_host = source_ip_host
        self.destination_ip_host = destination_ip_host
        self.raw_log = raw_log # Store the original raw log if available

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
            "source_ip_host": self.source_ip_host, # Include new fields
            "destination_ip_host": self.destination_ip_host, # Include new fields
            "raw_log": self.raw_log
        }
        # Filter out None values if you don't want them stored explicitly
        return {k: v for k, v in data.items() if v is not None}


class Alert(BaseModel):
    def __init__(self,
                 timestamp: datetime,
                 severity: str,
                 description: str,
                 source_ip_host: Optional[str] = None, # Make sure this is here too for Alert model
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
        self.source_ip_host = source_ip_host # Ensure it's handled here
        self.status = status
        self.assigned_to = assigned_to
        self.comments = comments if comments is not None else []
        self.rule_name = rule_name
        self.log_ids = log_ids if log_ids is not None else []

    def to_dict(self) -> Dict[str, Any]:
        """
        Converts the Alert object to a dictionary for database storage.
        """
        data = {
            "timestamp": self.timestamp,
            "severity": self.severity,
            "description": self.description,
            "source_ip_host": self.source_ip_host, # Include new fields
            "status": self.status,
            "assigned_to": self.assigned_to,
            "comments": self.comments,
            "rule_name": self.rule_name,
            "log_ids": self.log_ids
        }
        # Filter out None values, except for 'comments' and 'log_ids' if you want empty lists stored
        return {k: v for k, v in data.items() if v is not None or k in ['comments', 'log_ids']}

# You may also need to update the LogEntry and Alert creation in initialize_mock_data_api_side
# if you want to explicitly set source_ip_host for the directly created alerts.