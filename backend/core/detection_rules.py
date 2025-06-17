# backend/core/detection_rules.py

from datetime import datetime, timedelta
from collections import defaultdict
import re  # ADD THIS LINE

from backend.config import Config
from backend.database.db_client import SiemDatabase
from backend.database.models import LogEntry, Alert

class DetectionRules:
    # ... (rest of the file content)
    """
    Manages and executes various security anomaly detection rules.
    It interacts with the database to store generated alerts.
    """
    def __init__(self, db_client: SiemDatabase, config: Config):
        self.db = db_client
        self.config = config
        # Dictionary to track failed login attempts for the burst detection rule.
        # Key: "IP-Username", Value: list of (timestamp, log_id) tuples
        self.failed_login_attempts = defaultdict(list)

    def run_all_rules(self, log_entry: LogEntry):
        """
        Executes all configured detection rules against a newly processed log entry.
        """
        if not log_entry._id:
            print(f"WARNING: LogEntry {log_entry.message} does not have an ID. Rules might not link correctly.")
            # In a real system, you might raise an error or ensure _id is always set

        # Example rule: Multiple Failed Logins
        self._detect_failed_login_burst(log_entry)

        # Add calls to other detection rules here as they are implemented:
        # self._detect_unusual_data_transfer(log_entry)
        # self._detect_port_scan(log_entry)
        # self._detect_brute_force_ssh(log_entry)
        # self._detect_admin_privilege_escalation(log_entry)

    def _detect_failed_login_burst(self, log_entry: LogEntry):
        """
        Rule: Detects a burst of failed login attempts from a single source IP/user
        within a defined time window.
        Triggers a 'High' severity alert if the threshold is exceeded.
        """
        # Condition 1: Check if the log message indicates a failed password attempt
        # Condition 2: Ensure an IP address is available for tracking
        if "Failed password" in log_entry.message and log_entry.ip_address:
            # Extract username from the message if available, otherwise use 'unknown_user'
            user_match = re.search(r"for user (\S+)", log_entry.message)
            username = user_match.group(1) if user_match else "unknown_user"
            key = f"{log_entry.ip_address}-{username}" # Unique key to track attempts

            # Record the current failed attempt's timestamp and its database ID
            self.failed_login_attempts[key].append((log_entry.timestamp, log_entry._id))

            # Define the start of the time window for considering failed attempts
            time_window_start = datetime.now() - timedelta(seconds=self.config.FAILED_LOGIN_TIME_WINDOW_SECONDS)

            # Filter out attempts that are outside the defined time window
            # This keeps the list relevant to recent attempts only.
            self.failed_login_attempts[key] = [
                (ts, lid) for ts, lid in self.failed_login_attempts[key] if ts > time_window_start
            ]

            # Check if the number of valid attempts exceeds the configured threshold
            if len(self.failed_login_attempts[key]) >= self.config.FAILED_LOGIN_THRESHOLD:
                # Construct the alert description
                description = (
                    f"Detected {len(self.failed_login_attempts[key])} failed login attempts "
                    f"for user '{username}' from IP '{log_entry.ip_address}' "
                    f"within {self.config.FAILED_LOGIN_TIME_WINDOW_SECONDS} seconds."
                )

                # Create an Alert object
                new_alert = Alert(
                    alert_type="Multiple Failed Logins",
                    severity="High",
                    timestamp=datetime.now(), # Alert timestamp is when it's generated
                    description=description,
                    source_ip_host=log_entry.ip_address,
                    related_logs=[lid for ts, lid in self.failed_login_attempts[key]] # Collect IDs of relevant logs
                )
                # Insert the new alert into the database
                self.db.insert_alert(new_alert)

                # Clear the attempts for this specific key to prevent re-alerting
                # on the same burst immediately. A new burst will start tracking anew.
                self.failed_login_attempts[key] = []

# Example Usage (for testing purposes)
if __name__ == "__main__":
    # Simulate database and config
    class MockConfig:
        FAILED_LOGIN_THRESHOLD = 3
        FAILED_LOGIN_TIME_WINDOW_SECONDS = 60

    class MockDbClient:
        def insert_log(self, log_entry: LogEntry):
            if not log_entry._id:
                log_entry._id = f"mock_log_{datetime.now().timestamp()}"
            return log_entry._id
        def insert_alert(self, alert: Alert):
            print(f"MockDbClient: ALERT TRIGGERED: {alert.description} (Severity: {alert.severity})")

    mock_config = MockConfig()
    mock_db = MockDbClient()
    detection_rules = DetectionRules(mock_db, mock_config)

    print("--- Simulating Failed Login Burst Detection ---")

    # Scenario 1: Not enough attempts
    log1 = LogEntry(datetime.now(), "host-x", "Authentication", "AUTH", "Failed password for user test from 1.1.1.1.", "raw_log_1")
    log1._id = mock_db.insert_log(log1)
    detection_rules.run_all_rules(log1)
    print("Attempt 1 processed.")

    log2 = LogEntry(datetime.now(), "host-x", "Authentication", "AUTH", "Failed password for user test from 1.1.1.1.", "raw_log_2")
    log2._id = mock_db.insert_log(log2)
    detection_rules.run_all_rules(log2)
    print("Attempt 2 processed.")
    print("Expected: No alert yet.")

    # Scenario 2: Enough attempts within the window
    log3 = LogEntry(datetime.now(), "host-x", "Authentication", "AUTH", "Failed password for user test from 1.1.1.1.", "raw_log_3")
    log3._id = mock_db.insert_log(log3)
    detection_rules.run_all_rules(log3)
    print("Attempt 3 processed.")
    print("Expected: ALERT: Multiple Failed Logins for test from 1.1.1.1.")

    # Scenario 3: Attempts outside the window
    print("\nSimulating attempts far apart...")
    log4 = LogEntry(datetime.now() - timedelta(minutes=5), "host-y", "Authentication", "AUTH", "Failed password for user user2 from 2.2.2.2.", "raw_log_4")
    log4._id = mock_db.insert_log(log4)
    detection_rules.run_all_rules(log4)

    log5 = LogEntry(datetime.now(), "host-y", "Authentication", "AUTH", "Failed password for user user2 from 2.2.2.2.", "raw_log_5")
    log5._id = mock_db.insert_log(log5)
    detection_rules.run_all_rules(log5)
    print("Expected: No alert (first attempt is too old).")
