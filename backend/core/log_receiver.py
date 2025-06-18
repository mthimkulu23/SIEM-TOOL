from backend.config import Config
from backend.database.db_client import SiemDatabase
from backend.core.log_parser import LogParser
from backend.core.detection_rules import DetectionRules
from backend.database.models import LogEntry # Only for type hinting, actual object is created by parser

def process_raw_log(raw_log_line: str, db_client: SiemDatabase, parser: LogParser, rules_engine: DetectionRules):
    """
    Receives a raw log line, orchestrates its parsing, storage, and rule evaluation.
    This function acts as the entry point for each new log event.
    """
    print(f"LogReceiver: Receiving raw log: '{raw_log_line[:70]}...'")

    # 1. Parse the raw log line into a structured LogEntry object
    # IMPORTANT: Call the correct parsing method on LogParser, which now returns a LogEntry object.
    log_entry_obj = parser.parse_log_entry(raw_log_line) # THIS IS THE CORRECTION

    if log_entry_obj: # It should always return an object now, even if mostly defaults
        print(f"LogReceiver: Successfully parsed log (Level: {log_entry_obj.level}, Source: {log_entry_obj.source})")
        # 2. Store the parsed log in the database
        inserted_id = db_client.insert_log(log_entry_obj) # db_client expects a LogEntry object

        if inserted_id:
            # Set the _id on the LogEntry object AFTER insertion,
            # as it's needed by detection rules if they query for related logs.
            log_entry_obj._id = inserted_id
            print(f"LogReceiver: Log stored with ID: {inserted_id}")

            # 3. Pass the structured LogEntry object to the detection rules engine
            rules_engine.run_rules_on_log(log_entry_obj) # THIS IS THE CORRECTION: Correct method name
            print("LogReceiver: Detection rules applied.")
        else:
            print(f"ERROR: LogReceiver: Failed to store parsed log: {log_entry_obj.message}")
    else:
        # This case should be rare now with the improved parser always returning an object
        print(f"WARNING: LogReceiver: Parser returned None for raw log: '{raw_log_line}'. Skipping.")

# Example of how this might be used (e.g., from a Flask/FastAPI endpoint
# or a standalone log collection service)
if __name__ == "__main__":
    print("--- Running Conceptual Log Receiver Simulation ---")

    # Initialize conceptual components
    config = Config()
    db_client = SiemDatabase(config)
    parser = LogParser()
    rules_engine = DetectionRules(db_client, config)

    # Make sure to uncomment MongoDB setup in scripts/setup_db.py
    # and run it once before running this simulation if using a real DB.
    # Otherwise, db_client will use mock storage if not properly connected.

    # Clear mock storage for fresh simulation if db_client is in mock mode
    if hasattr(db_client, '_mock_logs_storage'):
        db_client._mock_logs_storage = []
        db_client._mock_alerts_storage = []
        print("Cleared mock storage for fresh simulation.")


    sample_raw_logs = [
        "Jun 17 10:00:01 host-a kernel: [INFO] System boot successful.", # Will be System/INFO
        "Jun 17 10:00:05 host-b sshd[123]: [AUTH] Failed password for user flask_test from 192.168.1.10.", # Will be Authentication/AUTH_FAILED
        "Jun 17 10:00:08 host-b sshd[124]: [AUTH] Failed password for user flask_test from 192.168.1.10.",
        "Jun 17 10:00:12 host-b sshd[125]: [AUTH] Failed password for user flask_test from 192.168.1.10.", # This one should trigger brute force alert
        "Jun 17 10:00:15 web-server-01 apache: [WARN] High CPU usage (85%).", # Web Server/WARN
        "Jun 17 10:00:20 db-server-01 postgres: [ERROR] Database connection pool exhausted.", # Database/ERROR
        "Jun 17 10:00:25 firewall-01 firewall: [INFO] Policy update applied.", # Network/INFO
        "Jun 17 10:00:30 critical-db app: [CRITICAL] Unauthorized data export attempt detected from 10.0.0.5 to external_server.", # Application/CRITICAL
        "Jun 17 10:00:35 backup-srv: [INFO] Daily backup initiated for critical_data_volume.", # Backup System/INFO
        "Jun 17 10:00:40 log-server-01 disk: [WARN] Low disk space on /var/log (90% full).", # System Monitor/WARN
        "Jun 17 10:00:45 endpoint-sec-03 av: [INFO] Anti-virus definitions updated to latest version.", # Endpoint Security/INFO
        "Jun 17 10:00:50 hr-laptop-03 endpoint: [ALERT] Ransomware activity detected and blocked on C:\\HR_Docs\\.", # Endpoint Security/CRITICAL
        "Jun 17 10:01:00 router-core-01 network: [INFO] New routing table deployed.", # Network/INFO
        "Jun 17 10:01:10 web-server-02 cert-monitor: [WARN] SSL certificate 'www.example.com' expires in 10 days.", # Certificate Monitor/WARN
        "Jun 17 10:01:20 db-dev-02 netflow: [ALERT] Suspicious high volume outbound connections to 172.16.20.100." # Network/ALERT
    ]

    for raw_log in sample_raw_logs:
        process_raw_log(raw_log, db_client, parser, rules_engine)
        print("-" * 50) # Separator for clarity

    print("\n--- Simulation Complete ---")
    # For real MongoDB, you'd query the DB to verify
    # For mock data:
    if hasattr(db_client, '_mock_logs_storage'):
        print(f"  Total Logs (Mock): {len(db_client._mock_logs_storage)}")
        print(f"  Total Alerts (Mock): {len(db_client._mock_alerts_storage)}")
        print("Mock Logs:")
        for log in db_client._mock_logs_storage:
            print(f"    [{log.level}] {log.timestamp.strftime('%H:%M:%S')} {log.host} ({log.source}): {log.message[:60]}...")
        print("\nMock Alerts:")
        for alert in db_client._mock_alerts_storage:
            print(f"    [{alert.severity}] {alert.timestamp.strftime('%H:%M:%S')} ({alert.rule_name}): {alert.description}")