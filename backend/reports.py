# backend/reports.py

from collections import defaultdict
from datetime import datetime, timedelta # This line ensures datetime and timedelta are imported

class ReportGenerator:
    def __init__(self, db_client):
        self.db_client = db_client

    def generate_daily_security_summary(self):
        recent_logs = self.db_client.get_recent_logs(limit=1000) # Fetch more logs for a richer report
        top_sources = self._get_top_sources(recent_logs, limit=5)
        alert_summary = self._get_alert_summary()
        event_volume_by_type = self._get_event_volume_by_type(recent_logs)

        report = {
            "title": "Daily Security Summary Report",
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), # datetime.now() is now defined
            "summary": "This report provides an overview of security events and alerts for the past 24 hours.",
            "metrics": {
                "total_events_processed": len(recent_logs),
                "total_alerts_generated": sum(alert_summary.values()),
                "critical_alerts": alert_summary.get("Critical", 0),
                "high_alerts": alert_summary.get("High", 0)
            },
            "top_event_sources": top_sources,
            "event_volume_by_type": event_volume_by_type,
            "recommendations": [
                "Review critical and high-severity alerts promptly.",
                "Investigate anomalous log patterns identified in top event sources.",
                "Ensure all security agents and log sources are active and reporting."
            ]
        }
        return report

    def generate_compliance_audit_report(self, standard):
        report_content = f"Compliance Audit Report for {standard}\n\n"
        report_content += "This report assesses the organization's compliance posture against the specified standard.\n\n"

        # Simulate compliance checks
        passed_checks = ["Access Control Policies", "Logging and Monitoring", "Incident Response Plan"]
        failed_checks = [] # You could add logic to simulate failures

        if standard == "GDPR":
            passed_checks.append("Data Privacy Regulations")
            failed_checks.append("Data Retention Policy (needs review)")
        elif standard == "HIPAA":
            passed_checks.append("Protected Health Information (PHI) Handling")
        elif standard == "ISO 27001":
            passed_checks.append("Information Security Management System (ISMS)")

        report_content += "Compliance Checks:\n"
        for check in passed_checks:
            report_content += f"- [x] {check}\n"
        for check in failed_checks:
            report_content += f"- [ ] {check}\n"

        report_content += "\nRecommendations:\n"
        if failed_checks:
            report_content += "- Address identified non-compliance areas.\n"
        report_content += "- Conduct regular internal audits.\n"
        report_content += "- Stay updated with changes in regulatory requirements.\n"

        return {"report_content": report_content}

    # --- Helper Methods for Report Generation ---

    def _get_top_sources(self, logs, limit=5):
        source_counts = defaultdict(int) # defaultdict is correctly imported
        for log in logs:
            source_counts[log.source] += 1
        
        total_logs = sum(source_counts.values())
        top_sources = []
        if total_logs > 0:
            sorted_sources = sorted(source_counts.items(), key=lambda item: item[1], reverse=True)
            for source, count in sorted_sources[:limit]:
                percentage = (count / total_logs) * 100
                top_sources.append({"source": source, "count": count, "percentage": round(percentage, 2)})
        return top_sources

    def _get_alert_summary(self):
        alerts = self.db_client.get_all_alerts() # Assuming this method exists and returns all alerts
        severity_counts = defaultdict(int)
        for alert in alerts:
            severity_counts[alert.severity] += 1
        return dict(severity_counts) # Convert defaultdict to dict for JSON serialization

    def _get_event_volume_by_type(self, logs):
        level_counts = defaultdict(int)
        for log in logs:
            level_counts[log.level] += 1
        
        total_logs = sum(level_counts.values())
        
        # Define categories based on your log levels
        info = level_counts.get("INFO", 0)
        warn = level_counts.get("WARN", 0)
        error = level_counts.get("ERROR", 0)
        alert = level_counts.get("ALERT", 0)
        critical = level_counts.get("CRITICAL", 0)

        # Aggregate ALERT and CRITICAL
        alert_critical = alert + critical

        # Calculate 'other' by summing up everything not explicitly categorized
        other = total_logs - (info + warn + error + alert_critical)
        if other < 0: # Should not happen, but defensive check
            other = 0

        # Calculate percentages
        def get_percentage(count, total):
            return round((count / total) * 100, 2) if total > 0 else 0

        return {
            "INFO": {"count": info, "percent": get_percentage(info, total_logs)},
            "WARN": {"count": warn, "percent": get_percentage(warn, total_logs)},
            "ERROR": {"count": error, "percent": get_percentage(error, total_logs)},
            "ALERT/CRITICAL": {"count": alert_critical, "percent": get_percentage(alert_critical, total_logs)},
            "OTHER": {"count": other, "percent": get_percentage(other, total_logs)},
        }