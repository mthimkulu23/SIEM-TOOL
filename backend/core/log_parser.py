# backend/core/log_parser.py

import re
from datetime import datetime
from backend.database.models import LogEntry # Assuming LogEntry is defined here

class LogParser:
    def __init__(self):
        # Regex to capture common log fields: Month Day HH:MM:SS host process: [LEVEL] message
        # This regex is a starting point and might need to be refined based on actual log formats.
        self.log_pattern = re.compile(
            r"^(?P<month>\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})\s+" # Timestamp (Month Day HH:MM:SS)
            r"(?P<host>\S+)\s+"                                  # Hostname/IP
            r"(?P<process>[a-zA-Z0-9_\-\.]+)(?:\[(?P<pid>\d+)\])?:\s*" # Process name (and optional PID)
            r"(?:\[(?P<level>[A-Z]+)\]\s*)?"                     # Log Level (optional, e.g., [INFO], [ERROR])
            r"(?P<message>.*)$"                                  # Remaining message
        )
        print("LogParser initialized.") # Added for debugging deployment

    def parse_log(self, raw_log_string: str) -> LogEntry | None:
        """
        Parses a raw log string into a structured LogEntry object.
        Extracts timestamp, host, process, level, and message.
        Attempts to extract source_ip_host and destination_ip_host from the message.
        """
        match = self.log_pattern.match(raw_log_string)
        if not match:
            # print(f"Failed to parse log: {raw_log_string}") # Uncomment for local debugging if needed
            return None

        data = match.groupdict()

        # Parse timestamp (adjust format string as needed)
        try:
            # Example: Jun 17 10:00:01
            # Python's strptime can't parse %b %d %H:%M:%S directly if year is missing
            # For simplicity in mock data, we'll assume current year if not present
            # or try to parse with a fixed year if logs are always from current year.
            # A more robust solution might infer the year or require it in logs.

            # Let's try to parse with current year (assuming logs are recent)
            current_year = datetime.now().year
            timestamp_str_with_year = f"{data['month']} {current_year}"
            timestamp = datetime.strptime(timestamp_str_with_year, "%b %d %H:%M:%S %Y")
        except ValueError:
            # Fallback if parsing fails, or handle a different timestamp format
            # print(f"Warning: Could not parse timestamp from log: {raw_log_string}")
            timestamp = datetime.now() # Use current time as fallback

        source = data.get('process') or data.get('host') or "Unknown"
        level = data.get('level', 'INFO').upper()
        message = data.get('message', '').strip()
        host = data.get('host', 'unknown-host')

        # Attempt to extract source_ip_host and destination_ip_host from the message
        source_ip_host = None
        destination_ip_host = None

        # Regex for common IP patterns in messages (e.g., "from 192.168.1.10", "to 10.0.0.5")
        # This is a very basic example; real-world parsing might need more sophisticated NLP or specific patterns per log type.
        ip_pattern = re.compile(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b')
        ips_found = ip_pattern.findall(message)

        if "from " in message and ips_found:
            source_ip_match = re.search(r'from (\S+)', message)
            if source_ip_match:
                # Use the matched group directly if it looks like an IP or hostname
                potential_source = source_ip_match.group(1).strip('.,')
                if re.match(ip_pattern, potential_source) or '.' in potential_source: # Simple check for IP or hostname
                    source_ip_host = potential_source
                else: # Fallback for just an IP found in message
                    source_ip_host = ips_found[0] if ips_found else None

        if "to " in message and ips_found:
            destination_ip_match = re.search(r'to (\S+)', message)
            if destination_ip_match:
                # Use the matched group directly if it looks like an IP or hostname
                potential_destination = destination_ip_match.group(1).strip('.,')
                if re.match(ip_pattern, potential_destination) or '.' in potential_destination:
                    destination_ip_host = potential_destination
                else: # Fallback for just an IP found in message
                    destination_ip_host = ips_found[-1] if ips_found else None # Last IP might be destination

        # Default source_ip_host to the host field if not found in message
        if not source_ip_host:
            source_ip_host = host if re.match(ip_pattern, host) or '.' in host else None


        log_entry = LogEntry(
            timestamp=timestamp,
            host=host,
            source=source,
            level=level,
            message=message,
            source_ip_host=source_ip_host,
            destination_ip_host=destination_ip_host,
            raw_log=raw_log_string
        )
        return log_entry