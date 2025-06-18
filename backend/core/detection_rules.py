from backend.database.db_client import SiemDatabase
from backend.database.models import LogEntry, Alert # Ensure Alert is imported
from backend.config import Config
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

class DetectionRules:
    def __init__(self, db_client: SiemDatabase, config: Config):
        self.db_client = db_client
        self.config = config
        self.rules = self._load_rules()

    def _load_rules(self) -> List[Dict[str, Any]]:
        """
        Loads detection rules. In a real scenario, this might load from a file,
        database, or external service. For now, hardcoded.
        """
        return [
            {
                "name": "Multiple Failed Logins",
                "condition": lambda log: log.level == "AUTH_FAILED" and log.source == "Authentication",
                "threshold_count": 3, # e.g., 3 failed logins
                "threshold_time_window_minutes": 5, # within 5 minutes
                "severity": "High",
                "description_template": "Multiple failed login attempts detected from {source_ip_host} on {host}.",
                "group_by": ["source_ip_host", "host"]
            },
            {
                "name": "Unauthorized Data Export",
                "condition": lambda log: log.level == "CRITICAL" and "unauthorized data export" in log.message.lower(),
                "severity": "Critical",
                "description_template": "Unauthorized data export attempt detected from {source_ip_host} on {host}.",
                "alert_immediately": True # This rule triggers an alert immediately
            },
            {
                "name": "Ransomware Activity Detected",
                "condition": lambda log: log.level == "CRITICAL" and "ransomware activity detected" in log.message.lower(),
                "severity": "Critical",
                "description_template": "Ransomware activity detected and blocked on {host} at {raw_log_short}.",
                "alert_immediately": True
            },
            {
                "name": "Suspicious Outbound Network Flow",
                "condition": lambda log: log.source == "Network Flow" and log.level == "ALERT" and "suspicious high volume outbound connections" in log.message.lower(),
                "severity": "High",
                "description_template": "Suspicious high volume outbound network connections detected from {source_ip_host}.",
                "alert_immediately": True
            },
            {
                "name": "Low Disk Space Alert",
                "condition": lambda log: log.source == "System Monitor" and log.level == "WARN" and "low disk space" in log.message.lower(),
                "severity": "Medium",
                "description_template": "Low disk space detected on host {host} at {raw_log_short}.",
                "alert_immediately": True
            },
            {
                "name": "SSL Certificate Nearing Expiry",
                "condition": lambda log: log.source == "Certificate Monitor" and log.level == "WARN" and "ssl certificate" in log.message.lower() and "expires in" in log.message.lower(),
                "severity": "Medium",
                "description_template": "SSL certificate {message_snippet} is nearing expiry on {host}.",
                "alert_immediately": True
            }
        ]

    def run_rules_on_log(self, log_entry: LogEntry):
        """
        Runs all configured detection rules against a single LogEntry.
        """
        print(f"Running rules on log: {log_entry.message[:50]}...") # Debug print

        for rule in self.rules:
            if rule["condition"](log_entry):
                if rule.get("alert_immediately"):
                    description = self._format_description(rule["description_template"], log_entry)
                    self._create_and_save_alert(
                        severity=rule["severity"],
                        description=description,
                        source_ip_host=log_entry.source_ip_host,
                        rule_name=rule["name"],
                        log_ids=[str(log_entry._id)] # Associate with the log that triggered it
                    )
                else:
                    # For threshold-based rules, we'd typically store the log
                    # and then have a separate process aggregate and check thresholds.
                    # For simplicity, we'll just log if a threshold rule condition is met.
                    # A full SIEM would use a stateful correlation engine here.
                    # print(f"  Rule '{rule['name']}' matched, but requires aggregation.")
                    pass

    def _format_description(self, template: str, log_entry: LogEntry) -> str:
        """Formats the alert description using log_entry attributes."""
        # Create a dictionary of available log_entry attributes for formatting
        attrs = {
            "timestamp": log_entry.timestamp.isoformat(),
            "host": log_entry.host,
            "source": log_entry.source,
            "level": log_entry.level,
            "message": log_entry.message,
            "source_ip_host": log_entry.source_ip_host if log_entry.source_ip_host else "N/A",
            "destination_ip_host": log_entry.destination_ip_host if log_entry.destination_ip_host else "N/A",
            "raw_log_short": log_entry.raw_log[:70] + "..." if log_entry.raw_log else "N/A",
            "message_snippet": log_entry.message[:50] + "..." # Useful for long messages
        }
        return template.format(**attrs)

    def _create_and_save_alert(self, severity: str, description: str, source_ip_host: Optional[str], rule_name: str, log_ids: List[str]):
        """
        Creates an Alert object and saves it to the database.
        """
        new_alert = Alert(
            timestamp=datetime.now(),
            severity=severity,
            description=description,
            status="Open",
            source_ip_host=source_ip_host,
            rule_name=rule_name,
            log_ids=log_ids # List of string ObjectIds
        )
        
        # CORRECTED LINE: Pass the Alert object directly, not its dictionary
        inserted_id = self.db_client.insert_alert(new_alert)
        if inserted_id:
            print(f"  ALERT GENERATED: Rule '{rule_name}' triggered. Severity: {severity}, ID: {inserted_id}")
            new_alert._id = inserted_id # Assign the DB-generated ID back to the object
        else:
            print(f"  WARNING: Failed to save alert for rule '{rule_name}'.")

