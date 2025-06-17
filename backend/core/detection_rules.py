# backend/core/detection_rules.py

from backend.database.models import LogEntry, Alert # Assuming these are defined here
from backend.database.db_client import SiemDatabase # To interact with the database
from backend.config import Config
from datetime import datetime, timedelta
import re

class DetectionRules:
    def __init__(self, db_client: SiemDatabase, config: Config):
        self.db_client = db_client
        self.config = config
        print("DetectionRules engine initialized.")

    def run_rules_on_log(self, log_entry: LogEntry):
        """
        Runs various detection rules on a single LogEntry.
        If a rule is triggered, an alert is created and saved.
        """
        print(f"Running rules on log: {log_entry.message[:50]}...") # Debug print

        # Rule 1: Multiple Failed Login Attempts (Brute Force)
        if log_entry.level == "AUTH" and "Failed password" in log_entry.message and log_entry.source_ip_host:
            # Check for 3 failed attempts from the same source_ip_host within a short time (e.g., 60 seconds)
            time_window = timedelta(seconds=60)
            threshold = 3

            # Get recent failed login attempts from this source IP
            recent_failed_logins = self.db_client.get_logs_by_criteria(
                query={
                    "source_ip_host": log_entry.source_ip_host,
                    "level": "AUTH",
                    "message": {"$regex": "Failed password"},
                    "timestamp": {"$gte": datetime.now() - time_window}
                },
                limit=threshold
            )

            if len(recent_failed_logins) >= threshold:
                alert_description = f"Brute Force Attempt: Multiple ({len(recent_failed_logins)}) failed login attempts from {log_entry.source_ip_host}."
                self._create_and_save_alert(
                    severity="Critical",
                    description=alert_description,
                    source_ip_host=log_entry.source_ip_host,
                    rule_name="Brute Force Detection",
                    log_ids=[log.get('_id') for log in recent_failed_logins if log.get('_id')]
                )
                print(f"Alert triggered: {alert_description}")


        # Rule 2: Unauthorized Data Export Attempt (Critical Event)
        if log_entry.level == "CRITICAL" and "Unauthorized data export attempt detected" in log_entry.message:
            alert_description = f"Critical Alert: Unauthorized data export attempt from {log_entry.source_ip_host if log_entry.source_ip_host else 'unknown'}."
            self._create_and_save_alert(
                severity="Critical",
                description=alert_description,
                source_ip_host=log_entry.source_ip_host,
                rule_name="Unauthorized Data Export"
            )
            print(f"Alert triggered: {alert_description}")

        # Rule 3: Ransomware Activity Detected
        if log_entry.level == "ALERT" and "Ransomware activity detected" in log_entry.message:
            alert_description = f"Critical Alert: Ransomware activity detected on {log_entry.host}."
            self._create_and_save_alert(
                severity="Critical",
                description=alert_description,
                source_ip_host=log_entry.host,
                rule_name="Ransomware Detection"
            )
            print(f"Alert triggered: {alert_description}")

        # Rule 4: Suspicious High Volume Outbound Connections
        if log_entry.level == "ALERT" and "Suspicious high volume outbound connections" in log_entry.message:
            alert_description = f"High Alert: Suspicious high volume outbound connections from {log_entry.host}."
            self._create_and_save_alert(
                severity="High",
                description=alert_description,
                source_ip_host=log_entry.host,
                rule_name="Suspicious Outbound Traffic"
            )
            print(f"Alert triggered: {alert_description}")

        # Rule 5: Low Disk Space Warning (Example of a less critical alert)
        if log_entry.level == "WARN" and "Low disk space" in log_entry.message:
            alert_description = f"Warning: Low disk space detected on {log_entry.host}."
            self._create_and_save_alert(
                severity="Low",
                description=alert_description,
                source_ip_host=log_entry.host,
                rule_name="Low Disk Space Warning"
            )
            print(f"Alert triggered: {alert_description}")


    def _create_and_save_alert(self, severity: str, description: str, source_ip_host: Optional[str] = None, rule_name: Optional[str] = None, log_ids: Optional[list] = None):
        """Helper method to create and save an alert."""
        alert = Alert(
            timestamp=datetime.now(),
            severity=severity,
            description=description,
            source_ip_host=source_ip_host,
            status="Open",
            rule_name=rule_name,
            log_ids=log_ids
        )
        self.db_client.insert_alert(alert.to_dict())