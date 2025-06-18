# backend/core/log_parser.py

import re
from datetime import datetime
from typing import Optional, Dict, Any
from backend.database.models import LogEntry # Crucial: Ensure LogEntry is imported

class LogParser:
    def __init__(self):
        # Updated regex to capture more robustly and handle various syslog formats
        # Added named groups for clarity: month, day, time, host, process, pid, level_tag, message
        self.syslog_pattern = re.compile(
            r"^(?P<month>\w{3})\s+"
            r"(?P<day>\s*\d{1,2})\s+"
            r"(?P<time>\d{2}:\d{2}:\d{2})\s+"
            r"(?P<host>[a-zA-Z0-9\-\._]+)\s+"
            r"(?P<process>[a-zA-Z0-9\/\._\-]+)(?:\[(?P<pid>\d+)\])?:\s*"
            r"(?:\[(?P<level_tag>[^\]]+)\]\s*)?" # Optional level tag like [INFO] or [AUTH]
            r"(?P<message>.*)$"
        )

        # Common source patterns to normalize
        self.source_map = {
            "kernel": "System",
            "sshd": "Authentication",
            "sudo": "Authentication",
            "apache": "Web Server",
            "nginx": "Web Server",
            "mysql": "Database",
            "postgres": "Database",
            "firewall": "Network",
            "network": "Network",
            "app": "Application", # Generic application logs
            "cron": "Scheduler",
            "systemd": "System",
            "rsyslogd": "Logging System",
            "audit": "Security Audit",
            "authpriv": "Authentication",
            "mail": "Mail System",
            "daemon": "System Daemon",
            "ntp": "Time Sync",
            "disk": "System Monitor",
            "cert-monitor": "Certificate Monitor",
            "av": "Endpoint Security",
            "endpoint": "Endpoint Security",
            "netflow": "Network Flow",
            "backup-srv": "Backup System",
            # Add more as needed based on your log sources
        }
        
        self.level_map = {
            "INFO": "INFO",
            "NOTICE": "INFO", # Treat NOTICE as INFO for dashboard purposes
            "WARN": "WARN",
            "WARNING": "WARN",
            "ERR": "ERROR",
            "ERROR": "ERROR",
            "CRIT": "CRITICAL",
            "CRITICAL": "CRITICAL",
            "ALERT": "CRITICAL", # Treating ALERT as CRITICAL for this SIEM
            "EMERG": "CRITICAL", # Treating EMERGENCY as CRITICAL
            "AUTH": "AUTHENTICATION", # Special level for authentication events
            "AUTHPRIV": "AUTHENTICATION",
            "DEBUG": "DEBUG",
            "FATAL": "CRITICAL",
        }


    def _normalize_source(self, raw_source: str, message: str) -> str:
        """Normalizes a raw source string to a common category."""
        normalized = self.source_map.get(raw_source.lower(), "unknown_source")

        # Further infer source from message content if still unknown or generic
        if normalized == "unknown_source" or normalized == raw_source.lower():
            message_lower = message.lower()
            if "login" in message_lower or "authentication" in message_lower or "user session" in message_lower:
                return "Authentication"
            if "cpu" in message_lower or "memory" in message_lower or "disk" in message_lower or "system" in message_lower:
                return "System Monitor"
            if "http" in message_lower or "web server" in message_lower or "request" in message_lower:
                return "Web Server"
            if "database" in message_lower or "sql" in message_lower or "query" in message_lower:
                return "Database"
            if "firewall" in message_lower or "deny" in message_lower or "accept" in message_lower or "connection" in message_lower:
                return "Network"
            if "malware" in message_lower or "virus" in message_lower or "ransomware" in message_lower or "threat" in message_lower:
                return "Endpoint Security"
            if "backup" in message_lower or "snapshot" in message_lower:
                return "Backup System"
            if "certificate" in message_lower or "ssl" in message_lower or "tls" in message_lower:
                return "Certificate Monitor"

        return normalized

    def _normalize_level(self, raw_level: str, message: str) -> str:
        """Normalizes a raw log level string to a common category."""
        normalized = self.level_map.get(raw_level.upper(), "INFO") # Default to INFO if unknown

        # Try to infer level from message content if the initial level is generic or missing
        message_lower = message.lower()
        if normalized == "INFO": # Only try to refine if it's still default INFO
            if "failed password" in message_lower or "authentication failure" in message_lower:
                return "AUTH_FAILED" # Custom level for specific rule matching
            if "error" in message_lower or "failed" in message_lower or "denied" in message_lower:
                return "ERROR"
            if "critical" in message_lower or "unauthorized" in message_lower or "alert" in message_lower or "ransomware" in message_lower:
                return "CRITICAL"
            if "warning" in message_lower or "high usage" in message_lower or "low disk" in message_lower:
                return "WARN"
            
        return normalized

    def _extract_ip_addresses(self, message: str) -> Dict[str, Optional[str]]:
        """Extracts source and destination IP addresses from the message."""
        source_ip = None
        destination_ip = None

        # Regex for common IP patterns including specific "from X.X.X.X to Y.Y.Y.Y"
        ip_patterns = {
            'from_to': r'from\s+(?P<src_ip>\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b)\s+to\s+(?P<dest_ip>\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b)',
            'from_only': r'from\s+(?P<src_ip>\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b)',
            'dest_only': r'to\s+(?P<dest_ip>\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b)',
            'any_ip': r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b' # General IP match
        }

        # Try specific patterns first
        if re.search(ip_patterns['from_to'], message):
            match = re.search(ip_patterns['from_to'], message)
            source_ip = match.group('src_ip')
            destination_ip = match.group('dest_ip')
        elif re.search(ip_patterns['from_only'], message):
            match = re.search(ip_patterns['from_only'], message)
            source_ip = match.group('src_ip')
        elif re.search(ip_patterns['dest_only'], message):
            match = re.search(ip_patterns['dest_only'], message)
            destination_ip = match.group('dest_ip')
        else:
            # Fallback to finding any IPs if specific patterns don't match
            all_ips = re.findall(ip_patterns['any_ip'], message)
            if all_ips:
                source_ip = all_ips[0] # Assume first found IP is source
                if len(all_ips) > 1:
                    destination_ip = all_ips[1] # Assume second is destination

        return {'source_ip_host': source_ip, 'destination_ip_host': destination_ip}


    def parse_log_entry(self, raw_log: str) -> LogEntry:
        """
        Parses a raw log string into a structured LogEntry object.
        This method is designed to be called by log_receiver.
        It encapsulates the full parsing and normalization logic.
        """
        match = self.syslog_pattern.match(raw_log)
        
        # Initialize with defaults in case parsing fails or parts are missing
        parsed_data = {
            'raw_log': raw_log,
            'timestamp': datetime.now(), # Default to current time
            'host': 'unknown_host',
            'source': 'unknown_source',
            'level': 'INFO', # Default to INFO
            'message': raw_log, # Default message is the raw log
            'source_ip_host': None,
            'destination_ip_host': None,
        }

        if match:
            # Extract basic components
            month_str = match.group('month')
            day_str = match.group('day')
            time_str = match.group('time')
            host = match.group('host')
            process = match.group('process')
            level_tag = match.group('level_tag')
            message = match.group('message').strip()

            # Construct timestamp (assuming current year if no year in log)
            try:
                current_year = datetime.now().year
                timestamp_str = f"{month_str} {day_str} {time_str} {current_year}"
                parsed_data['timestamp'] = datetime.strptime(timestamp_str, "%b %d %H:%M:%S %Y")
            except ValueError:
                # If parsing date/time fails, keep the default datetime.now()
                pass 

            parsed_data['host'] = host if host else 'unknown_host'
            parsed_data['message'] = message

            # Initial level extraction from tag
            if level_tag:
                parsed_data['level'] = level_tag.strip('[]')

            # Initial source extraction from process name
            if process:
                parsed_data['source'] = process.strip(':')

            # Extract IP addresses
            ip_info = self._extract_ip_addresses(message)
            parsed_data['source_ip_host'] = ip_info['source_ip_host']
            parsed_data['destination_ip_host'] = ip_info['destination_ip_host']

        # Apply normalization and further inference
        parsed_data['source'] = self._normalize_source(parsed_data['source'], parsed_data['message'])
        parsed_data['level'] = self._normalize_level(parsed_data['level'], parsed_data['message'])

        # Create and return a LogEntry object
        return LogEntry(
            timestamp=parsed_data['timestamp'],
            host=parsed_data['host'],
            source=parsed_data['source'],
            level=parsed_data['level'],
            message=parsed_data['message'],
            source_ip_host=parsed_data['source_ip_host'],
            destination_ip_host=parsed_data['destination_ip_host'],
            raw_log=raw_log # Ensure the original raw log is always stored
        )

# Example usage (for testing LogParser in isolation) - this part is not used by log_receiver
if __name__ == '__main__':
    parser = LogParser()
    
    test_logs = [
        "Jun 17 10:00:01 host-a kernel: [INFO] System boot successful.",
        "Jun 17 10:00:05 host-b sshd[123]: [AUTH] Failed password for user flask_test from 192.168.1.10.",
        "Jun 17 10:00:15 web-server-01 apache: [WARN] High CPU usage (85%).",
        "Jun 17 10:00:30 critical-db app: [CRITICAL] Unauthorized data export attempt detected from 10.0.0.5 to external_server.",
        "Jun 17 10:00:50 hr-laptop-03 endpoint: [ALERT] Ransomware activity detected and blocked on C:\\HR_Docs\\.",
        "Jun 17 10:01:20 db-dev-02 netflow: [ALERT] Suspicious high volume outbound connections to 172.16.20.100."
    ]

    print("--- LogParser Direct Test ---")
    for log_str in test_logs:
        print(f"\nParsing: '{log_str}'")
        parsed_entry = parser.parse_log_entry(log_str)
        if parsed_entry:
            print(f"  Parsed LogEntry:")
            print(f"    Timestamp: {parsed_entry.timestamp}")
            print(f"    Host: {parsed_entry.host}")
            print(f"    Source: {parsed_entry.source}")
            print(f"    Level: {parsed_entry.level}")
            print(f"    Message: {parsed_entry.message}")
            print(f"    Source IP: {parsed_entry.source_ip_host}")
            print(f"    Destination IP: {parsed_entry.destination_ip_host}")
            print(f"    Raw Log: {parsed_entry.raw_log[:70]}...")
        else:
            print("  Parsing failed: Returned None")