import re
from datetime import datetime

class LogParser:
    def __init__(self):
        # Define common log patterns. More can be added as needed.
        # This regex is a simplified example to match the mock data logs.
        # It looks for:
        # 1. Month, Day, Time (e.g., Jun 17 10:00:01)
        # 2. Hostname (e.g., host-a, web-server-01)
        # 3. Optional process/source (e.g., kernel, sshd[123], apache, app)
        # 4. Log Level in brackets (e.g., [INFO], [ERROR], [CRITICAL], [ALERT], [WARN], [AUTH])
        # 5. The rest of the message
        self.patterns = [
            re.compile(
                r'^(?P<month>\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})\s+' # Timestamp (e.g., Jun 17 10:00:01)
                r'(?P<host>[a-zA-Z0-9\._-]+)\s+'                       # Hostname
                r'(?P<process>[a-zA-Z0-9\._-]+(?:\[\d+\])?:)?\s*'    # Optional process (e.g., sshd[123]:)
                r'\[(?P<level>[A-Z]+)\]\s+'                           # Log Level (e.g., [INFO])
                r'(?P<message>.*)'                                    # The rest of the message
            ),
            # Add more patterns here for different log formats (e.g., JSON, Windows Event Logs)
            # Example for a more generic non-syslog line (fallback)
            re.compile(
                r'^(?P<timestamp>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)\s+' # ISO timestamp
                r'(?P<level>[A-Z]+):\s+'                               # Level
                r'(?P<message>.*)'                                     # Message
            ),
            # Simple fallback for lines that don't match complex patterns
            re.compile(
                r'^(?P<message>.*)' # Catch-all for any text
            )
        ]

        # Regex to find IPs in messages
        self.ip_pattern = re.compile(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b')

    def parse_log_entry(self, raw_log: str) -> dict:
        """
        Parses a raw log string into a structured dictionary based on defined patterns.
        """
        parsed_data = {
            'timestamp': datetime.now(), # Default to current time if unable to parse
            'host': 'unknown_host',
            'source': 'unknown_source',
            'level': 'INFO', # Default level
            'message': raw_log,
            'source_ip_host': None,
            'destination_ip_host': None,
            'raw_log': raw_log # Always store the original raw log
        }

        # Attempt to parse with the first, more specific pattern (Syslog-like)
        match = self.patterns[0].match(raw_log)
        if match:
            data = match.groupdict()
            try:
                # Attempt to parse the timestamp. Need current year for datetime object.
                # Format: "Jun 17 10:00:01"
                # To make this robust, you might need to infer the year or pass it.
                # For simplicity here, we'll assume current year.
                current_year = datetime.now().year
                timestamp_str = f"{data['month']} {current_year}"
                parsed_data['timestamp'] = datetime.strptime(timestamp_str, "%b %d %H:%M:%S %Y")
            except ValueError:
                # If timestamp parsing fails, keep the default datetime.now()
                pass

            parsed_data['host'] = data['host']
            # Use process if available, otherwise default to host or a generic source
            parsed_data['source'] = data['process'].strip(':') if data['process'] else data['host']
            parsed_data['level'] = data['level']
            parsed_data['message'] = data['message'].strip()

            # Attempt to extract IP addresses from the message
            ips = self.ip_pattern.findall(parsed_data['message'])
            if len(ips) > 0:
                # A very simplistic IP assignment: first one is source, second (if any) is dest
                parsed_data['source_ip_host'] = ips[0]
                if len(ips) > 1:
                    parsed_data['destination_ip_host'] = ips[1]
            return parsed_data
        
        # Add more `elif` blocks here for other patterns if you have them,
        # otherwise, the default parsed_data with raw_log as message will be returned.

        # If no specific pattern matches, return the default structure with the raw log.
        return parsed_data

    def parse_log(self, raw_log: str) -> dict:
        """
        Backward compatibility for older calls, delegates to parse_log_entry.
        """
        print("Warning: parse_log is deprecated. Use parse_log_entry instead.")
        return self.parse_log_entry(raw_log)