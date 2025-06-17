# backend/api.py

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import os
# Import ProxyFix for handling reverse proxies in deployment
from werkzeug.middleware.proxy_fix import ProxyFix

from backend.config import Config
from backend.database.db_client import SiemDatabase
from backend.core.log_parser import LogParser
from backend.core.detection_rules import DetectionRules
from backend.database.models import LogEntry, Alert
from collections import defaultdict
from datetime import datetime, timedelta # Added timedelta for mock data initialization

# --- Initialize Core Components ---
config = Config()
db_client = SiemDatabase(config)
log_parser = LogParser()
rules_engine = DetectionRules(db_client, config)

# --- Flask App Setup ---
# Determine the base directory of the Flask app (backend folder)
current_dir = os.path.dirname(os.path.abspath(__file__))

# Define the path to the frontend's public directory for index.html
frontend_public_dir = os.path.join(current_dir, '..', 'frontend', 'public')

# Define the path to the frontend's src directory for JS and CSS
frontend_src_dir = os.path.join(current_dir, '..', 'frontend', 'src')

# Create the Flask application instance
# We'll serve index.html directly and then add a rule for /src
# Initially, set static_folder to public for the root endpoint,
# but we'll manually add a static rule for /src
app = Flask(__name__)

# Apply ProxyFix to trust X-Forwarded-* headers when running behind a reverse proxy (like Nginx, Load Balancer)
# This ensures request.remote_addr gets the actual client IP, not the proxy's IP.
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_host=1, x_port=1, x_prefix=1)

# Enable CORS for all API routes
CORS(app)

# --- Frontend Serving Routes ---

# Route to serve the main index.html file
@app.route('/')
def serve_index():
    """
    Serves the main index.html file from the frontend/public directory.
    """
    return send_from_directory(frontend_public_dir, 'index.html')

# Route to serve files from the frontend/src directory (CSS, JS)
@app.route('/src/<path:filename>')
def serve_src_files(filename):
    """
    Serves files (CSS, JS) from the frontend/src directory when requested with /src/.
    """
    return send_from_directory(frontend_src_dir, filename)

# --- API Endpoints ---

@app.route('/api/status', methods=['GET'])
def get_api_status():
    db_connected = True
    # In a real app, you might try a simple database query to verify connection
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
        source_filter = request_data.get('source', 'All Sources') # Changed default to 'All Sources' for consistency
        level_filter = request_data.get('level', 'All Levels')   # Changed default to 'All Levels' for consistency

        # CORRECTED LINE: Use db_client.filter_logs directly
        filtered_logs_data = db_client.filter_logs(filter_text=filter_text, source=source_filter, level=level_filter)
        return jsonify([log.to_dict() for log in filtered_logs_data])

    except Exception as e:
        app.logger.error(f"Error filtering logs: {e}")
        return jsonify({"error": "Error filtering logs. Please try again."}), 500

@app.route('/api/alerts/open', methods=['GET'])
def get_open_alerts():
    open_alerts = db_client.get_open_alerts()
    return jsonify([alert.to_dict() for alert in open_alerts])

@app.route('/api/dashboard/metrics', methods=['GET'])
def get_dashboard_metrics():
    critical_alerts = db_client.get_open_alerts(severity="Critical")
    critical_alerts_count = len(critical_alerts)

    import random
    eps_count = random.randint(1000, 1800)

    recent_logs = db_client.get_recent_logs(limit=100)
    source_counts = defaultdict(int)
    for log in recent_logs:
        source_counts[log.source] += 1

    total_logs_for_sources = sum(source_counts.values())
    top_sources = []
    if total_logs_for_sources > 0:
        sorted_sources = sorted(source_counts.items(), key=lambda item: item[1], reverse=True)
        for source, count in sorted_sources[:4]:
            percentage = (count / total_logs_for_sources) * 100
            top_sources.append({"name": source, "percentage": round(percentage)})

    unassigned_alerts = db_client.get_open_alerts()
    unassigned_alerts_count = len(unassigned_alerts)

    alert_trend_data = [random.randint(5, 20) for _ in range(7)]

    return jsonify({
        "critical_alerts_count": critical_alerts_count,
        "eps_count": eps_count,
        "top_sources": top_sources,
        "unassigned_alerts_count": unassigned_alerts_count,
        "alert_trend_data": alert_trend_data
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
    Initializes mock data by processing sample raw logs.
    This is called when running api.py directly (e.g., for local development/testing).
    """
    print("Initializing mock data for API endpoints...")
    from backend.core.log_receiver import process_raw_log

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
        # Simulate processing a log, which will involve parsing and inserting into the DB
        # The `process_raw_log` function should handle DB insertion.
        processed_log = log_parser.parse_log(raw_log)
        if processed_log:
            db_client.insert_log(processed_log.to_dict())
            rules_engine.run_rules_on_log(processed_log) # Also run detection rules

    # Also add some mock alerts directly if the alert collection is empty
    if not db_client.get_open_alerts(): # Check if alerts are empty to prevent re-adding
        db_client.insert_alert(Alert(
            timestamp=datetime.now() - timedelta(minutes=10),
            severity="High",
            description="API Mock Alert: Multiple failed logins detected.",
            source_ip_host="192.168.1.50",
            status="Open"
        ).to_dict())
        db_client.insert_alert(Alert(
            timestamp=datetime.now() - timedelta(minutes=20),
            severity="Medium",
            description="API Mock Alert: Unusual data transfer volume.",
            source_ip_host="server-b",
            status="Open"
        ).to_dict())
    print("Mock data initialization complete.")


if __name__ == '__main__':
    # When running locally (i.e., this script is executed directly),
    # ensure mock data is initialized.
    # On Render, the `gunicorn` command starts the app, and the database
    # connection will either succeed or fall back to in-memory mock data
    # as defined in db_client.py's __init__.
    initialize_mock_data_api_side()
    app.run(host=config.API_HOST, port=config.API_PORT, debug=True)