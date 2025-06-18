from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from bson import ObjectId # Import ObjectId for MongoDB _id handling

@dataclass
class LogEntry:
    timestamp: datetime
    host: str
    source: str
    level: str
    message: str
    source_ip_host: Optional[str] = None
    destination_ip_host: Optional[str] = None
    raw_log: Optional[str] = None
    _id: Optional[ObjectId] = None # Add _id for MongoDB compatibility

    def to_dict(self) -> Dict[str, Any]:
        """
        Converts the LogEntry object to a dictionary for database storage or JSON serialization.
        Ensures ObjectId is converted to string for JSON.
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
        # CRITICAL FIX: Convert ObjectId to string for JSON serialization
        if self._id:
            data["_id"] = str(self._id) # Convert ObjectId to its string representation
        return {k: v for k, v in data.items() if v is not None}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """
        Creates a LogEntry instance from a dictionary (e.g., from MongoDB).
        Handles converting MongoDB's _id and ensures timestamp is datetime.
        """
        _id = data.pop('_id', None)
        # If _id is a string, convert it back to ObjectId for database operations
        if isinstance(_id, str):
            try:
                _id = ObjectId(_id)
            except Exception:
                _id = None # Handle invalid ObjectId strings gracefully

        # Ensure timestamp is datetime.datetime object
        if isinstance(data.get('timestamp'), str):
            try:
                # Try fromisoformat first (preferred for ISO 8601)
                data['timestamp'] = datetime.fromisoformat(data['timestamp'])
            except ValueError:
                # Fallback for other formats if necessary, e.g., if 'Z' is just present but not part of strict ISO
                data['timestamp'] = datetime.strptime(data['timestamp'].replace('Z', ''), "%Y-%m-%dT%H:%M:%S.%f")
        elif isinstance(data.get('timestamp'), (int, float)): # Handle potential Unix timestamps
             data['timestamp'] = datetime.fromtimestamp(data['timestamp'])

        log_entry = cls(
            timestamp=data.get('timestamp'),
            host=data.get('host'),
            source=data.get('source'),
            level=data.get('level'),
            message=data.get('message'),
            source_ip_host=data.get('source_ip_host'),
            destination_ip_host=data.get('destination_ip_host'),
            raw_log=data.get('raw_log'),
            _id=_id # Pass _id directly to constructor
        )
        return log_entry


@dataclass
class Alert:
    timestamp: datetime
    severity: str
    description: str
    status: str = "Open"
    source_ip_host: Optional[str] = None
    assigned_to: Optional[str] = None
    comments: List[str] = field(default_factory=list)
    rule_name: Optional[str] = None
    log_ids: List[str] = field(default_factory=list) # List of string _id from related logs
    _id: Optional[ObjectId] = None # Add _id for MongoDB compatibility

    def to_dict(self) -> Dict[str, Any]:
        """
        Converts the Alert object to a dictionary for database storage or JSON serialization.
        Ensures ObjectId is converted to string for JSON.
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
        # CRITICAL FIX: Convert ObjectId to string for JSON serialization
        if self._id:
            data["_id"] = str(self._id) # Convert ObjectId to its string representation
        return {k: v for k, v in data.items() if v is not None or k in ['comments', 'log_ids']}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """
        Creates an Alert instance from a dictionary (e.g., from MongoDB).
        """
        _id = data.pop('_id', None)
        # If _id is a string, convert it back to ObjectId for database operations
        if isinstance(_id, str):
            try:
                _id = ObjectId(_id)
            except Exception:
                _id = None # Handle invalid ObjectId strings gracefully

        if isinstance(data.get('timestamp'), str):
            try:
                data['timestamp'] = datetime.fromisoformat(data['timestamp'])
            except ValueError:
                data['timestamp'] = datetime.strptime(data['timestamp'].replace('Z', ''), "%Y-%m-%dT%H:%M:%S.%f")
        elif isinstance(data.get('timestamp'), (int, float)):
             data['timestamp'] = datetime.fromtimestamp(data['timestamp'])

        alert = cls(
            timestamp=data.get('timestamp'),
            severity=data.get('severity'),
            description=data.get('description'),
            source_ip_host=data.get('source_ip_host'),
            status=data.get('status', 'Open'),
            assigned_to=data.get('assigned_to'),
            comments=data.get('comments', []),
            rule_name=data.get('rule_name'),
            log_ids=data.get('log_ids', []),
            _id=_id # Pass _id directly to constructor
        )
        return alert

# --- NetworkFlowEntry Model ---
@dataclass
class NetworkFlowEntry:
    timestamp: datetime
    protocol: str
    source_ip: str
    destination_ip: str
    source_port: Optional[int] = None
    destination_port: Optional[int] = None
    packet_count: int = 1
    byte_count: int = 0
    flags: List[str] = field(default_factory=list)
    flow_duration_ms: Optional[int] = None
    application_layer_protocol: Optional[str] = None
    _id: Optional[ObjectId] = None # MongoDB _id

    def to_dict(self) -> Dict[str, Any]:
        """
        Converts the NetworkFlowEntry object to a dictionary for database storage or JSON serialization.
        Ensures ObjectId is converted to string for JSON.
        """
        data = {
            "timestamp": self.timestamp,
            "protocol": self.protocol,
            "source_ip": self.source_ip,
            "destination_ip": self.destination_ip,
            "source_port": self.source_port,
            "destination_port": self.destination_port,
            "packet_count": self.packet_count,
            "byte_count": self.byte_count,
            "flags": self.flags,
            "flow_duration_ms": self.flow_duration_ms,
            "application_layer_protocol": self.application_layer_protocol
        }
        # CRITICAL FIX: Convert ObjectId to string for JSON serialization
        if self._id:
            data["_id"] = str(self._id) # Convert ObjectId to its string representation
        return {k: v for k, v in data.items() if v is not None or k in ['flags']}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """Creates a NetworkFlowEntry instance from a dictionary."""
        _id = data.pop('_id', None)
        # If _id is a string, convert it back to ObjectId for database operations
        if isinstance(_id, str):
            try:
                _id = ObjectId(_id)
            except Exception:
                _id = None # Handle invalid ObjectId strings gracefully

        if isinstance(data.get('timestamp'), str):
            try:
                data['timestamp'] = datetime.fromisoformat(data['timestamp'])
            except ValueError:
                # Handle cases where ISO format might not be strict (e.g., missing Z)
                data['timestamp'] = datetime.strptime(data['timestamp'].replace('Z', ''), "%Y-%m-%dT%H:%M:%S.%f")
        elif isinstance(data.get('timestamp'), (int, float)):
             data['timestamp'] = datetime.fromtimestamp(data['timestamp'])
        
        return cls(
            timestamp=data.get('timestamp'),
            protocol=data.get('protocol'),
            source_ip=data.get('source_ip'),
            destination_ip=data.get('destination_ip'),
            source_port=data.get('source_port'),
            destination_port=data.get('destination_port'),
            packet_count=data.get('packet_count', 1),
            byte_count=data.get('byte_count', 0),
            flags=data.get('flags', []),
            flow_duration_ms=data.get('flow_duration_ms'),
            application_layer_protocol=data.get('application_layer_protocol'),
            _id=_id # Pass _id directly to constructor
        )
