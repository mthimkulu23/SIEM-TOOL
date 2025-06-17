# backend/core/log_parser.py

import re
from datetime import datetime
from backend.database.models import LogEntry

class LogParser:
    """
    Handles parsing and initial structuring of raw log data into LogEntry objects.
    This parser is designed for a simplified, common log format.
    """
    def __init__(self):
        # Regular expression to parse log lines.
        # It captures: Month, Day, Time, Host, Process Info, Log Level, and Message.
        self.log_pattern = re.compile(
            r"(\w+ \d+ \d{2}:\d{2}:\d{2}) " # Group 1: Timestamp (e.g., Jun 17 10:00:01)
            r"(\S+) "                       # Group 2: Hostname (e.g., host-a)
            r"(.*?): "                      # Group 3: Process Info (e.g., kernel, sshd[123]) - non-greedy match
            r"\[(INFO|WARN|ERROR|ALERT|CRITICAL|AUTH|DEBUG|TRACE)\] " # Group 4: Log Level
            r"(.*)"                         # Group 5: The rest of the message
        )
        # Regex to find common IPv4 patterns within the message
        self.ip_pattern = re.compile(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b")

        # Simplified mapping for common log sources/processes
        self.source_mapping = {
            "sshd": "Authentication",
            "apache": "Web Server",
            "nginx": "Web Server",
            "kernel": "System",
            "firewall": "Firewall",
            "postgres": "Database",
            "mysql": "Database",
            "app": "Application",
            "systemd": "System",
            "cron": "System",
            "network": "Network",
            "av": "Endpoint Security",
            "endpoint": "Endpoint Security",
            "vuln-scan": "Vulnerability Scanner",
            "backup-srv": "Backup System",
            "cert-monitor": "System",
            "auth-server": "Authentication", # More specific mapping
            "netflow": "Network" # For network flow data
        }

    def parse_log_line(self, log_line: str) -> LogEntry | None:
        """
        Parses a single raw log line string into a structured LogEntry object.
        Returns a LogEntry object on success, None on failure.
        """
        match = self.log_pattern.match(log_line)
        if not match:
            # print(f"DEBUG: No regex match for log: {log_line}")
            return None

        timestamp_str, host, process_info, level, message = match.groups()

        # --- Parse Timestamp ---
        # We assume the current year as logs usually don't contain it.
        # In a real-world scenario, you might infer the year from context
        # or require it to be present in the log.
        try:
            current_year = datetime.now().year
            # Example: "Jun 17 10:00:01 2024"
            timestamp = datetime.strptime(f"{timestamp_str} {current_year}", "%b %d %H:%M:%S %Y")
        except ValueError:
            # Fallback if timestamp format doesn't match or is invalid
            timestamp = datetime.now()
            print(f"WARNING: Could not parse exact timestamp for log: '{log_line}'. Using current time.")

        # --- Extract IP Address ---
        ip_address = None
        ip_match = self.ip_pattern.search(message)
        if ip_match:
            ip_address = ip_match.group(0)

        # --- Determine Source Name ---
        # Clean the process_info to get a more standardized source name.
        process_name_clean = process_info.split('[')[0].strip().lower()
        source = self.source_mapping.get(process_name_clean, "Unknown")
        if source == "Unknown" and process_name_clean:
            # If still unknown after mapping, capitalize the raw process name as a fallback.
            source = process_name_clean.capitalize()

        return LogEntry(
            timestamp=timestamp,
            host=host,
            source=source,
            level=level,
            message=message,
            raw_log=log_line,
            ip_address=ip_address
        )

# Example Usage (for testing purposes)
if __name__ == "__main__":
    parser = LogParser()
    sample_logs = [
        "Jun 17 10:00:01 host-a kernel: [INFO] User 'john.doe' logged in.",
        "Jun 17 10:00:05 host-b sshd[123]: [AUTH] Failed password for user admin from 203.0.113.5.",
        "Jul 01 08:30:15 web-server-01 apache: [WARN] High CPU usage.",
        "Aug 22 14:10:00 db-server-01 postgres: [CRITICAL] Unauthorized access attempt from 10.0.0.5.",
        "Sep 05 23:59:59 endpoint-01 av: [ALERT] Malware detected: virus.exe.",
        "Oct 10 07:07:07 router-alpha network: [INFO] Interface Up.",
        "Nov 15 11:11:11 unknown_host custom_app[55]: [DEBUG] Debug message here."
    ]

    print("--- Parsing Sample Logs ---")
    for i, log_line in enumerate(sample_logs):
        print(f"\nProcessing Log {i+1}: '{log_line}'")
        parsed_log = parser.parse_log_line(log_line)
        if parsed_log:
            print(f"  Parsed LogEntry:")
            print(f"    ID: {parsed_log._id}") # Will be None here, set by DB client
            print(f"    Timestamp: {parsed_log.timestamp}")
            print(f"    Host: {parsed_log.host}")
            print(f"    Source: {parsed_log.source}")
            print(f"    Level: {parsed_log.level}")
            print(f"    Message: {parsed_log.message}")
            print(f"    IP Address: {parsed_log.ip_address}")
        else:
            print("  Parsing FAILED.")
