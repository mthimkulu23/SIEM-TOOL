import re
from datetime import datetime
from backend.database.models import LogEntry

class LogParser:
    def __init__(self):
        # Optimized regex to capture common syslog-like formats with optional process and brackets
        # Group 1: Timestamp (Month Day HH:MM:SS)
        # Group 2: Hostname
        # Group 3: Optional Process (e.g., 'sshd[123]:', 'kernel:')
        # Group 4: Optional Log Level in Brackets (e.g., '[INFO]', '[AUTH]')
        # Group 5: The rest of the Message
        self.syslog_pattern = re.compile(
            r'^(?P<month>\w{3})\s+(?P<day>\d{1,2})\s+(?P<time>\d{2}:\d{2}:\d{2})\s+'
            r'(?P<host>[a-zA-Z0-9\._-]+)\s+'
            r'(?P<process>[a-zA-Z0-9\._-]+(?:\[\d+\])?:\s*)?' # Optional process with colon and space
            r'(?:\[(?P<level>[A-Z_]+)\])?\s*'               # Optional level in brackets
            r'(?P<message>.*)'
        )

        # Regex to find IP addresses
        self.ip_pattern = re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b')

    def parse_log_entry(self, raw_log: str) -> dict:
        """
        Parses a raw log string into a structured dictionary.
        """
        parsed_data = {
            'timestamp': datetime.now(), # Default to current time if parsing fails
            'host': 'unknown_host',
            'source': 'unknown_source',
            'level': 'INFO', # Default level
            'message': raw_log,
            'source_ip_host': None,
            'destination_ip_host': None,
            'raw_log': raw_log # Always store the original raw log
        }

        match = self.syslog_pattern.match(raw_log)
        if match:
            data = match.groupdict()
            try:
                # Construct datetime object: Add current year for full date
                current_year = datetime.now().year
                timestamp_str = f"{data['month']} {data['day']} {data['time']} {current_year}"
                parsed_data['timestamp'] = datetime.strptime(timestamp_str, "%b %d %H:%M:%S %Y")
            except ValueError:
                # If timestamp parsing fails, keep the default datetime.now()
                pass

            parsed_data['host'] = data['host']
            parsed_data['message'] = data['message'].strip()

            # Process source: take from 'process' group, clean it, and normalize
            process_raw = data['process'].strip(': ').split('[')[0].strip() if data['process'] else ''
            if process_raw:
                parsed_data['source'] = self._normalize_source(process_raw)
            else:
                # If no process, try to infer from message or host
                parsed_data['source'] = self._infer_source_from_message(parsed_data['message'], parsed_data['host'])

            # Level extraction
            parsed_data['level'] = data['level'] if data['level'] else 'INFO' # Use parsed level or default to INFO

            # IP Address Extraction - more robust
            self._extract_ips(parsed_data)

            # Further refine level and source based on message content
            self._refine_level_and_source_by_content(parsed_data)

        # If no syslog pattern matches, we rely on defaults.
        # Ensure 'message' is always the raw log if nothing else is parsed.
        if not match:
             parsed_data['message'] = raw_log # Make sure message is not None if no match

        return parsed_data

    def _normalize_source(self, raw_source: str) -> str:
        """Normalizes raw source strings to predefined categories."""
        raw_source_lower = raw_source.lower()
        if 'sshd' in raw_source_lower or 'login' in raw_source_lower or 'auth' in raw_source_lower:
            return 'Authentication'
        elif 'firewall' in raw_source_lower or 'router' in raw_source_lower or 'network' in raw_source_lower or 'netflow' in raw_source_lower:
            return 'Network'
        elif 'apache' in raw_source_lower or 'nginx' in raw_source_lower or 'web-server' in raw_source_lower:
            return 'Web Server'
        elif 'endpoint' in raw_source_lower or 'av' in raw_source_lower or 'antivirus' in raw_source_lower:
            return 'Endpoint Security'
        elif 'postgres' in raw_source_lower or 'db-server' in raw_source_lower or 'database' in raw_source_lower:
            return 'Database'
        elif 'kernel' in raw_source_lower or 'system' in raw_source_lower:
            return 'System'
        elif 'app' in raw_source_lower or 'application' in raw_source_lower:
            return 'Application'
        elif 'backup' in raw_source_lower:
            return 'Backup System'
        elif 'cert-monitor' in raw_source_lower:
            return 'Certificate Monitor'
        elif 'disk' in raw_source_lower:
            return 'System Monitor' # New category for disk alerts
        return 'unknown_source' # Default if no match


    def _infer_source_from_message(self, message: str, host: str) -> str:
        """Tries to infer source from message content or host if process is missing."""
        message_lower = message.lower()
        if 'failed password' in message_lower or 'authenticated' in message_lower:
            return 'Authentication'
        elif 'deny' in message_lower or 'block' in message_lower or 'policy' in message_lower:
            return 'Network' # Could be firewall
        elif 'cpu usage' in message_lower or 'memory usage' in message_lower:
            return 'System Monitor'
        elif 'database connection' in message_lower:
            return 'Database'
        elif 'ransomware' in message_lower or 'virus' in message_lower:
            return 'Endpoint Security'
        elif 'data export' in message_lower:
            return 'Application' # Or specific 'DLP'
        return 'unknown_source'


    def _extract_ips(self, parsed_data: dict):
        """Extracts source and destination IPs based on keywords and position."""
        message_lower = parsed_data['message'].lower()
        
        # Look for explicit "from X to Y" patterns
        from_to_match = re.search(r'from\s+(?P<src_ip>\S+)\s+to\s+(?P<dst_ip>\S+)', message_lower)
        if from_to_match:
            parsed_data['source_ip_host'] = from_to_match.group('src_ip').strip('.,')
            parsed_data['destination_ip_host'] = from_to_match.group('dst_ip').strip('.,')
            return

        # Look for "from X" only
        from_match = re.search(r'from\s+(?P<src_ip>\S+)', message_lower)
        if from_match:
            parsed_data['source_ip_host'] = from_match.group('src_ip').strip('.,')
            
        # Look for "to Y" only, or if "from" wasn't found
        to_match = re.search(r'to\s+(?P<dst_ip>\S+)', message_lower)
        if to_match and not parsed_data['destination_ip_host']: # Don't overwrite if found by from_to
             parsed_data['destination_ip_host'] = to_match.group('dst_ip').strip('.,')

        # Fallback: if no keywords, just find any IPs and assign.
        # This is less reliable but better than nothing.
        if not parsed_data['source_ip_host'] and not parsed_data['destination_ip_host']:
            ips = self.ip_pattern.findall(parsed_data['message'])
            if len(ips) > 0:
                parsed_data['source_ip_host'] = ips[0] # Assume first IP is source if no other info
                if len(ips) > 1:
                    parsed_data['destination_ip_host'] = ips[1]


    def _refine_level_and_source_by_content(self, parsed_data: dict):
        """Refines level and source based on specific keywords in the message."""
        message_lower = parsed_data['message'].lower()
        
        if 'failed password' in message_lower and parsed_data['level'] == 'AUTH':
            parsed_data['level'] = 'AUTH_FAILED' # Custom level for failed auth
        elif 'unauthorized data export' in message_lower:
            parsed_data['level'] = 'CRITICAL'
            parsed_data['source'] = 'Application' # More specific if generic
        elif 'ransomware activity detected' in message_lower:
            parsed_data['level'] = 'CRITICAL' # Elevate to CRITICAL for ransomware
            parsed_data['source'] = 'Endpoint Security'
        elif 'suspicious high volume outbound connections' in message_lower:
            parsed_data['level'] = 'ALERT'
            parsed_data['source'] = 'Network'
        elif 'low disk space' in message_lower and parsed_data['level'] == 'WARN':
            parsed_data['source'] = 'System Monitor' # Assign more specific source


    # Backward compatibility for older calls, delegates to parse_log_entry.
    def parse_log_line(self, raw_log: str) -> dict: # Renamed from parse_log to parse_log_line
        """
        Parses a raw log string into a structured LogEntry-like dictionary.
        This method is designed to be called by log_receiver.
        """
        # Parse into a dictionary first
        parsed_dict = self.parse_log_entry(raw_log)
        
        # Convert dictionary to LogEntry object for consistency with db_client.insert_log
        return LogEntry(
            timestamp=parsed_dict.get('timestamp', datetime.now()),
            host=parsed_dict.get('host', 'unknown_host'),
            source=parsed_dict.get('source', 'unknown_source'),
            level=parsed_dict.get('level', 'INFO'),
            message=parsed_dict.get('message', raw_log),
            source_ip_host=parsed_dict.get('source_ip_host'),
            destination_ip_host=parsed_dict.get('destination_ip_host'),
            raw_log=raw_log # Always include raw_log
        )