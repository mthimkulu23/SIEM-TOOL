# backend/api.py

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import os
from werkzeug.middleware.proxy_fix import ProxyFix

from backend.config import Config
from backend.database.db_client import SiemDatabase
from backend.core.log_parser import LogParser
from backend.core.detection_rules import DetectionRules
from backend.database.models import LogEntry, Alert, NetworkFlowEntry # NEW: Import NetworkFlowEntry
from collections import defaultdict
from datetime import datetime, timedelta

# --- Initialize Core Components ---
config = Config()
db_client = SiemDatabase(config)
log_parser = LogParser()
rules_engine = DetectionRules(db_client, config)

print("Flask API: SiemDatabase, LogParser, DetectionRules initialized.")

# --- Flask App Setup ---
current_dir = os.path.dirname(os.path.abspath(__file__))
frontend_public_dir = os.path.join(current_dir, '..', 'frontend', 'public')
frontend_src_dir = os.path.join(current_dir, '..', 'frontend', 'src')

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_host=1, x_port=1, x_prefix=1)
CORS(app)

# --- Frontend Serving Routes ---
@app.route('/')
def serve_index():
    return send_from_directory(frontend_public_dir, 'index.html')

@app.route('/src/<path:filename>')
def serve_src_files(filename):
    return send_from_directory(frontend_src_dir, filename)

# --- API Endpoints ---

@app.route('/api/status', methods=['GET'])
def get_api_status():
    db_connected = True # Placeholder, ideally check actual DB connection status
    return jsonify({"status": "running", "database_connected": db_connected})

@app.route('/api/logs/recent', methods=['GET'])
def get_recent_logs():
    recent_logs = db_client.get_recent_logs(limit=20)
    return jsonify([log.to_dict() for log in recent_logs])

@app.route('/api/logs/filter', methods=['POST'])
def filter_logs():
    try:
        request_data = request.get_json()
        filter_text = request_data.get('filter_text', '')
        source_filter = request_data.get('source', 'All Sources')
        level_filter = request_data.get('level', 'All Levels')

        filtered_logs_data = db_client.filter_logs(filter_text=filter_text, source=source_filter, level=level_filter)
        return jsonify([log.to_dict() for log in filtered_logs_data])

    except Exception as e:
        app.logger.error(f"Error filtering logs: {e}", exc_info=True)
        return jsonify({"error": "Error filtering logs. Please try again."}), 500

@app.route('/api/logs/ingest', methods=['POST'])
def ingest_log():
    """
    Receives raw log data, parses it, stores it, and runs detection rules.
    Expected request body: {"raw_log": "your raw log line here"}
    """
    try:
        data = request.get_json()
        if not data or 'raw_log' not in data:
            print("API Error: Missing 'raw_log' in request body or invalid JSON.")
            return jsonify({"error": "Missing 'raw_log' field in JSON payload"}), 400

        raw_log = data['raw_log']
        
        log_entry_obj = log_parser.parse_log_entry(raw_log)

        inserted_id = db_client.insert_log(log_entry_obj)
        
        if inserted_id:
            log_entry_obj._id = inserted_id 
            print(f"API: Log ingested with ID: {inserted_id} (Host: {log_entry_obj.host}, Source: {log_entry_obj.source}, Level: {log_entry_obj.level})")
            rules_engine.run_rules_on_log(log_entry_obj)
            print(f"API: Detection rules run for log: {log_entry_obj.message[:50]}...")
            
            return jsonify({"message": "Log ingested successfully", "log_id": str(inserted_id)}), 201
        else:
            print(f"ERROR: API: Failed to insert log: {raw_log[:100]}...")
            return jsonify({"error": "Failed to ingest log into database"}), 500

    except Exception as e:
        app.logger.error(f"Error ingesting log: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

# --- NEW: Network Flow Endpoints ---
@app.route('/api/network_flows/ingest', methods=['POST'])
def ingest_network_flow():
    """
    Receives structured network flow data from a capturing script.
    Expected request body: JSON matching NetworkFlowEntry.to_dict() structure.
    """
    try:
        flow_data = request.get_json()
        if not flow_data:
            print("API Error: Invalid JSON payload for network flow.")
            return jsonify({"error": "Invalid JSON payload"}), 400

        # Validate required fields (minimal validation for example)
        required_fields = ['timestamp', 'protocol', 'source_ip', 'destination_ip']
        if not all(field in flow_data for field in required_fields):
            print(f"API Error: Missing required fields in network flow payload. Expected: {required_fields}")
            return jsonify({"error": f"Missing required fields for network flow. Expected: {required_fields}"}), 400

        # Create NetworkFlowEntry object from incoming data
        # The from_dict method should handle datetime conversion from ISO string
        flow_entry = NetworkFlowEntry.from_dict(flow_data)

        inserted_id = db_client.insert_network_flow(flow_entry)
        if inserted_id:
            # Assign the generated MongoDB _id back to the NetworkFlowEntry object
            flow_entry._id = inserted_id
            print(f"API: Network flow ingested with ID: {inserted_id} (Src: {flow_entry.source_ip}, Dst: {flow_entry.destination_ip}, Proto: {flow_entry.protocol})")
            # You might add detection rules for network flows here later
            return jsonify({"message": "Network flow ingested successfully", "flow_id": str(inserted_id)}), 201
        else:
            print(f"ERROR: API: Failed to insert network flow: {flow_data.get('source_ip')} -> {flow_data.get('destination_ip')}")
            return jsonify({"error": "Failed to ingest network flow"}), 500

    except Exception as e:
        app.logger.error(f"Error ingesting network flow: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/api/network_flows/recent', methods=['GET'])
def get_recent_network_flows():
    """
    Retrieves recent network flows for display on the frontend.
    """
    try:
        recent_flows = db_client.get_recent_network_flows(limit=50) # Adjust limit as needed
        # Convert NetworkFlowEntry objects to dictionaries for JSON serialization
        return jsonify([flow.to_dict() for flow in recent_flows])
    except Exception as e:
        app.logger.error(f"Error fetching recent network flows: {e}", exc_info=True)
        return jsonify({"error": "Could not fetch network flows"}), 500
# --- END NEW: Network Flow Endpoints ---


@app.route('/api/alerts/open', methods=['GET'])
def get_open_alerts():
    open_alerts = db_client.get_open_alerts()
    return jsonify([alert.to_dict() for alert in open_alerts])

@app.route('/api/dashboard/metrics', methods=['GET'])
def get_dashboard_metrics():
    critical_alerts = db_client.get_open_alerts(severity="Critical")
    critical_alerts_count = len(critical_alerts)

    import random
    eps_count = random.randint(1000, 1800) # Still random

    recent_logs = db_client.get_recent_logs(limit=100)
    source_counts = defaultdict(int)
    level_counts = defaultdict(int)

    for log in recent_logs:
        source_counts[log.source] += 1
        level_counts[log.level] += 1

    total_logs_for_sources = sum(source_counts.values())
    top_sources = []
    if total_logs_for_sources > 0:
        sorted_sources = sorted(source_counts.items(), key=lambda item: item[1], reverse=True)
        for source, count in sorted_sources[:4]:
            percentage = (count / total_logs_for_sources) * 100
            top_sources.append({"name": source, "percentage": round(percentage)})
    
    total_logs_for_levels = sum(level_counts.values())
    event_volume_by_type = {
        "INFO": 0, "WARN": 0, "ERROR": 0, "CRITICAL": 0, "AUTH_FAILED": 0, "OTHER": 0 # Added AUTH_FAILED
    }
    if total_logs_for_levels > 0:
        for level, count in level_counts.items():
            percentage = (count / total_logs_for_levels) * 100
            # Aggregate specific levels, remaining go to OTHER
            if level in event_volume_by_type:
                event_volume_by_type[level] += round(percentage, 1) # Use += for safety with duplicates
            elif level.startswith("AUTH"): # Catch all AUTH levels for dashboard
                event_volume_by_type["AUTH_FAILED"] += round(percentage, 1)
            else:
                event_volume_by_type["OTHER"] += round(percentage, 1)
    
    unassigned_alerts = db_client.get_open_alerts()
    unassigned_alerts_count = len(unassigned_alerts)

    alert_trend_data = [random.randint(5, 20) for _ in range(7)] 

    return jsonify({
        "critical_alerts_count": critical_alerts_count,
        "eps_count": eps_count,
        "top_sources": top_sources,
        "unassigned_alerts_count": unassigned_alerts_count,
        "alert_trend_data": alert_trend_data,
        "event_volume_by_type": event_volume_by_type
    })

@app.route('/api/alerts/<string:alert_id>/status', methods=['PUT'])
def update_alert_status(alert_id: str):
    request_data = request.get_json()
    new_status = request_data.get('status')
    if not new_status:
        return jsonify({"message": "Status not provided", "success": False}), 400

    success = db_client.update_alert_status(alert_id, new_status)
    if success:
        return jsonify({"message": "Alert status updated successfully", "success": True}), 200
    else:
        return jsonify({"message": "Alert not found or update failed", "success": False}), 404

@app.route('/api/reports/daily_summary', methods=['GET'])
def get_daily_security_summary():
    from backend.reports import ReportGenerator
    report_gen = ReportGenerator(db_client)
    report_data = report_gen.generate_daily_security_summary()
    return jsonify(report_data)

@app.route('/api/reports/compliance_audit', methods=['POST'])
def get_compliance_audit_report():
    request_data = request.get_json()
    standard = request_data.get('standard')
    if not standard:
        return jsonify({"message": "Compliance standard not provided", "success": False}), 400

    from backend.reports import ReportGenerator
    report_gen = ReportGenerator(db_client)
    report_data = report_gen.generate_compliance_audit_report(standard)
    return jsonify(report_data)

def initialize_mock_data_api_side():
    """
    Initializes mock data by processing sample raw logs and alerts.
    This function is now called when the Flask app starts.
    """
    print("Checking for existing data before initializing mock data...")
    if db_client.get_recent_logs(limit=1) or db_client.get_open_alerts() or db_client.get_recent_network_flows(limit=1): # NEW: Check network flows too
        print("Existing data found. Skipping mock data initialization.")
        return

    print("No existing data found. Initializing mock data for API endpoints...")

    sample_logs_for_init = [
        "Jun 17 10:00:01 host-a kernel: [INFO] System boot successful.",
        "Jun 17 10:00:05 host-b sshd[123]: [AUTH] Failed password for user flask_test from 192.168.1.10.",
        "Jun 17 10:00:08 host-b sshd[124]: [AUTH] Failed password for user flask_test from 192.168.1.10.",
        "Jun 17 10:00:12 host-b sshd[125]: [AUTH] Failed password for user flask_test from 192.168.1.10.",
        "Jun 17 10:00:15 web-server-01 apache: [WARN] High CPU usage (85%).",
        "Jun 17 10:00:20 db-server-01 postgres: [ERROR] Database connection pool exhausted.",
        "Jun 17 10:00:25 firewall-01 firewall: [INFO] Policy update applied.",
        "Jun 17 10:00:30 critical-db app: [CRITICAL] Unauthorized data export attempt detected from 10.0.0.5 to external_server.",
        "Jun 17 10:00:35 backup-srv: [INFO] Daily backup initiated for critical_data_volume.",
        "Jun 17 10:00:40 log-server-01 disk: [WARN] Low disk space on /var/log (90% full).",
        "Jun 17 10:00:45 endpoint-sec-03 av: [INFO] Anti-virus definitions updated to latest version.",
        "Jun 17 10:00:50 hr-laptop-03 endpoint: [ALERT] Ransomware activity detected and blocked on C:\\HR_Docs\\.",
        "Jun 17 10:01:00 router-core-01 network: [INFO] New routing table deployed.",
        "Jun 17 10:01:10 web-server-02 cert-monitor: [WARN] SSL certificate 'www.example.com' expires in 10 days.",
        "Jun 17 10:01:20 db-dev-02 netflow: [ALERT] Suspicious high volume outbound connections to 172.16.20.100."
    ]
    for raw_log in sample_logs_for_init:
        log_entry_obj = log_parser.parse_log_entry(raw_log)
        if log_entry_obj:
            inserted_id = db_client.insert_log(log_entry_obj) 
            if inserted_id:
                log_entry_obj._id = inserted_id 
                rules_engine.run_rules_on_log(log_entry_obj) 
            else:
                print(f"WARNING: Failed to insert mock log: {raw_log}")

    db_client.insert_alert(Alert(
        timestamp=datetime.now() - timedelta(minutes=10),
        severity="High",
        description="API Mock Alert: Multiple failed logins detected.",
        source_ip_host="192.168.1.50",
        status="Open",
        rule_name="Mock Failed Login Alert"
    ))
    db_client.insert_alert(Alert(
        timestamp=datetime.now() - timedelta(minutes=20),
        severity="Medium",
        description="API Mock Alert: Unusual data transfer volume.",
        source_ip_host="server-b",
        status="Open",
        rule_name="Mock Data Transfer Alert"
    ))

    # --- NEW: Initialize mock network flow data ---
    sample_flows_for_init = [
        NetworkFlowEntry(timestamp=datetime.now() - timedelta(seconds=15), protocol="TCP", source_ip="192.168.1.1", destination_ip="8.8.8.8", source_port=51234, destination_port=53, byte_count=150, application_layer_protocol="DNS", flags=["SYN"]),
        NetworkFlowEntry(timestamp=datetime.now() - timedelta(seconds=10), protocol="UDP", source_ip="10.0.0.100", destination_ip="172.16.0.5", source_port=161, destination_port=162, byte_count=200, application_layer_protocol="SNMP"),
        NetworkFlowEntry(timestamp=datetime.now() - timedelta(seconds=5), protocol="TCP", source_ip="192.168.1.50", destination_ip="203.0.113.1", source_port=45678, destination_port=80, byte_count=1200, application_layer_protocol="HTTP", flags=["ACK", "PSH"])
    ]
    for flow_entry in sample_flows_for_init:
        inserted_id = db_client.insert_network_flow(flow_entry)
        if inserted_id:
            flow_entry._id = inserted_id
        else:
            print(f"WARNING: Failed to insert mock network flow: {flow_entry.source_ip}")
    # --- END NEW: Initialize mock network flow data ---

    print("Mock data initialization complete.")


initialize_mock_data_api_side()

if __name__ == '__main__':
    app.run(host=config.API_HOST, port=config.API_PORT, debug=True)