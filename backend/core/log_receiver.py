# backend/core/log_receiver.py

from backend.config import Config
from backend.database.db_client import SiemDatabase
from backend.core.log_parser import LogParser
from backend.core.detection_rules import DetectionRules
from backend.database.models import LogEntry # Only for type hinting

# This file would typically contain code to listen for incoming log data
# from various sources (e.g., Syslog, Kafka, file watchers).
# For this conceptual example, we'll use a simple function.

def process_raw_log(raw_log_line: str, db_client: SiemDatabase, parser: LogParser, rules_engine: DetectionRules):
    """
    Receives a raw log line, orchestrates its parsing, storage, and rule evaluation.
    This function acts as the entry point for each new log event.
    """
    print(f"LogReceiver: Receiving raw log: '{raw_log_line[:70]}...'")

    # 1. Parse the raw log line into a structured LogEntry object
    log_entry = parser.parse_log_line(raw_log_line)

    if log_entry:
        print(f"LogReceiver: Successfully parsed log (Level: {log_entry.level}, Source: {log_entry.source})")
        # 2. Store the parsed log in the database
        log_id = db_client.insert_log(log_entry)

        if log_id:
            # Ensure the LogEntry object has its _id set, needed for related_logs in alerts
            log_entry._id = log_id
            print(f"LogReceiver: Log stored with ID: {log_id}")

            # 3. Pass the structured log to the detection rules engine
            rules_engine.run_all_rules(log_entry)
            print("LogReceiver: Detection rules applied.")
        else:
            print(f"ERROR: LogReceiver: Failed to store parsed log: {log_entry.message}")
    else:
        print(f"WARNING: LogReceiver: Failed to parse raw log: '{raw_log_line}'. Skipping.")

# Example of how this might be used (e.g., from a Flask/FastAPI endpoint
# or a standalone log collection service)
if __name__ == "__main__":
    print("--- Running Conceptual Log Receiver Simulation ---")

    # Initialize conceptual components
    config = Config()
    db_client = SiemDatabase(config)
    parser = LogParser()
    rules_engine = DetectionRules(db_client, config)

    sample_raw_logs = [
        "Jun 17 10:00:01 host-a kernel: [INFO] System started.",
        "Jun 17 10:00:05 host-b sshd[123]: [AUTH] Failed password for user testuser from 192.168.1.100.",
        "Jun 17 10:00:08 host-b sshd[124]: [AUTH] Failed password for user testuser from 192.168.1.100.",
        "Jun 17 10:00:12 host-b sshd[125]: [AUTH] Failed password for user testuser from 192.168.1.100.",
        "Jun 17 10:00:15 web-server-01 apache: [WARN] High memory usage.",
        "Jun 17 10:00:30 critical-db app: [CRITICAL] Unauthorized data access detected from 10.0.0.5."
    ]

    for raw_log in sample_raw_logs:
        process_raw_log(raw_log, db_client, parser, rules_engine)
        print("-" * 50) # Separator for clarity

    print("\n--- Simulation Complete ---")
    print("\nFinal State of Conceptual Database:")
    print(f"  Total Logs: {len(db_client._mock_logs_storage)}")
    print(f"  Total Alerts: {len(db_client._mock_alerts_storage)}")
